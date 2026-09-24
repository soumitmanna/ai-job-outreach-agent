import streamlit as st
import requests


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Job Outreach Agent",
    page_icon="💼",
    layout="wide"
)


# --------------------------------------------------
# Main Header
# --------------------------------------------------

st.title("💼 AI Job Outreach Agent")

st.write(
    "Find relevant job opportunities, understand your fit, "
    "and generate personalized outreach."
)

st.divider()


# --------------------------------------------------
# Candidate Information
# --------------------------------------------------

st.header("👤 Your Job Preferences")


# Resume Upload
resume = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx"]
)


# Name
name = st.text_input(
    "Your Name",
    placeholder="e.g. Soumit Manna"
)


# Email
email = st.text_input(
    "Email",
    placeholder="e.g. soumit@example.com"
)


# Target Job Role
target_role = st.text_input(
    "Target Job Role",
    placeholder="e.g. Machine Learning Engineer Intern"
)


# Skills
skills = st.text_input(
    "Skills",
    placeholder="e.g. Python, PyTorch, FastAPI, SQL"
)


# Preferred Location
location = st.text_input(
    "Preferred Location",
    placeholder="e.g. India, Kolkata, Remote"
)


# Experience Level
experience = st.selectbox(
    "Experience Level",
    [
        "Student",
        "Intern",
        "Entry Level",
        "1-2 Years",
        "3+ Years"
    ]
)


st.divider()


# --------------------------------------------------
# Create Candidate Profile
# --------------------------------------------------

if st.button(
    "🚀 Create Candidate Profile",
    type="primary"
):

    # ----------------------------------------------
    # Basic Validation
    # ----------------------------------------------

    if not name or not target_role or not skills:

        st.warning(
            "Please provide your name, target role, and skills."
        )

    else:

        # ------------------------------------------
        # Prepare Candidate Data
        # ------------------------------------------

        candidate_data = {
            "name": name,
            "email": email if email else None,

            "target_roles": [
                target_role
            ],

            "skills": [
                skill.strip()
                for skill in skills.split(",")
            ],

            "preferred_location": (
                location if location else None
            ),

            "experience_level": experience,

            "resume_filename": (
                resume.name if resume else None
            )
        }


        # ------------------------------------------
        # Send Data to FastAPI
        # ------------------------------------------

        try:

            response = requests.post(
                "http://127.0.0.1:8000/candidate",
                json=candidate_data
            )


            # --------------------------------------
            # Successful Response
            # --------------------------------------

            if response.status_code == 200:

                st.success(
                    "Candidate profile created successfully!"
                )

                st.subheader("Candidate Profile")

                st.json(
                    response.json()
                )


            # --------------------------------------
            # API Error
            # --------------------------------------

            else:

                st.error(
                    f"API Error: {response.status_code}"
                )


        # ------------------------------------------
        # FastAPI Not Running
        # ------------------------------------------

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to the FastAPI backend. "
                "Make sure the FastAPI server is running."
            )