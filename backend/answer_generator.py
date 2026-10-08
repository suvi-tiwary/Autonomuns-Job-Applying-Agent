import json
from typing import Dict, Any, Optional
from models import CandidateProfile, QuestionCategory
from profile_service import normalize_to_candidate_profile
from job_context_service import format_job_summary_for_prompt
from llm_provider import get_llm_provider
from answer_validator import validate_and_refine_answer


def build_candidate_prompt_context(candidate: CandidateProfile) -> str:
    """
    Builds a structured facts summary of candidate without bloating prompt tokens.
    """
    p = candidate.personal
    e = candidate.education
    pr = candidate.professional
    pref = candidate.preferences

    lines = [
        f"NAME: {p.full_name}",
        f"EMAIL: {p.email}",
        f"LOCATION: {p.location or p.city}",
        f"EDUCATION: {e.degree} in {e.branch_specialization} from {e.college_name} (Graduation: {e.graduation_year or 'Recent'})",
        f"GPA/MARKS: {e.gpa_percentage or 'N/A'}",
        f"KEY SKILLS: {', '.join(pr.key_skills)}",
        f"YEARS OF EXPERIENCE: {pr.experience_years}"
    ]

    if pr.summary:
        lines.append(f"PROFESSIONAL SUMMARY: {pr.summary}")

    if pr.projects:
        lines.append("REAL PROJECTS:")
        for proj in pr.projects[:4]:
            tech_str = ", ".join(proj.technologies) if proj.technologies else ""
            desc = proj.description or ""
            lines.append(f"- {proj.name or proj.title}: {desc} (Technologies: {tech_str})")

    if pr.experience:
        lines.append("WORK / INTERNSHIP EXPERIENCE:")
        for exp in pr.experience[:3]:
            lines.append(f"- {exp.company} - {exp.role or exp.title} ({exp.duration}): {exp.description}")

    if pr.achievements:
        lines.append(f"ACHIEVEMENTS: {'; '.join(pr.achievements[:4])}")

    if pr.certifications:
        lines.append(f"CERTIFICATIONS: {'; '.join(pr.certifications[:4])}")

    if pref.work_authorization:
        lines.append(f"WORK AUTHORIZATION: {pref.work_authorization}")

    return "\n".join(lines)


def generate_application_answer(
    question: str,
    candidate_profile: Any,
    job_context: Dict[str, Any],
    question_category: QuestionCategory = QuestionCategory.DESCRIPTIVE,
    field_context: Optional[Dict[str, Any]] = None,
    default_max_words: int = 150
) -> str:
    """
    Intelligent LLM Question Agent that generates truthful, role-relevant answers.
    Adheres strictly to anti-hallucination rules.
    """
    norm_candidate = normalize_to_candidate_profile(candidate_profile)
    candidate_summary = build_candidate_prompt_context(norm_candidate)
    job_summary = format_job_summary_for_prompt(job_context)

    company_name = job_context.get("company") or "the company"
    job_title = job_context.get("title") or "this role"

    max_words = field_context.get("max_words") if field_context else default_max_words
    max_words = max_words or default_max_words

    # Custom category guidance
    category_guidance = ""
    if question_category == QuestionCategory.COVER_LETTER:
        category_guidance = f"""
- Write a professional, tailored Cover Letter for {job_title} at {company_name}.
- Highlight candidate's specific relevant projects and skills that match the job requirements.
- Structure with a strong opening, relevant project highlights, alignment with {company_name}, and a confident closing.
- Length: approximately 180-250 words.
"""
    elif question_category == QuestionCategory.PROJECT_DESCRIPTION:
        category_guidance = f"""
- Describe the candidate's most impressive and relevant project from the CANDIDATE FACTS.
- Detail the problem solved, architecture/technologies used, and practical outcome.
- Keep it concrete and technical.
"""
    elif question_category == QuestionCategory.WHY_COMPANY:
        category_guidance = f"""
- Connect the candidate's actual projects/skills to {company_name}'s mission, technical domain, and product.
- Be genuine and specific. Avoid empty generic flattery.
"""
    elif question_category == QuestionCategory.WHY_ROLE:
        category_guidance = f"""
- Clearly explain how the candidate's real coursework, projects, and skills make them an immediate contributor for {job_title}.
"""
    elif question_category == QuestionCategory.ACHIEVEMENT:
        category_guidance = f"""
- Highlight the candidate's genuine achievements, hackathons, or project milestones from the CANDIDATE FACTS.
"""

    prompt = f"""
You are an expert AI job application assistant. Write a high-impact, natural, and completely TRUTHFUL answer to the application question below.

CRITICAL ANTI-HALLUCINATION RULES:
1. NEVER invent companies, internships, projects, technologies, achievements, degrees, or certifications.
2. Use ONLY facts provided in CANDIDATE FACTS.
3. If the candidate has not worked at a specific company or role, focus on their actual projects, skills, and coursework.
4. Do NOT mention that you are an AI or an assistant. Write directly in first-person as the candidate.
5. Directly answer the question in a confident, professional, and natural tone.
6. Target length: Under {max_words} words.

CANDIDATE FACTS:
{candidate_summary}

TARGET JOB DETAILS:
{job_summary}

APPLICATION QUESTION:
"{question}"

CATEGORY GUIDELINES:
{category_guidance}

Return ONLY the exact answer text to be placed into the form field.
"""

    llm = get_llm_provider()
    raw_answer = ""

    try:
        if llm.is_configured():
            raw_answer = llm.generate(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional candidate filling an application form. Write completely truthful answers based strictly on candidate facts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=600
            )
    except Exception as e:
        print(f"[AnswerGenerator] LLM generation error: {e}")

    # Fallback to truthful rule-based compilation if LLM failed
    if not raw_answer:
        raw_answer = _build_fallback_answer(question, norm_candidate, job_context, question_category)

    # Validate, refine and enforce character/word limits
    final_answer = validate_and_refine_answer(
        raw_answer,
        field_context=field_context,
        default_max_words=max_words
    )

    return final_answer


def _build_fallback_answer(
    question: str,
    candidate: CandidateProfile,
    job: Dict[str, Any],
    category: QuestionCategory
) -> str:
    """
    Deterministic truthful fallback answer if LLM network call fails.
    """
    p = candidate.personal
    e = candidate.education
    pr = candidate.professional
    skills_str = ", ".join(pr.key_skills[:6]) if pr.key_skills else "software engineering and modern technologies"
    company = job.get("company", "your team")
    role = job.get("title", "this position")

    if category == QuestionCategory.PROJECT_DESCRIPTION and pr.projects:
        proj = pr.projects[0]
        tech = ", ".join(proj.technologies) if proj.technologies else "modern frameworks"
        return f"One of my notable projects is {proj.name or proj.title}. {proj.description or 'I developed this application to solve real-world problems.'} It was built using {tech}, emphasizing scalable architecture and clean code."

    if category == QuestionCategory.WHY_COMPANY:
        return f"I am excited to apply to {company} because of your impactful work and technical focus. With my background in {skills_str} and hands-on project experience, I look forward to contributing effectively to your engineering team."

    if category == QuestionCategory.WHY_ROLE:
        return f"I believe I am a strong fit for the {role} at {company} because of my strong foundation in {skills_str}. My hands-on projects have prepared me to learn quickly, collaborate, and deliver high quality results."

    if category == QuestionCategory.COVER_LETTER:
        return f"Dear Hiring Team at {company},\n\nI am writing to express my enthusiastic interest in the {role} position. With a background in {e.degree or 'Computer Science'} from {e.college_name} and hands-on experience with {skills_str}, I have built projects focusing on performance, clean code, and practical problem-solving. I would be thrilled to bring my dedication and skills to {company}.\n\nSincerely,\n{p.full_name}"

    if pr.summary:
        return pr.summary

    return f"With my background in {e.degree or 'technology'} and strong foundation in {skills_str}, I focus on building reliable, scalable software solutions."
