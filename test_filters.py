import requests
import json
import re

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
    if not user_loc: return True
    job_loc_lower = normalize_location(job_loc)
    user_loc_lower = normalize_location(user_loc)
    if "worldwide" in job_loc_lower or "anywhere" in job_loc_lower or "global" in job_loc_lower: return True
    if "remote" in job_loc_lower and not any(c in job_loc_lower for c in ["usa", "us only", "uk only", "europe only", "emea", "latam", "canada only"]): return True
    if user_loc_lower in job_loc_lower or job_loc_lower in user_loc_lower: return True
    if "india" in user_loc_lower:
        if any(c in job_loc_lower for c in ["usa", "us", "united states", "uk", "united kingdom", "canada", "germany", "europe"]) and "india" not in job_loc_lower:
            return False
    return True

# Mock request
response = requests.get("https://remotive.com/api/remote-jobs?search=machine learning&limit=50")
jobs = response.json().get("jobs", [])

target_roles = ["AI Engineer Intern"]
candidate_skills = ["Python", "Machine Learning", "FastAPI", "SQL"]
user_location = "India"
user_experience = "Intern"

raw_jobs = len(jobs)
loc_removed = 0
exp_removed = 0
role_removed = 0
finally_displayed = []

for j in jobs:
    title_lower = j.get("title", "").lower()
    desc = j.get("description", "").lower()
    text_to_search = f"{title_lower} {desc}"
    
    # 1. Location
    if not check_location_compatible(j.get("candidate_required_location", ""), user_location):
        loc_removed += 1
        continue
        
    # 2. Experience
    user_exp_lower = user_experience.lower()
    is_intern_search = True
    job_is_senior = any(re.search(rf'\b{k}\b', title_lower) for k in SENIOR_KEYWORDS)
    job_is_intern = any(re.search(rf'\b{k}\b', title_lower) for k in INTERN_KEYWORDS)
    
    if is_intern_search and job_is_senior:
        exp_removed += 1
        continue
        
    # 3. Role Relevance
    role_score = 0
    for role in target_roles:
        role_lower = role.strip().lower()
        domain_role = role_lower.replace("intern", "").strip()
        if domain_role and domain_role in title_lower:
            role_score = 40
            break
        elif any(part in title_lower for part in domain_role.split() if len(part) > 3):
            role_score = max(role_score, 20)
    if role_score == 0:
        for role in target_roles:
            domain_role = role.strip().lower().replace("intern", "").strip()
            if domain_role and domain_role in desc:
                role_score = 15
                break
                
    if role_score == 0:
        role_removed += 1
        continue
        
    has_any_skill = any(normalize_skill(s) in text_to_search for s in candidate_skills)
    if role_score < 40 and not has_any_skill:
        role_removed += 1
        continue
        
    # Passed all filters
    finally_displayed.append({
        "title": j.get("title"),
        "company": j.get("company_name"),
        "role_score": role_score
    })

print(f"Raw jobs: {raw_jobs}")
print(f"Removed by location: {loc_removed}")
print(f"Removed by experience: {exp_removed}")
print(f"Removed by role: {role_removed}")
print(f"Displayed: {len(finally_displayed)}")
for d in finally_displayed[:5]:
    print(d)
