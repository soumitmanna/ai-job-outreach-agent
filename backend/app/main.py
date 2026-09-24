from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from backend.app.schemas.candidate import CandidateProfile
from backend.app.database.database import SessionLocal
from backend.app.models.candidate import Candidate


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="AI Job Outreach Agent",
    description="Backend API for the AI Job Outreach Agent",
    version="0.1.0"
)


# --------------------------------------------------
# Database Dependency
# --------------------------------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "AI Job Outreach Agent API is running"
    }


# --------------------------------------------------
# Create Candidate
# --------------------------------------------------

@app.post("/candidate")
def create_candidate(
    candidate: CandidateProfile,
    db: Session = Depends(get_db)
):

    # Create database object
    new_candidate = Candidate(
        name=candidate.name,
        email=str(candidate.email) if candidate.email else None,
        target_roles=", ".join(candidate.target_roles),
        skills=", ".join(candidate.skills),
        preferred_location=candidate.preferred_location,
        experience_level=candidate.experience_level,
        resume_filename=candidate.resume_filename
    )

    # Save to database
    db.add(new_candidate)
    db.commit()

    # Get generated database ID
    db.refresh(new_candidate)

    return {
        "message": "Candidate profile saved successfully",
        "candidate_id": new_candidate.id,
        "candidate": candidate
    }