# backend/app/services/job_search_service.py
import concurrent.futures
from typing import List, Dict, Any
from app.integrations.search.tavily_client import tavily_client
from app.integrations.search.url_validator import JobURLValidator
from app.services.company_intelligence_service import company_intel
from app.services.job_ranking_service import job_ranking_service
from app.repositories.job_repository import job_repo
from app.core.logging import logger

CURATED_HIGH_QUALITY_POOL = [
    "https://job-boards.greenhouse.io/gitlab/jobs/8704363002",
    "https://job-boards.greenhouse.io/canonical/jobs/5643440",
    "https://job-boards.greenhouse.io/mongodb/jobs/8083366",
    "https://jobs.lever.co/zimperium/5b35759a-d445-4fcb-b255-d719330af055",
    "https://job-boards.greenhouse.io/moduscreate/jobs/7977989003",
]


class JobSearchService:
    @staticmethod
    def generate_search_queries(profile: Dict[str, Any]) -> List[str]:
        """
        Constructs multi-vector search queries covering:
        1. Role + Location + direct ATS boards
        2. Recognized Tier A tech companies + Role
        3. High-signal venture AI startups + Role
        4. Primary Candidate Skills + Role
        """
        role = profile.get("target_role") or "Software Engineer"
        location = profile.get("target_location") or ""
        
        skills = profile.get("skills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        top_skill = skills[0] if skills else "Python"
        second_skill = skills[1] if len(skills) > 1 else ""

        loc_clause = f"{location}" if location else ""

        queries = [
            # 1. Direct ATS role search
            f'(site:job-boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com) {role} {loc_clause} apply',
            # 2. Top tier brand search
            f'(site:job-boards.greenhouse.io OR site:jobs.lever.co) (Google OR Amazon OR Microsoft OR Uber OR Atlassian OR Stripe) {role}',
            # 3. High-signal startup & AI labs search
            f'(site:job-boards.greenhouse.io OR site:jobs.ashbyhq.com) (Anthropic OR OpenAI OR Scale OR Perplexity OR Supabase OR Vercel) {role}',
            # 4. Tech stack specific
            f'(site:job-boards.greenhouse.io OR site:jobs.lever.co) {role} {top_skill} {second_skill} jobs'
        ]
        return [q.strip() for q in queries]

    def discover_and_rank_jobs(
        self,
        profile: Dict[str, Any],
        user_id: str = "user_default",
        target_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Autonomous Multi-Step Discovery Pipeline:
        1. Generate multi-vector queries.
        2. Run Tavily searches in parallel thread pool.
        3. Validate URLs & scrape job pages (rejecting generic portals & 404s).
        4. Deduplicate by fingerprint.
        5. Score with multi-factor ranking (skill match + freshness decay + company tier).
        6. Apply balanced company mix (Recognizable + Scaleup + Emerging).
        7. Persist to DB and return.
        """
        queries = self.generate_search_queries(profile)
        candidate_urls: List[str] = []

        logger.info(f"Executing multi-query search for role '{profile.get('target_role')}'...")

        # 1. Parallel Tavily Discovery
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_query = {executor.submit(tavily_client.search_urls, q, max_results=6): q for q in queries}
            for future in concurrent.futures.as_completed(future_to_query):
                try:
                    urls = future.result()
                    for u in urls:
                        if u not in candidate_urls:
                            candidate_urls.append(u)
                except Exception as e:
                    logger.warning(f"Query thread error: {e}")

        # Fallback pool if search API returned 0
        if not candidate_urls:
            candidate_urls = list(CURATED_HIGH_QUALITY_POOL)

        # 2. Strict Real-Time URL Verification & Scraping in parallel
        verified_jobs: List[Dict[str, Any]] = []
        seen_fingerprints = set()

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_to_url = {executor.submit(JobURLValidator.verify_and_extract_job, u): u for u in candidate_urls[:15]}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    job_schema = future.result()
                    if job_schema and job_schema.is_verified:
                        fp = f"{job_schema.company.lower()}|{job_schema.title.lower()}"
                        if fp not in seen_fingerprints:
                            seen_fingerprints.add(fp)
                            verified_jobs.append(job_schema.model_dump())
                except Exception as e:
                    logger.warning(f"Verification error: {e}")

        if not verified_jobs:
            # Fallback to database jobs if any
            verified_jobs = job_repo.get_jobs(user_id=user_id, limit=target_count)

        # 3. Multi-Factor Scoring & Reasoning
        ranked_jobs = job_ranking_service.rank_and_enrich_jobs(verified_jobs, profile)

        # 4. Balanced Company Mix
        diversified_jobs = company_intel.balance_company_mix(ranked_jobs, target_count=target_count)

        # 5. Persist to SQLite
        if diversified_jobs:
            job_repo.save_jobs(diversified_jobs, user_id=user_id)

        logger.info(f"Discovery complete: {len(diversified_jobs)} high-quality diversified jobs ready.")
        return diversified_jobs

    def execute_search_and_rank(
        self,
        user_id: str = "user_default",
        query: str = "",
        target_roles: list = None,
        max_results: int = 12,
        progress_callback = None,
    ) -> List[Dict[str, Any]]:
        """
        Full orchestration of background job discovery, verification, multi-factor scoring,
        and company diversification with fine-grained progress updates.
        """
        from app.repositories.profile_repository import ProfileRepository
        from app.services.profile_service import ProfileService

        def notify(stage: str, percent: int, msg: str):
            if progress_callback:
                progress_callback(stage, percent, msg)
            logger.info(f"[{user_id}] ({percent}%) {stage}: {msg}")

        notify("FETCHING_PROFILE", 10, "Loading candidate profile and preferences...")
        p_repo = ProfileRepository()
        prof_obj = p_repo.get_profile(user_id)
        prof_dict = ProfileService.to_legacy_dict(prof_obj)

        if query:
            prof_dict["target_role"] = query
        elif target_roles and len(target_roles) > 0:
            prof_dict["target_role"] = target_roles[0]

        notify("GENERATING_QUERIES", 25, "Synthesizing multi-vector search queries (ATS, Brands, Startups)...")
        queries = self.generate_search_queries(prof_dict)
        candidate_urls: List[str] = []

        notify("SEARCHING_SOURCES", 45, f"Running parallel discovery across Greenhouse, Lever, Ashby ({len(queries)} vectors)...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_query = {executor.submit(tavily_client.search_urls, q, max_results=6): q for q in queries}
            for future in concurrent.futures.as_completed(future_to_query):
                try:
                    urls = future.result()
                    for u in urls:
                        if u not in candidate_urls:
                            candidate_urls.append(u)
                except Exception as e:
                    logger.warning(f"Search vector error: {e}")

        if not candidate_urls:
            candidate_urls = list(CURATED_HIGH_QUALITY_POOL)

        notify("VALIDATING_URLS", 65, f"Scraping & validating {min(len(candidate_urls), 15)} direct job postings...")
        verified_jobs: List[Dict[str, Any]] = []
        seen_fingerprints = set()

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_to_url = {executor.submit(JobURLValidator.verify_and_extract_job, u): u for u in candidate_urls[:15]}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    job_schema = future.result()
                    if job_schema and job_schema.is_verified:
                        fp = f"{job_schema.company.lower()}|{job_schema.title.lower()}"
                        if fp not in seen_fingerprints:
                            seen_fingerprints.add(fp)
                            verified_jobs.append(job_schema.model_dump())
                except Exception as e:
                    logger.warning(f"URL extraction error: {e}")

        if not verified_jobs:
            verified_jobs = job_repo.get_jobs(user_id=user_id, limit=max_results)

        notify("SCORING_AND_RANKING", 80, "Calculating multi-factor scores (Skills, Freshness, Company Signal)...")
        ranked_jobs = job_ranking_service.rank_and_enrich_jobs(verified_jobs, prof_dict)

        notify("BALANCING_MIX", 90, "Balancing company mix (Tier A leaders, Tier B startups, Tier C emerging)...")
        diversified_jobs = company_intel.balance_company_mix(ranked_jobs, target_count=max_results)

        if diversified_jobs:
            job_repo.save_jobs(diversified_jobs, user_id=user_id)

        notify("COMPLETED", 100, f"Discovered {len(diversified_jobs)} high-quality job postings.")
        return diversified_jobs


job_search_service = JobSearchService()
