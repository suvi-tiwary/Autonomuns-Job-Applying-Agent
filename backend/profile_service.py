import json
import re
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
from models import (
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
import db


def normalize_to_candidate_profile(data: Union[dict, CandidateProfile, None]) -> CandidateProfile:
    """
    Converts any dict (whether legacy flat structure, partial, or nested CandidateProfile)
    into a fully typed CandidateProfile object.
    """
    if not data:
        return CandidateProfile()

    if isinstance(data, CandidateProfile):
        return data

    if not isinstance(data, dict):
        return CandidateProfile()

    # Check if already structured with nested sections
    if any(k in data for k in ["personal", "education", "links", "professional", "preferences"]):
        personal_data = data.get("personal", {})
        education_data = data.get("education", {})
        links_data = data.get("links", {})
        prof_data = data.get("professional", {})
        pref_data = data.get("preferences", {})

        # Handle education history items
        edu_history = []
        if isinstance(education_data, dict) and "history" in education_data:
            for item in education_data.get("history", []):
                if isinstance(item, dict):
                    edu_history.append(EducationItem(**item))
                elif isinstance(item, str):
                    edu_history.append(EducationItem(degree=item))

        # Handle projects
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
                elif isinstance(proj, str):
                    projects_list.append(ProjectItem(name=proj, title=proj, description=""))

        # Handle experience
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
                elif isinstance(exp, str):
                    experience_list.append(ExperienceItem(company=exp, role="", description=""))

        # Build candidate profile
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

    # Convert legacy flat format
    full_name = data.get("name") or data.get("full_name") or ""
    first_name = data.get("first_name") or ""
    last_name = data.get("last_name") or ""
    if full_name and (not first_name or not last_name):
        parts = full_name.strip().split()
        if not first_name and parts:
            first_name = parts[0]
        if not last_name and len(parts) > 1:
            last_name = " ".join(parts[1:])

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
        postal_code=data.get("postal_code") or "",
        address=data.get("address") or ""
    )

    edu_val = data.get("education") or data.get("college") or ""
    education = EducationInfo(
        college_name=str(edu_val) if isinstance(edu_val, str) else "",
        degree=data.get("degree") or "",
        branch_specialization=data.get("branch") or data.get("specialization") or "",
        graduation_year=str(data.get("graduation_year") or ""),
        current_semester=str(data.get("current_semester") or ""),
        gpa_percentage=str(data.get("gpa") or data.get("gpa_percentage") or "")
    )

    links = LinksInfo(
        portfolio_url=data.get("portfolio") or data.get("portfolio_url") or "",
        github_url=data.get("github") or data.get("github_url") or "",
        linkedin_url=data.get("linkedin") or data.get("linkedin_url") or "",
        twitter_url=data.get("twitter") or data.get("twitter_url") or ""
    )

    # Process projects
    raw_projects = data.get("projects", [])
    projects_list = []
    if isinstance(raw_projects, list):
        for p in raw_projects:
            if isinstance(p, dict):
                projects_list.append(ProjectItem(
                    name=p.get("name") or p.get("title") or "",
                    title=p.get("title") or p.get("name") or "",
                    description=p.get("description") or "",
                    technologies=p.get("technologies", []) if isinstance(p.get("technologies"), list) else [],
                    role=p.get("role") or "",
                    url=p.get("url") or ""
                ))
            elif isinstance(p, str):
                projects_list.append(ProjectItem(name=p, title=p, description=""))

    # Process experience
    raw_exp = data.get("experience", [])
    exp_list = []
    if isinstance(raw_exp, list):
        for e in raw_exp:
            if isinstance(e, dict):
                exp_list.append(ExperienceItem(
                    company=e.get("company") or "",
                    role=e.get("role") or e.get("title") or "",
                    title=e.get("title") or e.get("role") or "",
                    duration=e.get("duration") or "",
                    description=e.get("description") or ""
                ))
            elif isinstance(e, str):
                exp_list.append(ExperienceItem(company=e, role="", description=""))

    achievements = data.get("achievements", [])
    if isinstance(achievements, str):
        achievements = [a.strip() for a in achievements.split(",") if a.strip()]

    certifications = data.get("certifications", [])
    if isinstance(certifications, str):
        certifications = [c.strip() for c in certifications.split(",") if c.strip()]

    professional = ProfessionalInfo(
        key_skills=skills,
        experience_years=str(data.get("experience_years") or data.get("years_of_experience") or "0"),
        summary=data.get("summary") or "",
        projects=projects_list,
        experience=exp_list,
        achievements=achievements if isinstance(achievements, list) else [],
        certifications=certifications if isinstance(certifications, list) else []
    )

    roles = data.get("preferred_job_roles") or data.get("target_role") or []
    if isinstance(roles, str):
        roles = [r.strip() for r in roles.split(",") if r.strip()]

    locations = data.get("preferred_locations") or data.get("target_location") or []
    if isinstance(locations, str):
        locations = [l.strip() for l in locations.split(",") if l.strip()]

    preferences = PreferencesInfo(
        preferred_job_roles=roles if isinstance(roles, list) else [],
        preferred_locations=locations if isinstance(locations, list) else [],
        remote_preference=data.get("remote_preference") or "Remote",
        work_authorization=data.get("work_authorization") or "Authorized to work without sponsorship",
        willing_to_relocate=str(data.get("willing_to_relocate") or "Yes"),
        notice_period=str(data.get("notice_period") or "Immediate"),
        expected_salary_stipend=str(data.get("expected_salary_stipend") or data.get("salary") or "")
    )

    return CandidateProfile(
        personal=personal,
        education=education,
        links=links,
        professional=professional,
        preferences=preferences,
        custom_fields=data.get("custom_fields", {}) if isinstance(data.get("custom_fields"), dict) else {},
        application_answers=data.get("application_answers", {}) if isinstance(data.get("application_answers"), dict) else {},
        extracted_fields=data.get("extracted_fields", []) if isinstance(data.get("extracted_fields"), list) else [],
        resume_path=data.get("resume_path") or "",
        resume_filename=data.get("resume_filename") or ""
    )


def candidate_profile_to_legacy_dict(profile: CandidateProfile) -> dict:
    """
    Exports CandidateProfile as flat dictionary for backward-compatible consumption.
    """
    p = profile.personal
    e = profile.education
    l = profile.links
    pr = profile.professional
    pref = profile.preferences

    skills = pr.key_skills
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
        "address": p.address,
        "college": e.college_name,
        "college_name": e.college_name,
        "education": e.degree or e.college_name,
        "degree": e.degree,
        "branch": e.branch_specialization,
        "branch_specialization": e.branch_specialization,
        "graduation_year": e.graduation_year,
        "current_semester": e.current_semester,
        "gpa": e.gpa_percentage,
        "linkedin": l.linkedin_url,
        "github": l.github_url,
        "portfolio": l.portfolio_url,
        "twitter": l.twitter_url,
        "skills": skills,
        "experience_years": pr.experience_years,
        "projects": [p.model_dump() for p in pr.projects],
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


def get_profile_field_value(profile: Union[dict, CandidateProfile], key: str) -> Optional[str]:
    """
    Dynamic field resolver that retrieves value for any standard or custom profile key.
    """
    if not profile or not key:
        return None

    norm_profile = normalize_to_candidate_profile(profile)
    k = key.lower().strip().replace(" ", "_")

    # 1. Check custom fields
    if norm_profile.custom_fields and k in norm_profile.custom_fields:
        val = norm_profile.custom_fields[k]
        return str(val) if val is not None else ""

    # 2. Check application answers
    if norm_profile.application_answers and k in norm_profile.application_answers:
        val = norm_profile.application_answers[k]
        return str(val) if val is not None else ""

    p = norm_profile.personal
    e = norm_profile.education
    l = norm_profile.links
    pr = norm_profile.professional
    pref = norm_profile.preferences

    field_map: Dict[str, Any] = {
        "full_name": p.full_name or f"{p.first_name} {p.last_name}".strip(),
        "name": p.full_name or f"{p.first_name} {p.last_name}".strip(),
        "first_name": p.first_name,
        "last_name": p.last_name,
        "email": p.email,
        "phone": p.phone,
        "mobile": p.phone,
        "tel": p.phone,
        "location": p.location or f"{p.city}, {p.state}".strip(", "),
        "city": p.city,
        "state": p.state,
        "country": p.country,
        "postal_code": p.postal_code,
        "zip": p.postal_code,
        "zipcode": p.postal_code,
        "pincode": p.postal_code,
        "address": p.address,
        "college": e.college_name,
        "college_name": e.college_name,
        "university": e.college_name,
        "institution": e.college_name,
        "school": e.college_name,
        "degree": e.degree,
        "education": e.degree or e.college_name,
        "branch": e.branch_specialization,
        "branch_specialization": e.branch_specialization,
        "specialization": e.branch_specialization,
        "major": e.branch_specialization,
        "discipline": e.branch_specialization,
        "graduation_year": e.graduation_year,
        "grad_year": e.graduation_year,
        "current_semester": e.current_semester,
        "semester": e.current_semester,
        "gpa": e.gpa_percentage,
        "gpa_percentage": e.gpa_percentage,
        "linkedin": l.linkedin_url,
        "github": l.github_url,
        "portfolio": l.portfolio_url,
        "website": l.portfolio_url,
        "twitter": l.twitter_url,
        "skills": ", ".join(pr.key_skills) if pr.key_skills else "",
        "key_skills": ", ".join(pr.key_skills) if pr.key_skills else "",
        "experience_years": pr.experience_years,
        "years_of_experience": pr.experience_years,
        "yoe": pr.experience_years,
        "summary": pr.summary,
        "target_role": pref.preferred_job_roles[0] if pref.preferred_job_roles else "",
        "preferred_job_roles": ", ".join(pref.preferred_job_roles) if pref.preferred_job_roles else "",
        "preferred_locations": ", ".join(pref.preferred_locations) if pref.preferred_locations else "",
        "target_location": pref.preferred_locations[0] if pref.preferred_locations else p.location,
        "work_authorization": pref.work_authorization,
        "authorized_to_work": pref.work_authorization,
        "sponsorship": pref.work_authorization,
        "willing_to_relocate": pref.willing_to_relocate,
        "relocate": pref.willing_to_relocate,
        "notice_period": pref.notice_period,
        "availability": pref.notice_period,
        "expected_salary": pref.expected_salary_stipend,
        "expected_salary_stipend": pref.expected_salary_stipend,
        "salary": pref.expected_salary_stipend,
        "stipend": pref.expected_salary_stipend,
    }

    if k in field_map:
        val = field_map[k]
        if isinstance(val, (list, dict)):
            return json.dumps(val, ensure_ascii=False)
        return str(val) if val is not None else ""

    return None


def populate_from_resume_extraction(
    extracted_data: dict,
    existing_profile: Optional[CandidateProfile] = None
) -> CandidateProfile:
    """
    Merges resume extraction into CandidateProfile while recording extracted fields.
    Preserves existing user customizations where applicable.
    """
    profile = existing_profile.model_copy(deep=True) if existing_profile else CandidateProfile()
    extracted_fields = set(profile.extracted_fields or [])

    # Personal Info
    p = profile.personal
    if extracted_data.get("name"):
        p.full_name = extracted_data["name"].strip()
        extracted_fields.add("personal.full_name")
        parts = p.full_name.split()
        if parts:
            p.first_name = parts[0]
            extracted_fields.add("personal.first_name")
            if len(parts) > 1:
                p.last_name = " ".join(parts[1:])
                extracted_fields.add("personal.last_name")

    if extracted_data.get("email"):
        p.email = extracted_data["email"].strip()
        extracted_fields.add("personal.email")

    if extracted_data.get("phone"):
        p.phone = extracted_data["phone"].strip()
        extracted_fields.add("personal.phone")

    if extracted_data.get("location"):
        p.location = extracted_data["location"].strip()
        extracted_fields.add("personal.location")

    if extracted_data.get("city"):
        p.city = extracted_data["city"].strip()
        extracted_fields.add("personal.city")

    if extracted_data.get("state"):
        p.state = extracted_data["state"].strip()
        extracted_fields.add("personal.state")

    if extracted_data.get("country"):
        p.country = extracted_data["country"].strip()
        extracted_fields.add("personal.country")

    if extracted_data.get("postal_code"):
        p.postal_code = extracted_data["postal_code"].strip()
        extracted_fields.add("personal.postal_code")

    # Links
    l = profile.links
    if extracted_data.get("linkedin"):
        l.linkedin_url = extracted_data["linkedin"].strip()
        extracted_fields.add("links.linkedin_url")

    if extracted_data.get("github"):
        l.github_url = extracted_data["github"].strip()
        extracted_fields.add("links.github_url")

    if extracted_data.get("portfolio"):
        l.portfolio_url = extracted_data["portfolio"].strip()
        extracted_fields.add("links.portfolio_url")

    if extracted_data.get("twitter"):
        l.twitter_url = extracted_data["twitter"].strip()
        extracted_fields.add("links.twitter_url")

    # Education
    e = profile.education
    raw_edu = extracted_data.get("education", [])
    if isinstance(raw_edu, list) and raw_edu:
        first_edu = raw_edu[0]
        if isinstance(first_edu, dict):
            if first_edu.get("institution") or first_edu.get("college") or first_edu.get("university"):
                e.college_name = first_edu.get("institution") or first_edu.get("college") or first_edu.get("university") or ""
                extracted_fields.add("education.college_name")
            if first_edu.get("degree"):
                e.degree = first_edu.get("degree") or ""
                extracted_fields.add("education.degree")
            if first_edu.get("branch") or first_edu.get("field_of_study") or first_edu.get("major"):
                e.branch_specialization = first_edu.get("branch") or first_edu.get("field_of_study") or first_edu.get("major") or ""
                extracted_fields.add("education.branch_specialization")
            if first_edu.get("graduation_year") or first_edu.get("year"):
                e.graduation_year = str(first_edu.get("graduation_year") or first_edu.get("year") or "")
                extracted_fields.add("education.graduation_year")
            if first_edu.get("current_semester") or first_edu.get("semester"):
                e.current_semester = str(first_edu.get("current_semester") or first_edu.get("semester") or "")
                extracted_fields.add("education.current_semester")
            if first_edu.get("gpa") or first_edu.get("cgpa") or first_edu.get("percentage"):
                e.gpa_percentage = str(first_edu.get("gpa") or first_edu.get("cgpa") or first_edu.get("percentage") or "")
                extracted_fields.add("education.gpa_percentage")

            # Store full history
            edu_history = []
            for item in raw_edu:
                if isinstance(item, dict):
                    edu_history.append(EducationItem(
                        institution=item.get("institution") or item.get("college") or "",
                        degree=item.get("degree") or "",
                        branch=item.get("branch") or item.get("field_of_study") or "",
                        graduation_year=str(item.get("graduation_year") or item.get("year") or ""),
                        current_semester=str(item.get("current_semester") or ""),
                        gpa_percentage=str(item.get("gpa") or item.get("cgpa") or "")
                    ))
            e.history = edu_history
        elif isinstance(first_edu, str):
            e.college_name = first_edu
            extracted_fields.add("education.college_name")
    elif isinstance(raw_edu, str) and raw_edu:
        e.college_name = raw_edu
        extracted_fields.add("education.college_name")

    if extracted_data.get("college_name"):
        e.college_name = extracted_data["college_name"]
        extracted_fields.add("education.college_name")
    if extracted_data.get("degree"):
        e.degree = extracted_data["degree"]
        extracted_fields.add("education.degree")
    if extracted_data.get("branch_specialization"):
        e.branch_specialization = extracted_data["branch_specialization"]
        extracted_fields.add("education.branch_specialization")
    if extracted_data.get("graduation_year"):
        e.graduation_year = str(extracted_data["graduation_year"])
        extracted_fields.add("education.graduation_year")

    # Professional
    pr = profile.professional
    if extracted_data.get("skills"):
        skills = extracted_data["skills"]
        if isinstance(skills, list):
            pr.key_skills = [str(s).strip() for s in skills if s]
            extracted_fields.add("professional.key_skills")
        elif isinstance(skills, str):
            pr.key_skills = [s.strip() for s in skills.split(",") if s.strip()]
            extracted_fields.add("professional.key_skills")

    if extracted_data.get("years_of_experience") is not None:
        pr.experience_years = str(extracted_data["years_of_experience"])
        extracted_fields.add("professional.experience_years")
    elif extracted_data.get("experience_years"):
        pr.experience_years = str(extracted_data["experience_years"])
        extracted_fields.add("professional.experience_years")

    if extracted_data.get("summary"):
        pr.summary = extracted_data["summary"].strip()
        extracted_fields.add("professional.summary")

    # Projects
    raw_projects = extracted_data.get("projects", [])
    if isinstance(raw_projects, list) and raw_projects:
        projects = []
        for p_item in raw_projects:
            if isinstance(p_item, dict):
                projects.append(ProjectItem(
                    name=p_item.get("name") or p_item.get("title") or "Project",
                    title=p_item.get("title") or p_item.get("name") or "Project",
                    description=p_item.get("description") or "",
                    technologies=p_item.get("technologies", []) if isinstance(p_item.get("technologies"), list) else [],
                    role=p_item.get("role") or "",
                    url=p_item.get("url") or p_item.get("link") or ""
                ))
            elif isinstance(p_item, str):
                projects.append(ProjectItem(name=p_item, title=p_item, description=""))
        pr.projects = projects
        extracted_fields.add("professional.projects")

    # Experience
    raw_exp = extracted_data.get("experience", [])
    if isinstance(raw_exp, list) and raw_exp:
        experiences = []
        for exp_item in raw_exp:
            if isinstance(exp_item, dict):
                experiences.append(ExperienceItem(
                    company=exp_item.get("company") or "Company",
                    role=exp_item.get("role") or exp_item.get("title") or "Role",
                    title=exp_item.get("title") or exp_item.get("role") or "Role",
                    duration=exp_item.get("duration") or "",
                    start_date=exp_item.get("start_date") or "",
                    end_date=exp_item.get("end_date") or "",
                    location=exp_item.get("location") or "",
                    description=exp_item.get("description") or ""
                ))
            elif isinstance(exp_item, str):
                experiences.append(ExperienceItem(company=exp_item, role="", description=""))
        pr.experience = experiences
        extracted_fields.add("professional.experience")

    # Achievements & Certifications
    if extracted_data.get("achievements"):
        ach = extracted_data["achievements"]
        pr.achievements = ach if isinstance(ach, list) else [str(ach)]
        extracted_fields.add("professional.achievements")

    if extracted_data.get("certifications"):
        cert = extracted_data["certifications"]
        pr.certifications = cert if isinstance(cert, list) else [str(cert)]
        extracted_fields.add("professional.certifications")

    # Preferences defaults if not set
    pref = profile.preferences
    if extracted_data.get("target_role"):
        pref.preferred_job_roles = [extracted_data["target_role"]]
    if extracted_data.get("target_location"):
        pref.preferred_locations = [extracted_data["target_location"]]

    profile.extracted_fields = sorted(list(extracted_fields))
    profile.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    return profile


def save_candidate_profile_to_db(
    profile: Union[dict, CandidateProfile],
    resume_path: str = "",
    resume_filename: str = ""
) -> CandidateProfile:
    """
    Persists CandidateProfile to SQLite DB and returns normalized object.
    """
    norm_profile = normalize_to_candidate_profile(profile)
    if resume_path:
        norm_profile.resume_path = resume_path
    if resume_filename:
        norm_profile.resume_filename = resume_filename

    norm_profile.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    profile_dict = norm_profile.model_dump()

    # Save via db module
    db.save_profile(
        profile_data=profile_dict,
        resume_path=norm_profile.resume_path or "",
        resume_filename=norm_profile.resume_filename or ""
    )

    return norm_profile


def get_active_candidate_profile_from_db() -> Tuple[Optional[CandidateProfile], Optional[str], Optional[str]]:
    """
    Fetches active CandidateProfile from DB.
    """
    raw_profile, resume_path, resume_filename = db.get_active_profile()
    if not raw_profile:
        return None, None, None

    candidate_profile = normalize_to_candidate_profile(raw_profile)
    candidate_profile.resume_path = resume_path or candidate_profile.resume_path
    candidate_profile.resume_filename = resume_filename or candidate_profile.resume_filename

    return candidate_profile, resume_path, resume_filename
