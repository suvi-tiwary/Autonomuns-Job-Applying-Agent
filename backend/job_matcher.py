from typing import List, Dict, Any


def calculate_match_score(job: Dict[str, Any], profile: Dict[str, Any]) -> float:
    candidate_skills = profile.get("skills", [])
    if isinstance(candidate_skills, str):
        candidate_skills = [s.strip() for s in candidate_skills.split(",") if s.strip()]
    candidate_skills_lower = set(s.lower() for s in candidate_skills)

    job_text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
        " ".join(job.get("skills", []))
    ]).lower()

    if not candidate_skills_lower:
        return 82.0

    matched = 0
    total_checked = min(len(candidate_skills_lower), 8)
    for skill in list(candidate_skills_lower)[:8]:
        if skill in job_text:
            matched += 1

    # Base match calculation
    score = 70.0 + (matched / max(total_checked, 1)) * 26.0

    # Boost if target role keyword matches
    target_role = (profile.get("target_role") or "").lower()
    if target_role and target_role in job.get("title", "").lower():
        score += 3.5

    return round(min(score, 98.0), 1)


def rank_jobs(jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not jobs:
        return []

    ranked = []
    for job in jobs:
        job_copy = dict(job)
        job_copy["match_score"] = calculate_match_score(job_copy, profile)
        ranked.append(job_copy)

    ranked.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return ranked