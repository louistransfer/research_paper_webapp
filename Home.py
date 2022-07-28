import streamlit as st
from logzero import logger
from analyser.streamlit_helpers import initialize_session_state
from analyser.api_helpers import import_form_data, import_gsheet_data
from analyser.viz_helpers import generate_funnel

st.set_page_config(layout="wide", page_icon="🏠")

# Loading config files
if "IS_INITIALIZED" not in st.session_state:
    initialize_session_state(st.session_state, st.secrets)

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


tab_introduction, tab_funnel = st.tabs(["Introduction", "Survey advancement"])

with tab_introduction:
    st.image(st.session_state["UNIFIED_LOGO"], width=600)
    st.title("Using data science to enhance Venture Capital deals")
    with open(st.session_state["INTRODUCTION_PATH"], "r") as md_file:
        st.markdown(md_file.read())


with tab_funnel:
    # st.markdown("---")

    st.write("**Here is the current advancement of my survey:**")

    fig = generate_funnel(df_tracking, df_forms)
    st.plotly_chart(fig)

    st.markdown(
        """If you are a data science or software engineering professional working in a VC firm, 
        don't hesitate to <a href="About_Me" target = "_self"> 
        send me a message 
    </a>
        if you want to participate in the survey !""",
        unsafe_allow_html=True,
    )
