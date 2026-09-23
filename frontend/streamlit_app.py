import streamlit as st


st.set_page_config(
    page_title="AI Job Outreach Agent",
    page_icon="💼",
    layout="wide"
)


st.title("💼 AI Job Outreach Agent")

st.write(
    "Find relevant job opportunities, understand your fit, "
    "and generate personalized outreach."
)


st.divider()


st.header("👤 Your Job Preferences")


resume = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx"]
)


target_role = st.text_input(
    "Target Job Role",
    placeholder="e.g. Machine Learning Engineer Intern"
)


skills = st.text_input(
    "Skills",
    placeholder="e.g. Python, PyTorch, FastAPI, SQL"
)


location = st.text_input(
    "Preferred Location",
    placeholder="e.g. India, Kolkata, Remote"
)


st.divider()


if st.button(
    "🔎 Find Opportunities",
    type="primary"
):

    st.info(
        "Job discovery will be connected in a later phase."
    )