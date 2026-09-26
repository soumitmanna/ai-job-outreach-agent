from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class JobBase(BaseModel):
    source: str
    external_job_id: str
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    job_url: str
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    posted_at: Optional[str] = None

class JobResponse(JobBase):
    id: int
    discovered_at: datetime
    match_score: Optional[int] = None
    matching_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    match_reasons: Optional[List[str]] = None

    class Config:
        from_attributes = True

class JobSearchRequest(BaseModel):
    query: str
    location: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_level: Optional[str] = None
    limit: Optional[int] = 20

class JobSearchResponse(BaseModel):
    count: int
    jobs: List[JobResponse]
    errors: Optional[List[str]] = None

class CandidateJobMatchResponse(BaseModel):
    candidate_id: int
    jobs: List[JobResponse]
