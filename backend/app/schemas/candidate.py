from pydantic import BaseModel, EmailStr
from typing import List, Optional


class CandidateProfile(BaseModel):

    name: str

    email: Optional[EmailStr] = None

    target_roles: List[str]

    skills: List[str]

    preferred_location: Optional[str] = None

    experience_level: Optional[str] = None

    resume_filename: Optional[str] = None