"""
Question Agent - Intelligent AI Application Question Answering
Generates accurate, concise, and truthful answers for job application questions.
Leverages the candidate profile, LLM provider, answer cache, and answer validator.
"""

from typing import Dict, Any, Optional, Tuple
from app.core.logging import get_logger
from app.models.profile import CandidateProfile
from app.models.application import QuestionCategory
from app.services.answer_service import AnswerService
from app.agents.answer_validator import AnswerValidator
from app.integrations.llm.provider import LLMProvider, get_llm_provider

logger = get_logger(__name__)


SYSTEM_PROMPT = """You are an intelligent, truthful AI assistant completing job application form fields for a candidate.
Your goal is to answer the specific application question accurately based ONLY on the candidate's verified profile data.

CRITICAL RULES:
1. GROUND TRUTH ONLY: Never fabricate, hallucinate, or exaggerate qualifications, experience, degrees, or skills.
2. CONCISENESS: Output ONLY the direct answer text. Do NOT add conversational preamble (e.g., "Sure, here is the answer:", "Based on my background...").
3. FORMAT MATCHING:
   - For numeric fields (Years of experience, GPA), return ONLY the number or standard format.
   - For Yes/No or Radio questions, return strictly "Yes", "No", or the exact matching choice.
   - For open-ended questions (Why this company, Cover letter snippet, Project description), write a polished, professional 2-4 sentence response tailored to the job and company using the candidate's actual projects.
4. STRICT LENGTH LIMITS: If a character or word limit is specified, your answer MUST be within that limit.
"""


class QuestionAgent:
    """
    Orchestrates question understanding, profile matching, cache lookup,
    LLM generation, and post-generation constraint validation.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        answer_service: Optional[AnswerService] = None,
        validator: Optional[AnswerValidator] = None,
    ):
        self.llm = llm_provider or get_llm_provider()
        self.answer_service = answer_service or AnswerService()
        self.validator = validator or AnswerValidator()

    def generate_answer(
        self,
        user_id: str,
        question_text: str,
        category: QuestionCategory,
        profile: CandidateProfile,
        job_title: str = "",
        company_name: str = "",
        job_description: str = "",
        max_length: Optional[int] = None,
        max_words: Optional[int] = None,
        options: Optional[list] = None,
    ) -> Tuple[str, float, str]:
        """
        Generates an answer for a job application question.
        
        Returns:
            Tuple of (answer_text, confidence_score, source_description)
        """
        # 1. Check Answer Service / Cache for existing verified answers
        cached_ans, cached_source = self.answer_service.find_reusable_answer(
            user_id=user_id,
            question_text=question_text,
            company=company_name,
            job_title=job_title,
        )
        if cached_ans:
            validated, _ = self.validator.validate_and_clamp(
                cached_ans, max_length=max_length, max_words=max_words
            )
            return validated, 0.95, f"cache:{cached_source}"

        # 2. Check for standard profile matching
        direct_ans, direct_source = self._try_direct_profile_field(profile, category, question_text)
        if direct_ans:
            validated, _ = self.validator.validate_and_clamp(
                direct_ans, max_length=max_length, max_words=max_words
            )
            return validated, 1.0, direct_source

        # 3. LLM Generation with Candidate Context
        prompt = self._build_prompt(
            question_text=question_text,
            category=category,
            profile=profile,
            job_title=job_title,
            company_name=company_name,
            job_description=job_description,
            max_length=max_length,
            max_words=max_words,
            options=options,
        )

        try:
            if not self.llm.is_configured():
                fallback = self._generate_safe_fallback(category, profile)
                return fallback, 0.6, "fallback_rule"

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]

            raw_answer = self.llm.generate(
                messages=messages,
                temperature=0.2,
                max_tokens=350,
            ).strip()

            # Clean quotes if wrapping entire answer
            if raw_answer.startswith('"') and raw_answer.endswith('"') and len(raw_answer) > 2:
                raw_answer = raw_answer[1:-1].strip()

            # 4. Validate & enforce constraints
            validated_answer, was_modified = self.validator.validate_and_clamp(
                raw_answer, max_length=max_length, max_words=max_words
            )

            # Store in answer service if appropriate
            self.answer_service.save_answer(
                user_id=user_id,
                question_text=question_text,
                category=category.value,
                answer_text=validated_answer,
                company=company_name,
                job_title=job_title,
                source="llm_generated",
            )

            return validated_answer, 0.88, "llm_generated"

        except Exception as e:
            logger.error(f"Error in QuestionAgent LLM generation: {e}")
            fallback = self._generate_safe_fallback(category, profile)
            return fallback, 0.5, "fallback_rule"

    def _try_direct_profile_field(
        self, profile: CandidateProfile, category: QuestionCategory, question_text: str
    ) -> Tuple[Optional[str], str]:
        """Maps standard questions directly to profile fields without calling LLM."""
        q_lower = question_text.lower()
        p = profile

        if category == QuestionCategory.CONTACT or "email" in q_lower:
            if "email" in q_lower and p.personal.email:
                return p.personal.email, "profile.personal.email"
            if "phone" in q_lower and p.personal.phone:
                return p.personal.phone, "profile.personal.phone"
            if ("city" in q_lower or "location" in q_lower or "address" in q_lower) and p.personal.location:
                return p.personal.location, "profile.personal.location"

        if category == QuestionCategory.LINKS or "linkedin" in q_lower or "github" in q_lower or "portfolio" in q_lower:
            if "linkedin" in q_lower and p.links.linkedin:
                return p.links.linkedin, "profile.links.linkedin"
            if "github" in q_lower and p.links.github:
                return p.links.github, "profile.links.github"
            if ("portfolio" in q_lower or "website" in q_lower) and p.links.portfolio:
                return p.links.portfolio, "profile.links.portfolio"

        if category == QuestionCategory.EDUCATION or "university" in q_lower or "college" in q_lower or "degree" in q_lower:
            if ("college" in q_lower or "university" in q_lower or "institution" in q_lower) and p.education.college_name:
                return p.education.college_name, "profile.education.college_name"
            if ("degree" in q_lower or "qualification" in q_lower) and p.education.degree:
                return p.education.degree, "profile.education.degree"
            if ("major" in q_lower or "branch" in q_lower or "specialization" in q_lower) and p.education.branch:
                return p.education.branch, "profile.education.branch"
            if ("gpa" in q_lower or "cgpa" in q_lower or "grade" in q_lower) and p.education.gpa:
                return str(p.education.gpa), "profile.education.gpa"
            if ("graduat" in q_lower or "passing year" in q_lower) and p.education.graduation_year:
                return str(p.education.graduation_year), "profile.education.graduation_year"

        if "experience" in q_lower and ("years" in q_lower or "how many" in q_lower):
            years = p.professional.years_of_experience
            return str(years), "profile.professional.years_of_experience"

        return None, ""

    def _build_prompt(
        self,
        question_text: str,
        category: QuestionCategory,
        profile: CandidateProfile,
        job_title: str,
        company_name: str,
        job_description: str,
        max_length: Optional[int],
        max_words: Optional[int],
        options: Optional[list],
    ) -> str:
        """Constructs a comprehensive, grounded prompt for the LLM."""
        projects_summary = "\n".join(
            [f"- {pr.title}: {pr.description} (Tech: {', '.join(pr.technologies)})" for pr in profile.projects[:3]]
        ) or "None specified"

        exp_summary = "\n".join(
            [f"- {e.role} at {e.company} ({e.duration}): {e.description}" for e in profile.experience[:3]]
        ) or "None (Student / Entry-level)"

        options_text = ""
        if options and len(options) > 0:
            options_text = f"\nAvailable Multiple Choice Options (You MUST choose the best option from this list):\n" + "\n".join(
                [f" - {opt}" for opt in options]
            )

        constraints = []
        if max_length:
            constraints.append(f"Maximum character limit: {max_length}")
        if max_words:
            constraints.append(f"Maximum word limit: {max_words}")
        constraints_text = "\n".join(constraints) if constraints else "Keep concise and direct."

        return f"""
TARGET JOB INFORMATION:
Company: {company_name or 'Hiring Company'}
Role: {job_title or 'Target Position'}
Role Context: {job_description[:300] if job_description else 'N/A'}

CANDIDATE VERIFIED PROFILE:
Name: {profile.personal.full_name}
Degree/College: {profile.education.degree} in {profile.education.branch}, {profile.education.college_name} (Graduation: {profile.education.graduation_year})
Key Skills: {', '.join(profile.professional.key_skills)}
Years of Experience: {profile.professional.years_of_experience}
Recent Experience:
{exp_summary}
Notable Projects:
{projects_summary}
Bio / Summary: {profile.professional.summary}

APPLICATION QUESTION TO ANSWER:
"{question_text}"
Category: {category.value}
{options_text}

CONSTRAINTS:
{constraints_text}

Provide the exact answer:"""

    def _generate_safe_fallback(self, category: QuestionCategory, profile: CandidateProfile) -> str:
        """Generates a safe fallback when LLM generation fails."""
        if category == QuestionCategory.EXPERIENCE:
            return f"I have strong hands-on experience in {', '.join(profile.professional.key_skills[:4])} through projects and coursework."
        if category == QuestionCategory.AVAILABILITY:
            return "Immediately available"
        if category == QuestionCategory.LOCATION:
            return profile.personal.location or "Open to relocation and remote work"
        if category == QuestionCategory.SALARY:
            return "Competitive / Negotiable"
        return "Yes"
