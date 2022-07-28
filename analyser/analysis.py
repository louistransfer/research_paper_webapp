import pandas as pd
from logzero import logger
from analyser.refinitiv_helpers import cleaner


def _compute_score(answers: list, scores_dict: dict) -> pd.Series:
    scores = sum([scores_dict[answer] for answer in answers])
    return scores


def _get_dummies_multi_choice_column(series_column):
    new_dummy_df = pd.get_dummies(series_column.explode()).groupby(level=0).sum()
    return new_dummy_df


def refinitiv_data_cleaning(df_refinitiv_full):
    if df_refinitiv_full["Firm Name"].isin(["OC4 Ventures Fund I LP"]).any():
        df_refinitiv_full = df_refinitiv_full[
            df_refinitiv_full["Firm Name"] != "OC4 Ventures Fund I LP"
        ].reset_index(drop=True)
    df_refinitiv_full.loc[
        df_refinitiv_full["Firm Industry"].isna(), "Firm Industry"
    ] = "Diversified"
    df_refinitiv_full.loc[
        df_refinitiv_full["Firm Stage"].isna(), "Firm Stage"
    ] = "Balanced Stage"
    return df_refinitiv_full


def generate_unified_dataframe(
    df_refinitiv: pd.DataFrame,
    df_tracking: pd.DataFrame,
    df_forms: pd.DataFrame,
):
    df_gsheets_extract = df_tracking[["Fonds", "email", "Fonds turbo-data ?"]]
    df_forms_completed = df_forms.merge(df_gsheets_extract, on="email", how="left")
    df_unified = df_refinitiv.merge(
        df_forms_completed, left_on="Main Fund Name", right_on="Fonds"
    )
    return df_unified


def generate_targets_list(df_tracking: pd.DataFrame):
    return (
        df_tracking[
            df_tracking["Statut"].isin(["Réponse positive", "Entretien réalisé"])
        ]["Fonds"]
        .apply(lambda text: cleaner(text))
        .to_list()
    )


def process_analysis_dataframe(
    df_analysis: pd.DataFrame, replacement_dict: dict, multi_choice_columns: list
) -> tuple[pd.DataFrame, dict]:

    dummy_columns_dict = {}
    cardinal_columns_replacement_dict: dict = replacement_dict["cardinal_columns"]
    scores_replacement_dict: dict = replacement_dict["scores"]

    for cardinal_column in cardinal_columns_replacement_dict.keys():
        df_analysis[cardinal_column] = df_analysis[cardinal_column].replace(
            cardinal_columns_replacement_dict[cardinal_column]
        )
    df_analysis["Effect on investments"] = (
        df_analysis["Effect on investments"].fillna(0).astype(int)
    )

    for score_column in scores_replacement_dict.keys():
        df_analysis[score_column] = df_analysis[score_column].apply(
            lambda answers: _compute_score(
                answers, scores_replacement_dict[score_column]
            )
        )
    for column in multi_choice_columns:
        df_temp = _get_dummies_multi_choice_column(df_analysis[column])
        dummy_columns = df_temp.columns.tolist()
        df_analysis = df_analysis.merge(
            df_temp,
            how="left",
            left_index=True,
            right_index=True,
        )
        dummy_columns_dict[column] = dummy_columns
    df_analysis = df_analysis.drop(columns=multi_choice_columns)
    return df_analysis, dummy_columns_dict


def generate_aggregated_firm_data(df_unified: pd.DataFrame, aggregation_columns: list):
    df_aggregated = (
        df_unified[["Firm Name", "Nb companies invested in"] + aggregation_columns]
        .rename(columns={"Firm Name": "Nb firms"})
        .groupby(aggregation_columns)
        .agg({"Nb firms": "count", "Nb companies invested in": ["mean", "median"]})
        .sort_values(by=("Nb firms", "count"), ascending=False)
        .reset_index()
        .style.format(precision=2)
    )
    return df_aggregated
