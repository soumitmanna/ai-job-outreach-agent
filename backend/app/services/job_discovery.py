import requests
from typing import List, Dict, Any, Tuple, Optional
from backend.app.schemas.job import JobBase
from backend.app.models.job import Job
from sqlalchemy.orm import Session
import datetime
import html
import re
import os

# Keyword sets for filtering
SENIOR_KEYWORDS = {"senior", "lead", "principal", "manager", "architect", "director", "head", "staff", "sr", "sr."}
INTERN_KEYWORDS = {"intern", "internship", "trainee", "student", "graduate", "fresher", "entry level", "junior", "jr", "jr."}

SKILL_ALIASES = {
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "fast api": "fastapi",
    "js": "javascript",
    "ts": "typescript",
    "ai": "artificial intelligence",
    "genai": "generative ai"
}

def normalize_skill(skill: str) -> str:
    s = skill.strip().lower()
    return SKILL_ALIASES.get(s, s)

def normalize_location(loc: str) -> str:
    return loc.strip().lower() if loc else ""

def check_location_compatible(job_loc: str, user_loc: str) -> bool:
    if not user_loc:
        return True
    job_loc_lower = normalize_location(job_loc)
    user_loc_lower = normalize_location(user_loc)
    
    if "worldwide" in job_loc_lower or "anywhere" in job_loc_lower or "global" in job_loc_lower:
        return True
    
    # If job says remote and doesn't explicitly mention another restricted country
    if "remote" in job_loc_lower and not any(country in job_loc_lower for country in ["usa", "us only", "uk only", "europe only", "emea", "latam", "canada only"]):
        return True
    
    if user_loc_lower in job_loc_lower or job_loc_lower in user_loc_lower:
        return True
        
    # Check for strict mismatches (e.g. user in India, job strictly in USA/UK)
    if "india" in user_loc_lower:
        if any(c in job_loc_lower for c in ["usa", "us", "united states", "uk", "united kingdom", "canada", "germany", "europe"]) and "india" not in job_loc_lower:
            return False
            
    return True

def get_core_search_query(query: str) -> str:
    """Extract core domain to search Remotive more effectively."""
    q_lower = query.lower()
    if "ai" in q_lower or "machine learning" in q_lower:
        return "machine learning"
    if "data" in q_lower:
        return "data"
    if "frontend" in q_lower or "front end" in q_lower or "react" in q_lower:
        return "frontend"
    if "backend" in q_lower or "back end" in q_lower or "python" in q_lower:
        return "backend"
    return query.split()[0] if query else ""

class JobSource:
    def search_jobs(self, query: str, limit: int) -> List[JobBase]:
        raise NotImplementedError

class RemotiveJobSource(JobSource):
    def search_jobs(self, query: str, limit: int) -> List[JobBase]:
        url = "https://remotive.com/api/remote-jobs"
        core_query = get_core_search_query(query)
        # Fetch more to allow aggressive filtering later
        params = {"search": core_query, "limit": max(limit * 3, 50)}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            jobs_data = data.get("jobs", [])
            
            jobs = []
            for j in jobs_data:
                desc = html.unescape(j.get("description", ""))
                desc_clean = re.sub(r'<[^>]+>', '', desc)
                
                jobs.append(JobBase(
                    source="remotive",
                    external_job_id=str(j.get("id")),
                    title=j.get("title", "Unknown"),
                    company=j.get("company_name", "Unknown"),
                    location=j.get("candidate_required_location", "Remote"),
                    description=desc_clean[:1000],
                    job_url=j.get("url", ""),
                    employment_type=j.get("job_type", ""),
                    experience_level=None,
                    posted_at=j.get("publication_date", "")
                ))
            return jobs
        except Exception as e:
            print(f"Remotive API error: {e}")
            raise Exception(f"Remotive error: {e}")

class AshbyJobSource(JobSource):
    def __init__(self, job_boards: List[str]):
        self.job_boards = job_boards

    def search_jobs(self, query: str, limit: int) -> List[JobBase]:
        jobs = []
        for board in self.job_boards:
            url = f"https://api.ashbyhq.com/posting-api/job-board/{board.strip()}"
            params = {"includeCompensation": "false"}
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Ashby doesn't have a direct search query, so we fetch and filter locally
                board_jobs = data.get("jobs", [])
                
                # Filter by core query string locally
                core_query = get_core_search_query(query).lower()
                filtered_board_jobs = []
                for j in board_jobs:
                    j_title = j.get("title", "").lower()
                    j_desc = j.get("descriptionPlain", "").lower()
                    if not core_query or core_query in j_title or core_query in j_desc:
                        filtered_board_jobs.append(j)
                
                for j in filtered_board_jobs[:limit]:
                    title = j.get("title", "Unknown")
                    # company name might not be provided per job, fallback to board name
                    company = j.get("company", board.strip()) 
                    location = j.get("location", "")
                    if j.get("isRemote"):
                        location = f"{location} (Remote)".strip()
                        
                    desc = html.unescape(j.get("descriptionPlain", ""))
                    desc_clean = re.sub(r'<[^>]+>', '', desc)
                    
                    jobs.append(JobBase(
                        source="ashby",
                        external_job_id=str(j.get("id")),
                        title=title,
                        company=company,
                        location=location,
                        description=desc_clean[:1000],
                        job_url=j.get("applyUrl") or j.get("jobUrl", ""),
                        employment_type=j.get("employmentType", ""),
                        experience_level=None,
                        posted_at=j.get("publishedAt", "")
                    ))
            except Exception as e:
                print(f"Ashby API error for {board}: {e}")
                # We do not raise here because we want to try the other boards
                continue 
                
        return jobs

class JobDiscoveryService:
    def __init__(self):
        self.providers: List[JobSource] = [
            RemotiveJobSource()
        ]
        
        ashby_boards_env = os.environ.get("ASHBY_JOB_BOARDS")
        if ashby_boards_env:
            boards = [b.strip() for b in ashby_boards_env.split(",") if b.strip()]
            if boards:
                self.providers.append(AshbyJobSource(boards))

    def discover_jobs(self, search_params, db: Session) -> Dict[str, Any]:
        all_jobs: List[JobBase] = []
        errors = []
        
        for provider in self.providers:
            try:
                jobs = provider.search_jobs(search_params.query, search_params.limit)
                all_jobs.extend(jobs)
            except Exception as e:
                errors.append(f"{provider.__class__.__name__} failed: {str(e)}")

        saved_jobs = []
        for job_data in all_jobs:
            existing_job = db.query(Job).filter(
                Job.source == job_data.source,
                Job.external_job_id == job_data.external_job_id
            ).first()
            
            if not existing_job:
                new_job = Job(
                    source=job_data.source,
                    external_job_id=job_data.external_job_id,
                    title=job_data.title,
                    company=job_data.company,
                    location=job_data.location,
                    description=job_data.description,
                    job_url=job_data.job_url,
                    employment_type=job_data.employment_type,
                    experience_level=job_data.experience_level,
                    posted_at=job_data.posted_at,
                    discovered_at=datetime.datetime.utcnow()
                )
                db.add(new_job)
                try:
                    db.commit()
                    db.refresh(new_job)
                    saved_jobs.append(new_job)
                except Exception as e:
                    db.rollback()
                    errors.append(f"DB save error: {e}")
            else:
                saved_jobs.append(existing_job)
                
        return {
            "jobs": saved_jobs,
            "errors": errors
        }

def calculate_match_score(
    job: Job, 
    candidate_skills: List[str], 
    target_roles: List[str],
    user_location: str,
    user_experience: str
) -> Optional[Dict[str, Any]]:
    
    score = 0
    match_reasons = []
    
    title_lower = job.title.lower()
    desc_lower = (job.description or "").lower()
    text_to_search = f"{title_lower} {desc_lower}"
    
    # --------------------------------------------------
    # 1. HARD FILTERS
    # --------------------------------------------------
    
    if not check_location_compatible(job.location, user_location):
        return None
        
    user_exp_lower = (user_experience or "").lower()
    
    is_intern_search = any(k in user_exp_lower for k in INTERN_KEYWORDS) or \
                       any(k in " ".join(target_roles).lower() for k in INTERN_KEYWORDS)
                       
    job_is_senior = any(re.search(rf'\b{k}\b', title_lower) for k in SENIOR_KEYWORDS)
    job_is_intern = any(re.search(rf'\b{k}\b', title_lower) for k in INTERN_KEYWORDS)
    
    if is_intern_search and job_is_senior:
        return None

    # --------------------------------------------------
    # 2. SCORING
    # --------------------------------------------------
    
    # A. Role Relevance (0 - 40 points)
    role_score = 0
    for role in target_roles:
        role_lower = role.strip().lower()
        if not role_lower:
            continue
        
        # Strip "intern" from target role to find the actual domain if it's there
        domain_role = role_lower.replace("intern", "").strip()
        
        if domain_role and domain_role in title_lower:
            role_score = 40
            match_reasons.append("Strong role match in title")
            break
        elif any(part in title_lower for part in domain_role.split() if len(part) > 3):
            role_score = max(role_score, 20)
            
    if role_score == 0:
        for role in target_roles:
            domain_role = role.strip().lower().replace("intern", "").strip()
            if domain_role and domain_role in desc_lower:
                role_score = 15
                match_reasons.append("Role mentioned in description")
                break
                
    if role_score == 20:
        match_reasons.append("Partial role match in title")
        
    # If it completely misses the role, discard it regardless of skills
    if role_score == 0:
        return None
        
    has_any_skill = False
    for s in candidate_skills:
        skill_norm = normalize_skill(s)
        if skill_norm and skill_norm in text_to_search:
            has_any_skill = True
            break
            
    if role_score < 40 and candidate_skills and not has_any_skill:
        return None
        
    score += role_score

    # B. Experience Relevance (0 - 20 points)
    exp_score = 0
    if is_intern_search and job_is_intern:
        exp_score = 20
        match_reasons.append("Internship/Junior level match")
    elif not is_intern_search and not job_is_intern and not job_is_senior:
        exp_score = 10
        match_reasons.append("Standard experience level")
    elif not is_intern_search and job_is_senior and "senior" in user_exp_lower:
        exp_score = 20
        match_reasons.append("Senior level match")
        
    score += exp_score
    
    # C. Skill Matching (0 - 30 points)
    skill_score = 0
    matching_skills = []
    missing_skills = []
    
    for skill in candidate_skills:
        skill_norm = normalize_skill(skill)
        if skill_norm and skill_norm in text_to_search:
            matching_skills.append(skill.strip())
        elif skill.strip():
            missing_skills.append(skill.strip())
            
    if matching_skills:
        skill_ratio = len(matching_skills) / len(candidate_skills) if candidate_skills else 0
        skill_score = int(skill_ratio * 30)
        match_reasons.append(f"Matched {len(matching_skills)} skills")
        
    score += skill_score
    
    # D. Location Relevance (0 - 10 points)
    loc_score = 0
    user_loc_norm = normalize_location(user_location)
    job_loc_norm = normalize_location(job.location)
    
    if user_loc_norm and (user_loc_norm in job_loc_norm or job_loc_norm in user_loc_norm):
        loc_score = 10
        match_reasons.append("Exact location match")
    elif "remote" in job_loc_norm or "worldwide" in job_loc_norm:
        loc_score = 5
        match_reasons.append("Remote compatible")
        
    score += loc_score
    
    score = min(max(score, 0), 100)
    
    return {
        "match_score": score,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "match_reasons": match_reasons
    }
