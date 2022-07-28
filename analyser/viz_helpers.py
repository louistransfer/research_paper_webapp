import plotly.express as px
from plotly.graph_objects import Figure
import pandas as pd


def generate_parallel_categories(df: pd.DataFrame) -> Figure:
    # TO-DO : fix colors

    # print(df_exploded[color_column].unique())
    # color_map = {
    #     value: idx + 1 for idx, value in enumerate(df[color_column].unique())
    # }
    # manual_color_map = {
    #     "In an experimental fashion": "aliceblue",
    #     "Systematically": "antiquewhite",
    #     "Regularly": "aqua",
    # }
    # df["Data science usage"] = df["Data science usage"].map(
    #     manual_color_map
    # )

    fig = px.parallel_categories(
        df,
        # color="Data science usage"
        # color_continuous_scale=px.colors.sequential.Inferno,
    )

    return fig


def generate_funnel(df_gsheet: pd.DataFrame, df_full: pd.DataFrame) -> Figure:
    nb_funds = len(df_gsheet["Fonds"].unique())
    nb_ds_funds = len(df_gsheet[df_gsheet["Nom cible"] != "X"])
    nb_contacted = nb_ds_funds - df_gsheet["Nom cible"].isna().sum()
    nb_answered_survey = len(df_full)
    nb_interviews = len(df_gsheet[df_gsheet["Statut"] == "Entretien réalisé"])
    funnel_data = {
        "stage": [
            "Initial list",
            "Funds where I found data scientists",
            "Funds I contacted",
            "Funds who answered the survey",
            "Funds interviewed",
        ],
        "number": [
            nb_funds,
            nb_ds_funds,
            nb_contacted,
            nb_answered_survey,
            nb_interviews,
        ],
    }
    fig = px.funnel(funnel_data, x="number", y="stage")
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis=dict(ticksuffix="    "),
        font={"size": 18},
        width=800,
    )
    return fig
