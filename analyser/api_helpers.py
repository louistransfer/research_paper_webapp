import json
import os
import pandas as pd
from streamlit.state import SessionStateProxy
from google.oauth2 import service_account
from apiclient import discovery
from analyser.df_processing import process_answers
from analyser.refinitiv_helpers import search_fund_name
from analyser.analysis import refinitiv_data_cleaning
from logzero import logger


def _authenticate(
    service_account_info: dict, scopes: list
) -> tuple[discovery.Resource, discovery.Resource]:
    creds = service_account.Credentials.from_service_account_info(
        info=service_account_info,
        scopes=scopes,
    )
    api_forms = discovery.build("forms", "v1", credentials=creds)
    api_sheets = discovery.build("sheets", "v4", credentials=creds)
    logger.info("🔑 Authentification successful.")
    return api_forms, api_sheets


def _extract_form_dataset(
    api: discovery.Resource, form_id: str, dump_response: bool = False
) -> dict:
    res = api.forms().responses().list(formId=form_id).execute()
    responses = res["responses"]
    if dump_response:
        with open("res_english_export.json", "w") as out_file:
            json.dump(responses, out_file)
    return responses


def _extract_all_responses(
    api: discovery.Resource, french_form_id: str, english_form_id: str
) -> tuple[dict, dict]:
    french_response = _extract_form_dataset(api, form_id=french_form_id)
    english_response = _extract_form_dataset(api, form_id=english_form_id)
    return french_response, english_response


def import_form_data(
    session_state: SessionStateProxy,
    french_form_id: str,
    english_form_id: str,
    questions_mapping: dict,
    translation_mapping: dict,
    forms_csv_path: str,
    multi_choice_columns: list,
    force_reload: bool = False,
) -> pd.DataFrame:

    if (os.path.exists(forms_csv_path)) and (force_reload is False):
        logger.info("🔢 Found existing Forms csv, loading it now.")
        converter_dict = {i: pd.eval for i in multi_choice_columns}
        df_full = pd.read_csv(forms_csv_path, sep=";", converters=converter_dict)
    else:
        logger.warning("⚙ No csv found, extracting data from the Forms API.")
        if session_state["api_forms"] == None:
            session_state["api_forms"], session_state["api_sheets"] = _authenticate(
                session_state["SERVICE_ACCOUNT_INFO"], session_state["SCOPES"]
            )

        french_response, english_response = _extract_all_responses(
            session_state["api_forms"],
            french_form_id=french_form_id,
            english_form_id=english_form_id,
        )
        df_french = process_answers(
            french_response,
            questions_mapping,
            multi_choice_columns,
            language="french",
            translation_mapping=translation_mapping,
        )
        logger.info("(1/2) 🇫🇷 Processed french answers.")
        df_english = process_answers(
            english_response,
            questions_mapping,
            multi_choice_columns,
            language="english",
        )
        logger.info("(2/2) 🇬🇧 Processed english answers.")
        df_full = pd.concat([df_english, df_french], axis=0)
        df_full.to_csv(forms_csv_path, index=False, sep=";")
        logger.info("Merged dataset save successful.")
    return df_full


def import_gsheet_data(
    session_state: SessionStateProxy,
    gsheet_id: str,
    range: str,
    csv_path: str = "",
    force_reload=False,
) -> pd.DataFrame:

    if (os.path.exists(csv_path)) and (force_reload == False):
        logger.info("🔢 Found existing GSheets csv, loading it now.")
        df = pd.read_csv(csv_path, sep=";")
    else:
        logger.warning("⚙ No csv found, extracting data from the GSheets API.")
        if session_state["api_sheets"] == None:
            session_state["api_forms"], session_state["api_sheets"] = _authenticate(
                session_state["SERVICE_ACCOUNT_INFO"], session_state["SCOPES"]
            )

        result = (
            session_state["api_sheets"]
            .spreadsheets()
            .values()
            .get(
                spreadsheetId=gsheet_id,
                range=range,
                valueRenderOption="UNFORMATTED_VALUE",
            )
            .execute()
        )["values"]
        headers = result[0]
        df = pd.DataFrame(data=result[1:], columns=headers)
        if csv_path != "":
            df.to_csv(csv_path, index=False, sep=";")
    return df


def import_refinitiv_data(
    session_state,
    gsheet_refinitiv_id: str,
    df_refinitiv_csv_path: str,
    cols_to_keep: list,
    col_replace_dict: dict,
    targets_list_data: list,
    force_reload: bool = False,
) -> pd.DataFrame:

    if (os.path.exists(df_refinitiv_csv_path)) and (force_reload is False):
        logger.info("🔢 Found existing Refinitiv csv, loading it now.")

        df_refinitiv = pd.read_csv(df_refinitiv_csv_path, sep=";")
    else:
        logger.warning("⚙ No csv found, extracting Refinitiv data from the Sheets API.")
        if session_state["api_sheets"] == None:
            session_state["api_sheets"], session_state["api_sheets"] = _authenticate(
                session_state["SERVICE_ACCOUNT_INFO"], session_state["SCOPES"]
            )

        df_refinitiv_investments = import_gsheet_data(
            session_state, gsheet_refinitiv_id, range="Firms - Investments"
        )

        df_refinitiv_fundraising = import_gsheet_data(
            session_state, gsheet_refinitiv_id, range="Firms - Fundraising"
        )

        df_refinitiv_investments = df_refinitiv_investments.rename(
            columns={"Firm Investor Name": "Firm Name"}
        )
        df_refinitiv_investments = df_refinitiv_investments[
            df_refinitiv_investments["Firm Name"] != "TOTAL"
        ]

        df_refinitiv_fundraising = df_refinitiv_fundraising[
            df_refinitiv_fundraising["Firm Name"] != "Industry total"
        ]

        df_refinitiv = df_refinitiv_fundraising.merge(
            df_refinitiv_investments, on="Firm Name", how="left"
        )

        df_refinitiv = df_refinitiv.rename(columns=col_replace_dict)[cols_to_keep]

        df_refinitiv["Main Fund Name"] = df_refinitiv["Firm Name"].apply(
            lambda sub_fund_name: search_fund_name(sub_fund_name, targets_list_data)
        )
        df_refinitiv = refinitiv_data_cleaning(df_refinitiv)
        df_refinitiv.to_csv(df_refinitiv_csv_path, index=False, sep=";")

    return df_refinitiv