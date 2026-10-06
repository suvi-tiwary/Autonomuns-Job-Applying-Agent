def rank_jobs(jobs, profile):
    """
    Rank jobs against the user's profile.

    Currently keeps the jobs returned by the job searcher.
    Replace the scoring logic here when your matching
    implementation is ready.
    """

    if not jobs:
        return []

    ranked_jobs = []

    for job in jobs:
        job = dict(job)

        # Keep an existing score if the searcher already provides one.
        score = job.get("match_score", job.get("similarity", 0))

        job["match_score"] = score

        ranked_jobs.append(job)

    ranked_jobs.sort(
        key=lambda x: x.get("match_score", 0),
        reverse=True
    )

    return ranked_jobs