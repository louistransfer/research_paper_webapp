import streamlit as st
from analyser.streamlit_helpers import initialize_session_state

if "IS_INITIALIZED" not in st.session_state:
    initialize_session_state(st.session_state, st.secrets)


st.title("About me")
col1, col2 = st.columns([1, 2])
with col1:
    st.image(st.session_state["IDENTITY_PHOTO"], width=200)

with col2:
    with open(st.session_state["RESUME_PATH"], "rb") as resume_file:
        st.download_button(
        label="📄 Download my resume (English)",
        data=resume_file,
        file_name="Resume - Louis Bertolotti.pdf",
        mime="application/octet-stream"
    )

    with open(st.session_state["CV_PATH"], "rb") as cv_file:
        st.download_button(
        label="📄 Download my CV (French)",
        data=cv_file,
        file_name="CV - Louis Bertolotti.pdf",
        mime="application/octet-stream"
    )

    with open(st.session_state["CONTACT_INFORMATION"], 'r') as md_file:
        st.markdown(md_file.read())
    

with open(st.session_state["PERSONAL_PRESENTATION"], 'r') as md_file:
    st.markdown(md_file.read())

