import io
import os
import base64
import toml
import streamlit as st
import pandas as pd
import tempfile
import requests
from logzero import logger


def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.title("👮‍♂️ Authentification")
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True


def initialize_session_state(session_state, secrets):
    logger.info("Initializing session state variables.")
    CONFIG = toml.load(os.path.join("parameters", "config.toml"))
    DATA_PATH = CONFIG["data"]["default_data_path"]

    if not os.path.exists(DATA_PATH):
        os.mkdir(DATA_PATH)

    session_state["IS_INITIALIZED"] = True
    session_state["questions_mapping"] = toml.load(
        CONFIG["data"]["yaml_questions_path"]
    )
    session_state["translation_mapping"] = toml.load(
        CONFIG["data"]["yaml_translation_path"]
    )

    # Loading secrets
    session_state["SCOPES"] = secrets["api"]["default_scopes"]
    session_state["SERVICE_ACCOUNT_INFO"] = secrets["api"]["service_account"]
    session_state["FRENCH_FORM_ID"] = secrets["forms"]["french_form_id"]
    session_state["ENGLISH_FORM_ID"] = secrets["forms"]["english_form_id"]
    session_state["GSHEET_TRACKING_ID"] = secrets["sheets"]["gsheet_tracking_id"]
    session_state["GSHEET_REFINITIV_ID"] = secrets["sheets"]["gsheet_refinitiv_id"]

    # Loading config variables
    session_state["FORMS_CSV_PATH"] = os.path.join(DATA_PATH, "full_forms_data.csv")
    session_state["TRACKING_CSV_PATH"] = os.path.join(DATA_PATH, "tracking_data.csv")
    session_state["REFINITIV_CSV_PATH"] = os.path.join(DATA_PATH, "refinitiv_data.csv")
    session_state["REFINITIV_NEW_COLUMNS_DICT"] = CONFIG["refinitiv"][
        "new_column_names"
    ]
    session_state["REPLACEMENT_DICT"] = CONFIG["forms"]["analysis"]
    session_state["MULTI_CHOICE_COLUMNS"] = CONFIG["forms"]["multi_choice_columns"]
    session_state["COLUMN_NAMES_RENAMING_DICT"] = CONFIG["forms"]["new_column_names"]

    # PDF files path loading
    session_state["RESEARCH_PAPER_PDF_ID"] = CONFIG["assets"]["pdf"][
        "research_paper_pdf_id"
    ]
    session_state["DEFENSE_PDF_ID"] = CONFIG["assets"]["pdf"]["defense_pdf_id"]
    session_state["RESUME_PATH"] = CONFIG["assets"]["pdf"]["resume_path"]
    session_state["CV_PATH"] = CONFIG["assets"]["pdf"]["cv_path"]

    # Markdown files loading
    session_state["INTRODUCTION_PATH"] = CONFIG["assets"]["markdown"][
        "introduction_path"
    ]
    session_state["PERSONAL_PRESENTATION"] = CONFIG["assets"]["markdown"][
        "personal_presentation_path"
    ]
    session_state["SURVEY_INTRO"] = CONFIG["assets"]["markdown"]["survey_intro_path"]
    session_state["CONTACT_INFORMATION"] = CONFIG["assets"]["markdown"][
        "contact_information_path"
    ]

    session_state["UNIFIED_LOGO"] = CONFIG["assets"]["images"]["unified_logo_path"]
    session_state["IDENTITY_PHOTO"] = CONFIG["assets"]["images"]["identity_photo_path"]
    session_state["api_forms"], session_state["api_sheets"] = None, None


def generate_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Results")
        writer.save()
    return buffer


def display_pdf(file_path):
    # Opening file from file path
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")

    # Embedding PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'

    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)


def display_online_pdf(pdf_id, width=800, height=800):
    pdf_display = f'<iframe src="https://drive.google.com/file/d/{pdf_id}/preview" width="{width}" height="{height}" allow="autoplay"</iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def _get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value

    return None


def get_file_from_google_drive(id):
    data = None
    CHUNK_SIZE = 32768
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params={"id": id}, stream=True)
    token = _get_confirm_token(response)

    if token:
        params = {"id": id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    temp = tempfile.TemporaryFile()
    if response.headers["content-type"] == "application/pdf":
        logger.info("PDF correctly loaded.")
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                temp.write(chunk)
        temp.seek(0)
        data = temp.read()
        temp.close()
    else:
        logger.critical("File not found. Check URL or GDrive sharing parameters.")
        raise ValueError("File not found. Check URL or GDrive sharing parameters.")
    return data
