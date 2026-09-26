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

# --------------------------------------------------
# Job Search UI
# --------------------------------------------------

st.divider()

st.header("🔎 Find Jobs")

col1, col2 = st.columns(2)

with col1:
    search_query = st.text_input("Search Query (e.g. AI Engineer Intern)", key="job_query")
    search_location = st.text_input("Location (e.g. Remote, India)", key="job_location")

with col2:
    search_skills = st.text_input("Skills (comma separated)", key="job_skills")
    search_experience = st.selectbox("Experience Level", ["Student", "Intern", "Entry Level", "Mid Level", "Senior"], key="job_exp")

search_limit = st.slider("Number of Jobs", min_value=1, max_value=50, value=20)

if st.button("🔍 Search Jobs", type="primary"):
    if not search_query:
        st.warning("Please provide a search query.")
    else:
        search_data = {
            "query": search_query,
            "location": search_location if search_location else None,
            "skills": [s.strip() for s in search_skills.split(",")] if search_skills else [],
            "experience_level": search_experience,
            "limit": search_limit
        }
        
        with st.spinner("Searching for jobs..."):
            try:
                response = requests.post("http://127.0.0.1:8000/jobs/search", json=search_data)
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    st.success(f"Found {len(jobs)} jobs!")
                    
                    if data.get("errors"):
                        for err in data["errors"]:
                            st.warning(err)
                            
                    for job in jobs:
                        score = job.get('match_score', 0)
                        with st.expander(f"{job['title']} @ {job['company']} (Score: {score})"):
                            st.write(f"**Location:** {job.get('location', 'N/A')}")
                            st.write(f"**Match Score:** {score}/100")
                            
                            match_skills = job.get('matching_skills', [])
                            if match_skills:
                                st.write(f"**✅ Matching Skills:** {', '.join(match_skills)}")
                                
                            miss_skills = job.get('missing_skills', [])
                            if miss_skills:
                                st.write(f"**❌ Missing Skills:** {', '.join(miss_skills)}")
                                
                            reasons = job.get('match_reasons', [])
                            if reasons:
                                st.write(f"**💡 Match Reasons:** {', '.join(reasons)}")
                                
                            st.write(f"**Source:** {job['source']}")
                            if job.get('description'):
                                st.write(f"**Description Snippet:** {job['description'][:300]}...")
                            st.markdown(f"[View Job]({job['job_url']})")
                else:
                    st.error(f"Error searching jobs: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to FastAPI backend.")


# --------------------------------------------------
# Candidate-Based Job Search
# --------------------------------------------------

st.divider()

st.header("🎯 Find Jobs for My Profile")

match_candidate_id = st.number_input("Enter Candidate ID", min_value=1, step=1, value=1)

if st.button("Find Matching Jobs"):
    with st.spinner("Matching jobs for candidate..."):
        try:
            response = requests.get(f"http://127.0.0.1:8000/candidates/{match_candidate_id}/jobs")
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                st.success(f"Found {len(jobs)} matched jobs!")
                
                for job in jobs:
                    score = job.get('match_score', 0)
                    with st.expander(f"{job['title']} @ {job['company']} (Score: {score})"):
                        st.write(f"**Location:** {job.get('location', 'N/A')}")
                        st.write(f"**Match Score:** {score}/100")
                        
                        match_skills = job.get('matching_skills', [])
                        if match_skills:
                            st.write(f"**✅ Matching Skills:** {', '.join(match_skills)}")
                            
                        miss_skills = job.get('missing_skills', [])
                        if miss_skills:
                            st.write(f"**❌ Missing Skills:** {', '.join(miss_skills)}")
                            
                        reasons = job.get('match_reasons', [])
                        if reasons:
                            st.write(f"**💡 Match Reasons:** {', '.join(reasons)}")
                            
                        st.write(f"**Source:** {job['source']}")
                        if job.get('description'):
                            st.write(f"**Description Snippet:** {job['description'][:300]}...")
                        st.markdown(f"[View Job]({job['job_url']})")
            elif response.status_code == 404:
                st.error("Candidate not found.")
            else:
                st.error(f"Error matching jobs: {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to FastAPI backend.")