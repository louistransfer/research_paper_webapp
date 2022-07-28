import streamlit as st
import plotly.express as px
from analyser.df_processing import generate_value_counts_df
from analyser.streamlit_helpers import generate_excel, initialize_session_state
from analyser.api_helpers import import_form_data, import_gsheet_data
from analyser.viz_helpers import generate_funnel

if "IS_INITIALIZED" not in st.session_state:
    initialize_session_state(st.session_state, st.secrets)

available_columns = st.session_state["COLUMN_NAMES_RENAMING_DICT"].values()

tab_introduction, tab_aggregated_results, tab_anonymized_results = st.tabs(["Survey introduction","Aggregated results", "Anonymized results"])

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

df_forms_anonymized = df_forms.drop(columns=["email", "create_time"])
df_forms_anonymized["Firm ID"] = [
    f"Firm {idx}" for idx in range(1, len(df_forms_anonymized) + 1)
]
df_forms_anonymized.set_index("Firm ID", inplace=True)

with tab_introduction:
    with open(st.session_state["SURVEY_INTRO"], 'r') as md_file:
        st.markdown(md_file.read())

    # fig = generate_funnel(df_tracking, df_forms)

    # st.markdown("---")

    # st.title("Answers funnel")

    # st.plotly_chart(fig)

with tab_aggregated_results:
    selected_column = st.selectbox(
        "Choose a variable to see the answer count",
        available_columns,
    )
    if selected_column in st.session_state["MULTI_CHOICE_COLUMNS"]:
        is_multi_choice_column = True
    else:
        is_multi_choice_column = False

    df_count = generate_value_counts_df(df_forms, selected_column, st.session_state["MULTI_CHOICE_COLUMNS"])

    fig1 = px.bar(
        df_count, x="Number of answers", y="Possible choices", orientation="h",
    )
    fig1.update_layout(
        showlegend=False, yaxis={"ticksuffix": "    "}, font={"size": 18}, width=1000
    )
    fig2 = px.pie(df_count, names="Possible choices", values="Number of answers")
    fig2.update_layout(
        yaxis={"ticksuffix": "    "},
        font={"size": 18},
        # legend={"yanchor": "bottom", "y": 0.3, "xanchor": "center", "x": 1},
        width=1200,
        height=500
    )
    # st.plotly_chart(fig1, width=1000, height=1000)
    # st.plotly_chart(fig2, width=1000, height=1000)
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)

with tab_anonymized_results:
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        if st.button("🔁 Reload GForm data"):
            df_forms = import_form_data(
                st.session_state,
                st.session_state["FRENCH_FORM_ID"],
                st.session_state["ENGLISH_FORM_ID"],
                st.session_state["questions_mapping"],
                st.session_state["translation_mapping"],
                st.session_state["FORMS_CSV_PATH"],
                st.session_state["MULTI_CHOICE_COLUMNS"],
                force_reload=True,
            )

    with col2:
        if st.button("🔁 Reload GSheets data"):
            df_gsheet = import_gsheet_data(
                st.session_state,
                st.session_state["GSHEET_TRACKING_ID"],
                range="Contacts",
                csv_path=st.session_state["TRACKING_CSV_PATH"],
                force_reload=True,
            )

    st.dataframe(data=df_forms_anonymized)

    with col3:
        st.download_button(
            label="Download data as CSV",
            data=df_forms_anonymized.to_csv(encoding="utf-8", sep=";"),
            file_name="survey_results.csv",
            mime="text/csv",
        )

    with col4:
        buffer = generate_excel(df_forms_anonymized)
        st.download_button(
            label="Download data as Excel",
            data=buffer,
            file_name="survey_results.xlsx",
            mime="application/vnd.ms-excel",
        )
