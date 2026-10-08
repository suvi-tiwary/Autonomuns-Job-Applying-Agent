# backend/app/repositories/job_repository.py
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.models.job import JobSchema, CompanyTier


def _compute_job_hash(company: str, title: str, location: str, job_url: str) -> str:
    raw = f"{company.strip().lower()}|{title.strip().lower()}|{location.strip().lower()}|{job_url.split('?')[0].strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class JobRepository:
    def save_jobs(self, jobs_list: List[Dict[str, Any]], user_id: str = "user_default") -> List[Dict[str, Any]]:
        if not jobs_list:
            return []

        saved = []
        with get_db() as conn:
            cursor = conn.cursor()

            for job in jobs_list:
                job_dict = dict(job)
                title = job_dict.get("title") or "Untitled Role"
                company = job_dict.get("company") or "Company"
                location = job_dict.get("location") or "Remote"
                job_url = job_dict.get("job_url") or job_dict.get("url") or f"job-{hash(title)}"
                apply_url = job_dict.get("apply_url") or job_url
                
                job_hash = _compute_job_hash(company, title, location, job_url)
                job_id = job_dict.get("id") or job_hash
                job_dict["id"] = job_id
                job_dict["job_hash"] = job_hash

                requirements = json.dumps(job_dict.get("requirements", []), ensure_ascii=False)
                responsibilities = json.dumps(job_dict.get("responsibilities", []), ensure_ascii=False)
                skills = json.dumps(job_dict.get("skills", []), ensure_ascii=False)
                why_rec = json.dumps(job_dict.get("why_recommended", []), ensure_ascii=False)
                raw_json = json.dumps(job_dict, ensure_ascii=False)

                tier_val = job_dict.get("company_tier")
                if hasattr(tier_val, "value"):
                    tier_val = tier_val.value
                elif not tier_val:
                    tier_val = "emerging"

                freshness_score = float(job_dict.get("freshness_score", 80.0) or 80.0)
                company_score = float(job_dict.get("company_score", 70.0) or 70.0)
                match_score = float(job_dict.get("match_score", 85.0) or 85.0)
                final_score = float(job_dict.get("final_score", 80.0) or 80.0)

                # Upsert into global jobs pool
                cursor.execute("""
                    INSERT INTO jobs (
                        id, external_id, title, company, company_domain, company_tier,
                        location, remote_type, employment_type, description, requirements,
                        responsibilities, skills, salary, posted_at, discovered_at, verified_at,
                        is_verified, job_url, apply_url, source, source_type, ats,
                        freshness_score, company_score, match_score, final_score,
                        url_validated, why_recommended, status, job_hash, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(job_url) DO UPDATE SET
                        title = excluded.title,
                        company = excluded.company,
                        company_tier = excluded.company_tier,
                        location = excluded.location,
                        remote_type = excluded.remote_type,
                        employment_type = excluded.employment_type,
                        description = excluded.description,
                        requirements = excluded.requirements,
                        responsibilities = excluded.responsibilities,
                        skills = excluded.skills,
                        salary = excluded.salary,
                        apply_url = excluded.apply_url,
                        ats = excluded.ats,
                        freshness_score = excluded.freshness_score,
                        company_score = excluded.company_score,
                        match_score = excluded.match_score,
                        final_score = excluded.final_score,
                        why_recommended = excluded.why_recommended,
                        is_verified = excluded.is_verified,
                        raw_json = excluded.raw_json
                """, (
                    job_id,
                    job_dict.get("external_id"),
                    title,
                    company,
                    job_dict.get("company_domain"),
                    tier_val,
                    location,
                    job_dict.get("remote_type", "Remote"),
                    job_dict.get("employment_type", "Full-time"),
                    job_dict.get("description", ""),
                    requirements,
                    responsibilities,
                    skills,
                    job_dict.get("salary", ""),
                    job_dict.get("posted_at", ""),
                    job_dict.get("discovered_at") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    job_dict.get("verified_at") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    1 if job_dict.get("is_verified", True) else 0,
                    job_url,
                    apply_url,
                    job_dict.get("source", "ATS"),
                    job_dict.get("source_type", "direct_ats"),
                    job_dict.get("ats", "custom"),
                    freshness_score,
                    company_score,
                    match_score,
                    final_score,
                    1 if job_dict.get("url_validated", True) else 0,
                    why_rec,
                    job_dict.get("status", "VERIFIED"),
                    job_hash,
                    raw_json
                ))

                # Upsert into user_job_matches table for personalized ranking per user
                cursor.execute("""
                    INSERT INTO user_job_matches (
                        user_id, job_id, match_score, freshness_score, company_score, final_score, why_recommended
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, job_id) DO UPDATE SET
                        match_score = excluded.match_score,
                        freshness_score = excluded.freshness_score,
                        company_score = excluded.company_score,
                        final_score = excluded.final_score,
                        why_recommended = excluded.why_recommended
                """, (user_id, job_id, match_score, freshness_score, company_score, final_score, why_rec))

                saved.append(job_dict)

            conn.commit()
        return saved

    def get_jobs(self, user_id: str = "user_default", limit: int = 100) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Select joined with user_job_matches if exists
            cursor.execute("""
                SELECT j.*, 
                       COALESCE(m.match_score, j.match_score) as user_match_score,
                       COALESCE(m.final_score, j.final_score) as user_final_score,
                       COALESCE(m.why_recommended, j.why_recommended) as user_why_recommended
                FROM jobs j
                LEFT JOIN user_job_matches m ON j.id = m.job_id AND m.user_id = ?
                ORDER BY user_final_score DESC, j.created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            result = []
            for row in rows:
                row_dict = dict(row)
                try:
                    job_obj = json.loads(row_dict.get("raw_json")) if row_dict.get("raw_json") else {}
                except Exception:
                    job_obj = {}

                job_obj["id"] = row_dict.get("id")
                job_obj["title"] = row_dict.get("title", "")
                job_obj["company"] = row_dict.get("company", "")
                job_obj["company_domain"] = row_dict.get("company_domain")
                job_obj["company_tier"] = row_dict.get("company_tier") or "emerging"
                job_obj["location"] = row_dict.get("location", "Remote")
                job_obj["remote_type"] = row_dict.get("remote_type") or "Remote"
                job_obj["job_url"] = row_dict.get("job_url", "")
                job_obj["url"] = row_dict.get("job_url", "")
                job_obj["apply_url"] = row_dict.get("apply_url") or row_dict.get("job_url", "")
                job_obj["ats"] = row_dict.get("ats") or "custom"
                job_obj["description"] = row_dict.get("description", "")
                job_obj["match_score"] = float(row_dict.get("user_match_score") or row_dict.get("match_score") or 80.0)
                job_obj["freshness_score"] = float(row_dict.get("freshness_score") or 80.0)
                job_obj["company_score"] = float(row_dict.get("company_score") or 70.0)
                job_obj["final_score"] = float(row_dict.get("user_final_score") or row_dict.get("final_score") or 80.0)
                job_obj["posted_at"] = row_dict.get("posted_at")
                job_obj["source"] = row_dict.get("source", "ATS")
                job_obj["is_verified"] = bool(row_dict.get("is_verified", True))
                job_obj["created_at"] = row_dict.get("created_at")

                try:
                    job_obj["requirements"] = json.loads(row_dict.get("requirements")) if row_dict.get("requirements") else []
                except Exception:
                    job_obj["requirements"] = []

                try:
                    job_obj["responsibilities"] = json.loads(row_dict.get("responsibilities")) if row_dict.get("responsibilities") else []
                except Exception:
                    job_obj["responsibilities"] = []

                try:
                    why_rec_raw = row_dict.get("user_why_recommended") or row_dict.get("why_recommended")
                    job_obj["why_recommended"] = json.loads(why_rec_raw) if why_rec_raw else []
                except Exception:
                    job_obj["why_recommended"] = []

                result.append(job_obj)

            return result

    def get_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ? LIMIT 1", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            try:
                job_obj = json.loads(row["raw_json"]) if row["raw_json"] else {}
            except Exception:
                job_obj = {}
            job_obj["id"] = row["id"]
            job_obj["title"] = row["title"]
            job_obj["company"] = row["company"]
            job_obj["job_url"] = row["job_url"]
            job_obj["apply_url"] = row["apply_url"]
            return job_obj

    def get_user_jobs(self, user_id: str = "user_default", limit: int = 50, offset: int = 0) -> List[JobSchema]:
        """Fetches personalized job listings returning typed JobSchema objects."""
        raw_list = self.get_jobs(user_id=user_id, limit=limit + offset)
        sliced = raw_list[offset:offset + limit]
        return [JobSchema(**j) for j in sliced]

    def get_job_by_id(self, job_id: str) -> Optional[JobSchema]:
        raw = self.get_by_id(job_id)
        if not raw:
            return None
        return JobSchema(**raw)

    def clear_jobs(self, user_id: Optional[str] = None):
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("DELETE FROM user_job_matches WHERE user_id = ?", (user_id,))
            else:
                cursor.execute("DELETE FROM user_job_matches")
                cursor.execute("DELETE FROM jobs")
            conn.commit()

    def clear_user_jobs(self, user_id: str):
        return self.clear_jobs(user_id=user_id)


job_repo = JobRepository()
