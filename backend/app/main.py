from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.schemas.candidate import CandidateProfile
from backend.app.schemas.job import JobSearchRequest, JobSearchResponse, CandidateJobMatchResponse, JobResponse
from backend.app.database.database import SessionLocal, engine, Base
from backend.app.models.candidate import Candidate
from backend.app.models.job import Job
from backend.app.services.job_discovery import JobDiscoveryService, calculate_match_score
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

# Initialize services
job_service = JobDiscoveryService()


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


# --------------------------------------------------
# Get Candidate by ID
# --------------------------------------------------

@app.get("/candidate/{candidate_id}")
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):

    # Find candidate in database
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id
    ).first()

    # Candidate not found
    if not candidate:
        return {
            "message": "Candidate not found"
        }

    # Return candidate data
    return {
        "candidate_id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "target_roles": candidate.target_roles,
        "skills": candidate.skills,
        "preferred_location": candidate.preferred_location,
        "experience_level": candidate.experience_level,
        "resume_filename": candidate.resume_filename
    }


# --------------------------------------------------
# Job Search
# --------------------------------------------------

@app.post("/jobs/search", response_model=JobSearchResponse)
def search_jobs(
    request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    result = job_service.discover_jobs(request, db)
    
    # Process and filter jobs
    target_roles = [request.query] if request.query else []
    
    matched_jobs = []
    for job in result["jobs"]:
        score_data = calculate_match_score(
            job=job,
            candidate_skills=request.skills or [],
            target_roles=target_roles,
            user_location=request.location or "",
            user_experience=request.experience_level or ""
        )
        
        if score_data is not None:
            job_dict = {
                "id": job.id,
                "source": job.source,
                "external_job_id": job.external_job_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "job_url": job.job_url,
                "employment_type": job.employment_type,
                "experience_level": job.experience_level,
                "posted_at": job.posted_at,
                "discovered_at": job.discovered_at,
                "match_score": score_data["match_score"],
                "matching_skills": score_data["matching_skills"],
                "missing_skills": score_data["missing_skills"],
                "match_reasons": score_data["match_reasons"]
            }
            matched_jobs.append(job_dict)
            
    # Sort: Match score DESC, then role relevance, etc.
    matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Optional: hard limit to requested amount
    limit = request.limit if request.limit else 20
    final_jobs = matched_jobs[:limit]

    return {
        "count": len(final_jobs),
        "jobs": final_jobs,
        "errors": result["errors"]
    }


# --------------------------------------------------
# Candidate Job Matching
# --------------------------------------------------

@app.get("/candidates/{candidate_id}/jobs", response_model=CandidateJobMatchResponse)
def get_candidate_jobs(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    # Find candidate
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Get recent jobs (e.g., last 200) to filter from
    jobs = db.query(Job).order_by(Job.discovered_at.desc()).limit(200).all()
    
    # Parse candidate lists
    candidate_skills = [s.strip() for s in candidate.skills.split(",")] if candidate.skills else []
    target_roles = [r.strip() for r in candidate.target_roles.split(",")] if candidate.target_roles else []
    
    matched_jobs = []
    for job in jobs:
        score_data = calculate_match_score(
            job=job,
            candidate_skills=candidate_skills,
            target_roles=target_roles,
            user_location=candidate.preferred_location or "",
            user_experience=candidate.experience_level or ""
        )
        
        if score_data is not None:
            job_dict = {
                "id": job.id,
                "source": job.source,
                "external_job_id": job.external_job_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "job_url": job.job_url,
                "employment_type": job.employment_type,
                "experience_level": job.experience_level,
                "posted_at": job.posted_at,
                "discovered_at": job.discovered_at,
                "match_score": score_data["match_score"],
                "matching_skills": score_data["matching_skills"],
                "missing_skills": score_data["missing_skills"],
                "match_reasons": score_data["match_reasons"]
            }
            matched_jobs.append(job_dict)
        
    # Sort by match score descending
    matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Limit to top 20 for UI brevity
    return {
        "candidate_id": candidate_id,
        "jobs": matched_jobs[:20]
    }