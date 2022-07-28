import streamlit as st
from analyser.streamlit_helpers import initialize_session_state
from analyser.streamlit_helpers import display_online_pdf, get_file_from_google_drive

if "IS_INITIALIZED" not in st.session_state:
    initialize_session_state(st.session_state, st.secrets)

radio_choice = st.selectbox("Select the Research paper itself or the Research paper Defence slides.", options=["Research Paper", "Defence slides"])

if radio_choice == "Research Paper":
    # st.title("Research Paper")

    st.download_button(
        label="📄 Download Research Paper as pdf",
        data=get_file_from_google_drive(st.session_state["RESEARCH_PAPER_PDF_ID"]),
        file_name="ResearchPaper.pdf",
        mime="application/octet-stream"
    )
    display_online_pdf(st.session_state["RESEARCH_PAPER_PDF_ID"])

elif radio_choice == "Defence slides":
    # st.title("Defence slides")
    st.download_button(
        label="📄 Download Research Paper Defence Slides as pdf",
        data=get_file_from_google_drive(st.session_state["DEFENSE_PDF_ID"]),
        file_name="ResearchPaperDefence.pdf",
        mime="application/octet-stream"
    )
    display_online_pdf(st.session_state["DEFENSE_PDF_ID"])
