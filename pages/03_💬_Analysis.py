import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from logzero import logger

from analyser.api_helpers import (
    import_form_data,
    import_gsheet_data,
    import_refinitiv_data,
)
from analyser.streamlit_helpers import initialize_session_state
from analyser.df_processing import generate_exploded_df
from analyser.viz_helpers import generate_parallel_categories
from analyser.analysis import (
    process_analysis_dataframe,
    generate_unified_dataframe,
    generate_targets_list,
    generate_aggregated_firm_data,
)

if "IS_INITIALIZED" not in st.session_state:
    initialize_session_state(st.session_state, st.secrets)

# Temporary hardcoded

CARDINAL_COLUMNS = set(["Technologies used", "Implementation time"])
NOMINAL_COLUMNS = set(st.session_state["MULTI_CHOICE_COLUMNS"]) - CARDINAL_COLUMNS

COLS_TO_KEEP = [
    "Firm Name",
    "Nb funds",
    "Fund Size",
    "Firm Stage",
    "Firm Industry",
    "Sum Equity Invested",
    "Estimated Equity Available",
    "Nb companies invested in",
    "Sum Deal Rank",
]

tab_industry, tab_correlation, tab_intra = st.tabs(
    ["Industry overview", "Correlations", "Intra-questions analysis"]
)

df_forms = import_form_data(
    st.session_state,
    st.session_state["FRENCH_FORM_ID"],
    st.session_state["ENGLISH_FORM_ID"],
    st.session_state["questions_mapping"],
    st.session_state["translation_mapping"],
    st.session_state["FORMS_CSV_PATH"],
    st.session_state["MULTI_CHOICE_COLUMNS"],
)

df_tracking = import_gsheet_data(
    st.session_state,
    st.session_state["GSHEET_TRACKING_ID"],
    range="Contacts",
    csv_path=st.session_state["TRACKING_CSV_PATH"],
)

targets_list_data = generate_targets_list(df_tracking)
df_refinitiv = import_refinitiv_data(
    st.session_state,
    st.session_state["GSHEET_REFINITIV_ID"],
    st.session_state["REFINITIV_CSV_PATH"],
    COLS_TO_KEEP,
    st.session_state["REFINITIV_NEW_COLUMNS_DICT"],
    targets_list_data,
)
df_unified = generate_unified_dataframe(df_refinitiv, df_tracking, df_forms)
df_analysis, dummy_columns_dict = process_analysis_dataframe(
    df_unified, st.session_state["REPLACEMENT_DICT"], NOMINAL_COLUMNS
)


with tab_industry:

    if st.button("🔁 Reload Refinitiv data"):
        df_refinitiv = import_refinitiv_data(
            st.session_state,
            st.session_state["GSHEET_REFINITIV_ID"],
            st.session_state["REFINITIV_CSV_PATH"],
            COLS_TO_KEEP,
            st.session_state["REFINITIV_NEW_COLUMNS_DICT"],
            targets_list_data,
            force_reload=True,
        )
        df_unified = generate_unified_dataframe(df_refinitiv, df_tracking, df_forms)
        df_analysis, dummy_columns_dict = process_analysis_dataframe(
            df_unified, st.session_state["REPLACEMENT_DICT"], NOMINAL_COLUMNS
        )

    st.title("Profile of the firms which answered the survey")
    

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        df_aggregated_firm_stage = generate_aggregated_firm_data(
            df_unified, ["Firm Stage"]
        )

        st.markdown("**Preferred firms investment stage**")
        st.table(df_aggregated_firm_stage)
    with col2:
        df_aggregated_firm_industry = generate_aggregated_firm_data(
            df_unified, ["Firm Industry"]
        )
        st.markdown("**Preferred firms investment industry**")
        st.table(df_aggregated_firm_industry)

with tab_correlation:
    col1, col2 = st.columns(spec=2)
    with col1:
        refinitiv_options = df_refinitiv.select_dtypes(include=np.number).columns.tolist()
        selected_refinitiv_options = st.multiselect(
            "Financial data columns", refinitiv_options
        )
        st.markdown("""---""")
        how_options = dummy_columns_dict["How ?"]
        selected_how_options = st.multiselect(
            "How data science techniques improved investments", how_options
        )

        data_sources_options = dummy_columns_dict["Data sources"]
        selected_data_sources_options = st.multiselect(
            "Which data sources are used", data_sources_options
        )

    with col2:

        unichoice_options = set(df_forms.columns) - NOMINAL_COLUMNS - set(["create_time", "email"])
        selected_unichoice_options = st.multiselect(
            "Unichoice forms columns", unichoice_options
        )

        st.markdown("""---""")
        stage_options = dummy_columns_dict["At which stage of the deal process"]
        selected_stage_options = st.multiselect(
            "At which stage of the deal process are the data science techniques used", stage_options
        )

        usage_options = dummy_columns_dict["Main usage reason"]
        selected_usage_options = st.multiselect(
            "Main usage reason of data science techniques", usage_options
        )



    
    st.session_state["selected_options"] = selected_refinitiv_options + selected_unichoice_options + selected_how_options + selected_stage_options + selected_data_sources_options + selected_usage_options
    df_analysis_corr = df_analysis.loc[:, st.session_state["selected_options"]].corr()
    fig = px.imshow(
        df_analysis_corr,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Bluered_r",
    )
    st.plotly_chart(fig)

with tab_intra:
    available_columns = st.session_state["COLUMN_NAMES_RENAMING_DICT"].values()
    converter_dict = {i: pd.eval for i in st.session_state["MULTI_CHOICE_COLUMNS"]}
    df_full = pd.read_csv(st.session_state["FORMS_CSV_PATH"], sep=";", converters=converter_dict)

    selected_options = st.multiselect(
        "Choose variables to generate the parallel plot",
        available_columns,
    )
    df_exploded_parallel = generate_exploded_df(
        df_full, selected_options, st.session_state["MULTI_CHOICE_COLUMNS"]
    )
    # selected_color_column = st.selectbox(
    #     "Choose the variable which determines the color of the connections",
    #     selected_options,
    #     format_func=lambda text: NEW_COLUMN_NAMES[text]
    # )
    # selected_color_column = NEW_COLUMN_NAMES[selected_color_column]

    # if selected_color_column is not None:

    fig1 = generate_parallel_categories(df_exploded_parallel)
    st.plotly_chart(fig1, use_container_width=True)

    # selected_options_corr = st.multiselect(
    #     "Choose variables to generate the correlation plot",
    #     available_columns,
    #     format_func=lambda text: NEW_COLUMN_NAMES[text],
    # )

    # df_corr = generate_correlations(df_full, available_columns)

    # if len(selected_options_corr) > 0:
    #     selected_options_corr_renamed = [NEW_COLUMN_NAMES[idx] for idx in selected_options_corr]
    #     df_corr_filtered = df_corr.loc[selected_options_corr_renamed, selected_options_corr_renamed]
    #     fig2, ax = plt.subplots()
    #     ax = sns.heatmap(df_corr_filtered, annot=True)
    #     st.pyplot(fig2)
    #     # df_exploded_corr
