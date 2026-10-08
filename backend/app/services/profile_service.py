# backend/app/services/profile_service.py
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Union
from app.models.profile import (
    CandidateProfile,
    PersonalInfo,
    EducationInfo,
    EducationItem,
    LinksInfo,
    ProfessionalInfo,
    ProjectItem,
    ExperienceItem,
    PreferencesInfo
)
from app.repositories.profile_repository import profile_repo


class ProfileService:
    @staticmethod
    def normalize_to_candidate_profile(data: Union[dict, CandidateProfile, None], user_id: str = "user_default") -> CandidateProfile:
        if not data:
            return CandidateProfile(user_id=user_id)

        if isinstance(data, CandidateProfile):
            return data

        if not isinstance(data, dict):
            return CandidateProfile(user_id=user_id)

        # If already nested
        if any(k in data for k in ["personal", "education", "links", "professional", "preferences"]):
            personal_data = data.get("personal", {})
            education_data = data.get("education", {})
            links_data = data.get("links", {})
            prof_data = data.get("professional", {})
            pref_data = data.get("preferences", {})

            edu_history = []
            if isinstance(education_data, dict) and "history" in education_data:
                for item in education_data.get("history", []):
                    if isinstance(item, dict):
                        edu_history.append(EducationItem(**item))

            projects_list = []
            if isinstance(prof_data, dict):
                for proj in prof_data.get("projects", []):
                    if isinstance(proj, dict):
                        projects_list.append(ProjectItem(
                            name=proj.get("name") or proj.get("title") or "",
                            title=proj.get("title") or proj.get("name") or "",
                            description=proj.get("description") or "",
                            technologies=proj.get("technologies", []) if isinstance(proj.get("technologies"), list) else [],
                            role=proj.get("role") or "",
                            url=proj.get("url") or proj.get("link") or ""
                        ))

            experience_list = []
            if isinstance(prof_data, dict):
                for exp in prof_data.get("experience", []):
                    if isinstance(exp, dict):
                        experience_list.append(ExperienceItem(
                            company=exp.get("company") or "",
                            role=exp.get("role") or exp.get("title") or "",
                            title=exp.get("title") or exp.get("role") or "",
                            duration=exp.get("duration") or "",
                            start_date=exp.get("start_date") or "",
                            end_date=exp.get("end_date") or "",
                            location=exp.get("location") or "",
                            description=exp.get("description") or ""
                        ))

            personal = PersonalInfo(**personal_data) if isinstance(personal_data, dict) else PersonalInfo()
            edu_kwargs = dict(education_data) if isinstance(education_data, dict) else {}
            edu_kwargs["history"] = edu_history
            education = EducationInfo(**{k: v for k, v in edu_kwargs.items() if k in EducationInfo.model_fields})
            links = LinksInfo(**links_data) if isinstance(links_data, dict) else LinksInfo()

            prof_kwargs = dict(prof_data) if isinstance(prof_data, dict) else {}
            prof_kwargs["projects"] = projects_list
            prof_kwargs["experience"] = experience_list
            professional = ProfessionalInfo(**{k: v for k, v in prof_kwargs.items() if k in ProfessionalInfo.model_fields})
            preferences = PreferencesInfo(**pref_data) if isinstance(pref_data, dict) else PreferencesInfo()

            return CandidateProfile(
                user_id=data.get("user_id") or user_id,
                personal=personal,
                education=education,
                links=links,
                professional=professional,
                preferences=preferences,
                application_answers=data.get("application_answers", {}) if isinstance(data.get("application_answers"), dict) else {},
                custom_fields=data.get("custom_fields", {}) if isinstance(data.get("custom_fields"), dict) else {},
                extracted_fields=data.get("extracted_fields", []) if isinstance(data.get("extracted_fields"), list) else [],
                resume_path=data.get("resume_path") or "",
                resume_filename=data.get("resume_filename") or "",
                updated_at=data.get("updated_at") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )

        # Legacy flat structure mapping
        full_name = data.get("name") or data.get("full_name") or ""
        first_name = data.get("first_name") or ""
        last_name = data.get("last_name") or ""
        if full_name and (not first_name or not last_name):
            parts = full_name.strip().split()
            if not first_name and parts: first_name = parts[0]
            if not last_name and len(parts) > 1: last_name = " ".join(parts[1:])

        skills = data.get("skills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]

        personal = PersonalInfo(
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            email=data.get("email") or "",
            phone=data.get("phone") or "",
            location=data.get("location") or "",
            city=data.get("city") or "",
            state=data.get("state") or "",
            country=data.get("country") or "",
            postal_code=data.get("postal_code") or ""
        )

        edu_val = data.get("education") or data.get("college") or ""
        education = EducationInfo(
            college_name=str(edu_val) if isinstance(edu_val, str) else "",
            degree=data.get("degree") or "",
            branch_specialization=data.get("branch") or data.get("specialization") or "",
            graduation_year=str(data.get("graduation_year") or "")
        )

        links = LinksInfo(
            portfolio_url=data.get("portfolio") or data.get("portfolio_url") or "",
            github_url=data.get("github") or data.get("github_url") or "",
            linkedin_url=data.get("linkedin") or data.get("linkedin_url") or ""
        )

        professional = ProfessionalInfo(
            key_skills=skills,
            experience_years=str(data.get("experience_years") or "0"),
            summary=data.get("summary") or ""
        )

        roles = data.get("preferred_job_roles") or data.get("target_role") or []
        if isinstance(roles, str): roles = [r.strip() for r in roles.split(",") if r.strip()]

        preferences = PreferencesInfo(
            preferred_job_roles=roles if isinstance(roles, list) else [],
            work_authorization=data.get("work_authorization") or "Authorized to work without sponsorship"
        )

        return CandidateProfile(
            user_id=user_id,
            personal=personal,
            education=education,
            links=links,
            professional=professional,
            preferences=preferences,
            custom_fields=data.get("custom_fields", {}) if isinstance(data.get("custom_fields"), dict) else {},
            application_answers=data.get("application_answers", {}) if isinstance(data.get("application_answers"), dict) else {}
        )

    @staticmethod
    def candidate_profile_to_legacy_dict(profile: CandidateProfile) -> dict:
        p = profile.personal
        e = profile.education
        l = profile.links
        pr = profile.professional
        pref = profile.preferences

        target_role = pref.preferred_job_roles[0] if pref.preferred_job_roles else ""
        target_loc = pref.preferred_locations[0] if pref.preferred_locations else p.location

        return {
            "name": p.full_name,
            "full_name": p.full_name,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "email": p.email,
            "phone": p.phone,
            "location": p.location or f"{p.city}, {p.state}".strip(", "),
            "city": p.city,
            "state": p.state,
            "country": p.country,
            "postal_code": p.postal_code,
            "college": e.college_name,
            "college_name": e.college_name,
            "education": e.degree or e.college_name,
            "degree": e.degree,
            "branch": e.branch_specialization,
            "graduation_year": e.graduation_year,
            "current_semester": e.current_semester,
            "gpa": e.gpa_percentage,
            "linkedin": l.linkedin_url,
            "github": l.github_url,
            "portfolio": l.portfolio_url,
            "skills": pr.key_skills,
            "experience_years": pr.experience_years,
            "projects": [proj.model_dump() for proj in pr.projects],
            "experience": [exp.model_dump() for exp in pr.experience],
            "achievements": pr.achievements,
            "certifications": pr.certifications,
            "target_role": target_role,
            "target_location": target_loc,
            "work_authorization": pref.work_authorization,
            "willing_to_relocate": pref.willing_to_relocate,
            "notice_period": pref.notice_period,
            "expected_salary_stipend": pref.expected_salary_stipend,
            "custom_fields": profile.custom_fields,
            "application_answers": profile.application_answers,
            "extracted_fields": profile.extracted_fields,
            "resume_path": profile.resume_path,
            "resume_filename": profile.resume_filename,
            "updated_at": profile.updated_at
        }

    @staticmethod
    def to_legacy_dict(profile: CandidateProfile) -> dict:
        return ProfileService.candidate_profile_to_legacy_dict(profile)

    @staticmethod
    def get_profile_field_value(profile: Union[dict, CandidateProfile], key: str) -> Optional[str]:
        if not profile or not key:
            return None

        norm = ProfileService.normalize_to_candidate_profile(profile)
        k = key.lower().strip().replace(" ", "_")

        if norm.custom_fields and k in norm.custom_fields:
            return str(norm.custom_fields[k])

        if norm.application_answers and k in norm.application_answers:
            return str(norm.application_answers[k])

        p = norm.personal
        e = norm.education
        l = norm.links
        pr = norm.professional
        pref = norm.preferences

        field_map = {
            "full_name": p.full_name or f"{p.first_name} {p.last_name}".strip(),
            "name": p.full_name or f"{p.first_name} {p.last_name}".strip(),
            "first_name": p.first_name,
            "last_name": p.last_name,
            "email": p.email,
            "phone": p.phone,
            "location": p.location or f"{p.city}, {p.state}".strip(", "),
            "city": p.city,
            "state": p.state,
            "country": p.country,
            "postal_code": p.postal_code,
            "address": p.address,
            "college": e.college_name,
            "college_name": e.college_name,
            "university": e.college_name,
            "degree": e.degree,
            "education": e.degree or e.college_name,
            "branch": e.branch_specialization,
            "branch_specialization": e.branch_specialization,
            "graduation_year": e.graduation_year,
            "current_semester": e.current_semester,
            "gpa": e.gpa_percentage,
            "linkedin": l.linkedin_url,
            "github": l.github_url,
            "portfolio": l.portfolio_url,
            "skills": ", ".join(pr.key_skills) if pr.key_skills else "",
            "key_skills": ", ".join(pr.key_skills) if pr.key_skills else "",
            "experience_years": pr.experience_years,
            "summary": pr.summary,
            "target_role": pref.preferred_job_roles[0] if pref.preferred_job_roles else "",
            "work_authorization": pref.work_authorization,
            "willing_to_relocate": pref.willing_to_relocate,
            "notice_period": pref.notice_period,
            "expected_salary_stipend": pref.expected_salary_stipend
        }

        if k in field_map:
            val = field_map[k]
            if isinstance(val, (list, dict)):
                return json.dumps(val, ensure_ascii=False)
            return str(val) if val is not None else ""

        return None

    @staticmethod
    def populate_from_resume(extracted: Dict[str, Any], existing: Optional[CandidateProfile] = None, user_id: str = "user_default") -> CandidateProfile:
        prof = existing.model_copy(deep=True) if existing else CandidateProfile(user_id=user_id)
        extracted_set = set(prof.extracted_fields or [])

        # Personal
        p = prof.personal
        if extracted.get("name"):
            p.full_name = extracted["name"].strip()
            extracted_set.add("personal.full_name")
            parts = p.full_name.split()
            if parts: p.first_name = parts[0]
            if len(parts) > 1: p.last_name = " ".join(parts[1:])
        if extracted.get("email"):
            p.email = extracted["email"].strip()
            extracted_set.add("personal.email")
        if extracted.get("phone"):
            p.phone = extracted["phone"].strip()
            extracted_set.add("personal.phone")
        if extracted.get("location"):
            p.location = extracted["location"].strip()
            extracted_set.add("personal.location")

        # Links
        l = prof.links
        if extracted.get("linkedin"):
            l.linkedin_url = extracted["linkedin"].strip()
            extracted_set.add("links.linkedin_url")
        if extracted.get("github"):
            l.github_url = extracted["github"].strip()
            extracted_set.add("links.github_url")
        if extracted.get("portfolio"):
            l.portfolio_url = extracted["portfolio"].strip()
            extracted_set.add("links.portfolio_url")

        # Education
        e = prof.education
        if extracted.get("college_name"):
            e.college_name = extracted["college_name"]
            extracted_set.add("education.college_name")
        if extracted.get("degree"):
            e.degree = extracted["degree"]
            extracted_set.add("education.degree")
        if extracted.get("branch_specialization"):
            e.branch_specialization = extracted["branch_specialization"]
            extracted_set.add("education.branch_specialization")
        if extracted.get("graduation_year"):
            e.graduation_year = str(extracted["graduation_year"])
            extracted_set.add("education.graduation_year")

        # Skills & Projects
        pr = prof.professional
        if extracted.get("skills"):
            s_list = extracted["skills"] if isinstance(extracted["skills"], list) else [s.strip() for s in extracted["skills"].split(",")]
            pr.key_skills = [s for s in s_list if s]
            extracted_set.add("professional.key_skills")

        if extracted.get("projects") and isinstance(extracted["projects"], list):
            projects = []
            for item in extracted["projects"]:
                if isinstance(item, dict):
                    projects.append(ProjectItem(
                        name=item.get("name") or item.get("title") or "Project",
                        description=item.get("description") or "",
                        technologies=item.get("technologies", []) if isinstance(item.get("technologies"), list) else [],
                        url=item.get("url") or ""
                    ))
            pr.projects = projects
            extracted_set.add("professional.projects")

        prof.extracted_fields = sorted(list(extracted_set))
        prof.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return prof

    def __init__(self, repo=None):
        self.repo = repo or profile_repo

    def get_candidate_profile(self, user_id: str = "user_default") -> Tuple[Optional[CandidateProfile], Optional[str], Optional[str]]:
        raw_dict, resume_path, resume_filename = self.repo.get_by_user_id(user_id=user_id) if hasattr(self.repo, 'get_by_user_id') else (self.repo.get_profile(user_id).model_dump() if hasattr(self.repo, 'get_profile') else ({}, None, None))
        if not raw_dict:
            return None, None, None
        profile = self.normalize_to_candidate_profile(raw_dict, user_id=user_id)
        profile.resume_path = resume_path or profile.resume_path
        profile.resume_filename = resume_filename or profile.resume_filename
        return profile, resume_path, resume_filename

    def get_profile(self, user_id: str = "user_default") -> CandidateProfile:
        prof, _, _ = self.get_candidate_profile(user_id)
        return prof or CandidateProfile(user_id=user_id)

    def update_profile(self, user_id: str, profile_data: Union[dict, CandidateProfile]) -> CandidateProfile:
        return self.save_candidate_profile(profile_data, user_id=user_id)

    def save_candidate_profile(self, profile_data: Union[dict, CandidateProfile], user_id: str = "user_default", resume_path: str = "", resume_filename: str = "") -> CandidateProfile:
        norm = self.normalize_to_candidate_profile(profile_data, user_id=user_id)
        if resume_path: norm.resume_path = resume_path
        if resume_filename: norm.resume_filename = resume_filename
        norm.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self.repo, 'save_profile'):
            try:
                self.repo.save_profile(norm.model_dump(), user_id=user_id, resume_path=norm.resume_path or "", resume_filename=norm.resume_filename or "")
            except TypeError:
                self.repo.save_profile(norm)
        return norm


profile_service = ProfileService()
