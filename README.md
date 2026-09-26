# AI Job Outreach Agent

An MVP application to discover jobs and match them with a candidate's profile.

## Features
- Save candidate profiles (skills, target roles, experience)
- **Job Discovery**: Discovers real job listings using the Remotive Public API.
- **Job Matching**: Deterministic, explainable matching based on skills and target roles.
- Streamlit web interface for easy usage.

## Setup & Running

1. **Virtual Environment**
   Activate your existing virtual environment:
   ```bash
   # Windows
   venv\Scripts\activate
   ```

2. **Dependencies**
   Install the required dependencies (if you haven't already):
   ```bash
   pip install -r requirements.txt
   ```

3. **Start FastAPI Backend**
   ```bash
   uvicorn backend.app.main:app --reload
   ```

4. **Start Streamlit Frontend**
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

## Workflow

1. Open the Streamlit frontend.
2. Under **Your Job Preferences**, enter your details and click **Create Candidate Profile**.
3. Scroll down to **Find Jobs** to manually search for jobs by query (e.g. "AI Engineer").
4. Scroll down to **Find Jobs for My Profile**, enter your generated Candidate ID, and click **Find Matching Jobs** to view matching jobs based on your saved profile.

## Supported Job Sources
- **Remotive API** (Public, remote jobs)

*Note: No environment variables or API keys are required for this basic MVP using Remotive.*
