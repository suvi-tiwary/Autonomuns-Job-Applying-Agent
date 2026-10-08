# backend/app/services/job_ranking_service.py
from typing import List, Dict, Any, Tuple, Optional
from app.services.company_intelligence_service import company_intel
from app.models.job import JobSchema, CompanyTier


class JobRankingService:
    @staticmethod
    def calculate_scores_and_reasons(job: Dict[str, Any], profile: Dict[str, Any]) -> Tuple[float, float, float, float, float, List[str]]:
        """
        Calculates multi-factor scores and human-readable recommendation reasons:
        Returns: (match_score, freshness_score, company_score, role_match_score, final_score, why_recommended)
        """
        # 1. Candidate Skills
        skills = profile.get("skills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        candidate_skills_lower = [s.lower() for s in skills]

        job_text = " ".join([
            job.get("title", ""),
            job.get("company", ""),
            job.get("description", ""),
            " ".join(job.get("requirements", [])),
            " ".join(job.get("skills", []))
        ]).lower()

        # Skill match
        matched_skills = []
        for s in candidate_skills_lower:
            if s in job_text:
                matched_skills.append(s.title())

        total_checked = max(min(len(candidate_skills_lower), 8), 1)
        skill_ratio = min(len(matched_skills) / total_checked, 1.0)
        resume_skill_match = round(70.0 + (skill_ratio * 26.0), 1)

        # Role match
        target_role = (profile.get("target_role") or "").lower().strip()
        job_title_lower = (job.get("title") or "").lower()
        if target_role and any(w in job_title_lower for w in target_role.split()):
            role_match_score = 95.0
        else:
            role_match_score = 80.0

        # Freshness score
        freshness_score = float(job.get("freshness_score", 85.0) or 85.0)

        # Company intelligence score & tier
        company_name = job.get("company", "")
        tier, company_score = company_intel.classify_company(company_name)

        # Final weighted composite score
        # 35% Resume Skill Match, 25% Freshness, 25% Company Signal, 15% Role Match
        final_score = round(
            (resume_skill_match * 0.35) +
            (freshness_score * 0.25) +
            (company_score * 0.25) +
            (role_match_score * 0.15),
            1
        )
        final_score = min(final_score, 98.5)

        # Build transparent recommendation reasons
        reasons: List[str] = []
        if matched_skills:
            reasons.append(f"Matching skills: {', '.join(matched_skills[:4])}")

        if tier == CompanyTier.RECOGNIZABLE:
            reasons.append(f"Recognized tier-1 tech leader ({company_name})")
        elif tier == CompanyTier.STRONG_STARTUP:
            reasons.append(f"High-growth venture startup ({company_name})")
        else:
            reasons.append("Emerging opportunity with targeted tech stack")

        if freshness_score >= 90:
            reasons.append("Very fresh posting (last 48 hours)")
        elif freshness_score >= 80:
            reasons.append("Recently posted opening")

        target_loc = profile.get("target_location") or ""
        job_loc = job.get("location") or "Remote"
        if "remote" in job_loc.lower():
            reasons.append("Remote / Global flexibility")
        elif target_loc and target_loc.lower() in job_loc.lower():
            reasons.append(f"Location match ({job_loc})")

        return resume_skill_match, freshness_score, company_score, role_match_score, final_score, reasons

    def rank_job(self, job: Any, profile: Any) -> JobSchema:
        """Ranks and enriches a single job against candidate profile."""
        from app.models.profile import CandidateProfile
        from app.services.profile_service import ProfileService

        job_dict = job.model_dump() if hasattr(job, "model_dump") else dict(job)
        if isinstance(profile, CandidateProfile):
            prof_dict = ProfileService.to_legacy_dict(profile)
        elif hasattr(profile, "model_dump"):
            prof_dict = profile.model_dump()
        else:
            prof_dict = dict(profile)

        tier, comp_score = company_intel.classify_company(job_dict.get("company", ""))
        job_dict["company_tier"] = tier.value if hasattr(tier, "value") else str(tier)

        match_score, freshness_score, company_score, role_match, final_score, reasons = self.calculate_scores_and_reasons(job_dict, prof_dict)
        job_dict["match_score"] = match_score
        job_dict["freshness_score"] = freshness_score
        job_dict["company_score"] = company_score
        job_dict["final_score"] = final_score
        job_dict["why_recommended"] = reasons

        return JobSchema(**job_dict)

    def rank_and_enrich_jobs(self, jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not jobs:
            return []

        ranked: List[Dict[str, Any]] = []
        for j in jobs:
            job_copy = dict(j)
            tier, comp_score = company_intel.classify_company(job_copy.get("company", ""))
            job_copy["company_tier"] = tier.value if hasattr(tier, "value") else str(tier)

            match_score, freshness_score, company_score, role_match, final_score, reasons = self.calculate_scores_and_reasons(job_copy, profile)
            job_copy["match_score"] = match_score
            job_copy["freshness_score"] = freshness_score
            job_copy["company_score"] = company_score
            job_copy["final_score"] = final_score
            job_copy["why_recommended"] = reasons
            ranked.append(job_copy)

        # Sort by final_score descending
        ranked.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        return ranked


job_ranking_service = JobRankingService()
