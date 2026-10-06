import os
import json
import urllib.request


TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def search_jobs(profile):

    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not set")

    skills = ", ".join(profile.get("skills", []))

    projects = " ".join(
        project.get("name", "")
        for project in profile.get("projects", [])
        if isinstance(project, dict)
    )

    query = f"""
AI ML software engineering jobs internships
for candidate with skills {skills}
projects {projects}
India remote
"""

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "max_results": 10
    }

    request = urllib.request.Request(
        "https://api.tavily.com/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=60) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    jobs = []

    for item in result.get("results", []):

        jobs.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("content", ""),
            "source": "tavily"
        })

    return jobs

def rank_jobs(jobs, profile):

    matched_jobs = []

    for job in jobs:

        result = calculate_match(
            job,
            profile
        )

        matched_jobs.append(result)

    matched_jobs.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    return matched_jobs