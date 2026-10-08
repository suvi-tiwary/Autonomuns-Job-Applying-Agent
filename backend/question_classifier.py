import re
from typing import Dict, Any, Optional
from models import QuestionCategory
from llm_provider import get_llm_provider


def normalize(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


SENSITIVE_KEYWORDS = [
    # Demographics & Diversity
    "gender", "race", "ethnicity", "hispanic", "latino", "sexual orientation",
    "pronoun", "veteran", "military", "protected veteran", "armed forces",
    # Disability & Accommodations
    "disability", "disabled", "medical condition", "physical condition", "accommodation",
    # Work Authorization & Sponsorship Declarations
    "require sponsorship", "sponsorship now or in the future", "visa status",
    "h1b", "opt/cpt", "require visa sponsorship",
    # Legal & Background
    "felony", "misdemeanor", "criminal", "convicted", "background check", "drug test",
    "security clearance", "non-compete", "nda",
    # Attestation & Legal Consent
    "i certify", "i declare", "under penalty", "signature", "sign here", "attest",
    "terms and conditions", "privacy notice consent", "i agree that the information"
]


class FieldClassificationResult:
    def __init__(
        self,
        category: QuestionCategory,
        profile_key: Optional[str] = None,
        can_be_filled_from_profile: bool = False,
        requires_llm: bool = False,
        is_sensitive: bool = False,
        confidence: float = 1.0,
        explanation: str = ""
    ):
        self.category = category
        self.profile_key = profile_key
        self.can_be_filled_from_profile = can_be_filled_from_profile
        self.requires_llm = requires_llm
        self.is_sensitive = is_sensitive
        self.confidence = confidence
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "profile_key": self.profile_key,
            "can_be_filled_from_profile": self.can_be_filled_from_profile,
            "requires_llm": self.requires_llm,
            "is_sensitive": self.is_sensitive,
            "confidence": self.confidence,
            "explanation": self.explanation
        }


def is_sensitive_question(field: Dict[str, Any]) -> bool:
    """
    Checks if a field touches sensitive demographic, disability, veteran,
    criminal, or legal attestation topics.
    """
    # Core contact inputs are never sensitive questions
    name_id = (field.get("name", "") + " " + field.get("id", "") + " " + field.get("autocomplete", "")).lower()
    if any(core in name_id for core in ["first_name", "last_name", "email", "phone", "mobile", "tel", "resume", "cv", "linkedin", "github"]):
        return False

    text = normalize(" ".join([
        field.get("label", ""),
        field.get("placeholder", ""),
        field.get("name", ""),
        field.get("aria_label", ""),
        field.get("surrounding_text", ""),
        field.get("parent_text", "")
    ]))

    return any(keyword in text for keyword in SENSITIVE_KEYWORDS)


def classify_field(field: Dict[str, Any], use_llm_fallback: bool = False) -> FieldClassificationResult:
    """
    Modular classification pipeline that classifies form fields into categories.
    Determines whether a field should be filled from profile, generated via LLM,
    or flagged as sensitive for user review.
    """
    tag = (field.get("tag") or "").lower()
    field_type = (field.get("type") or "").lower()
    field_name = (field.get("name") or "").lower()
    field_id = (field.get("id") or "").lower()
    autocomplete = (field.get("autocomplete") or "").lower()
    label = (field.get("label") or "").lower()
    placeholder = (field.get("placeholder") or "").lower()
    aria_label = (field.get("aria_label") or "").lower()

    text = normalize(f"{field_type} {field_name} {field_id} {autocomplete} {label} {placeholder} {aria_label}")
    question_text = normalize(label or placeholder or aria_label or field_name)

    # 1. Check for sensitive legal / demographic declarations first
    if is_sensitive_question(field):
        return FieldClassificationResult(
            category=QuestionCategory.SENSITIVE_LEGAL,
            is_sensitive=True,
            explanation="Requires manual applicant confirmation or legal consent."
        )

    # 2. Check standard structured profile fields
    # FIRST NAME
    if (
        "first_name" in field_name or "first_name" in field_id or "firstname" in field_name or "firstname" in field_id or
        "first name" in label or "first name" in placeholder or autocomplete == "given-name" or
        "given name" in label or "forename" in label
    ):
        return FieldClassificationResult(
            category=QuestionCategory.PERSONAL_INFO,
            profile_key="first_name",
            can_be_filled_from_profile=True,
            explanation="Matched first name"
        )

    # LAST NAME
    if (
        "last_name" in field_name or "last_name" in field_id or "lastname" in field_name or "lastname" in field_id or
        "last name" in label or "last name" in placeholder or autocomplete == "family-name" or
        "surname" in label or "family name" in label
    ):
        return FieldClassificationResult(
            category=QuestionCategory.PERSONAL_INFO,
            profile_key="last_name",
            can_be_filled_from_profile=True,
            explanation="Matched last name"
        )

    # EMAIL
    if (
        "email" in field_name or "email" in field_id or field_type == "email" or
        autocomplete == "email" or "email" in label or "email" in placeholder
    ):
        return FieldClassificationResult(
            category=QuestionCategory.CONTACT_INFO,
            profile_key="email",
            can_be_filled_from_profile=True,
            explanation="Matched email"
        )

    # PHONE
    if (
        "phone" in field_name or "phone" in field_id or field_type == "tel" or autocomplete == "tel" or
        "mobile" in field_name or "mobile" in field_id or
        any(w in label for w in ["phone", "mobile", "contact number", "telephone", "cell"]) or
        any(w in placeholder for w in ["phone", "mobile"])
    ):
        return FieldClassificationResult(
            category=QuestionCategory.CONTACT_INFO,
            profile_key="phone",
            can_be_filled_from_profile=True,
            explanation="Matched phone number"
        )

    # FULL NAME (when not first/last)
    if (
        "full_name" in field_name or "fullname" in field_name or
        any(w in label for w in ["full name", "candidate name", "your name", "applicant name"]) or
        label == "name" or label == "name *" or label.startswith("name (")
    ):
        return FieldClassificationResult(
            category=QuestionCategory.PERSONAL_INFO,
            profile_key="full_name",
            can_be_filled_from_profile=True,
            explanation="Matched full name"
        )

    # LINKEDIN
    if "linkedin" in text:
        return FieldClassificationResult(
            category=QuestionCategory.LINK,
            profile_key="linkedin",
            can_be_filled_from_profile=True,
            explanation="Matched LinkedIn URL"
        )

    # GITHUB
    if "github" in text:
        return FieldClassificationResult(
            category=QuestionCategory.LINK,
            profile_key="github",
            can_be_filled_from_profile=True,
            explanation="Matched GitHub URL"
        )

    # PORTFOLIO / WEBSITE
    if (
        "portfolio" in text or "website" in text or "blog" in text or
        "personal url" in label or "website url" in label or "personal link" in label
    ):
        return FieldClassificationResult(
            category=QuestionCategory.LINK,
            profile_key="portfolio",
            can_be_filled_from_profile=True,
            explanation="Matched Portfolio / Website URL"
        )

    # LOCATION / CITY
    if (
        "location" in field_name or "location" in field_id or "city" in field_name or "city" in field_id or
        any(w in label for w in ["current city", "current location", "where are you located", "location", "city"])
    ):
        return FieldClassificationResult(
            category=QuestionCategory.LOCATION,
            profile_key="location",
            can_be_filled_from_profile=True,
            explanation="Matched location / city"
        )

    # ADDRESS
    if "address" in field_name or "address" in field_id or "street address" in label:
        return FieldClassificationResult(
            category=QuestionCategory.CONTACT_INFO,
            profile_key="address",
            can_be_filled_from_profile=True,
            explanation="Matched address"
        )

    # POSTAL / ZIP
    if any(w in text for w in ["zip", "postal", "zipcode", "pincode", "pin code", "postal code"]):
        return FieldClassificationResult(
            category=QuestionCategory.CONTACT_INFO,
            profile_key="postal_code",
            can_be_filled_from_profile=True,
            explanation="Matched postal code"
        )

    # COLLEGE / UNIVERSITY
    if any(w in text for w in ["college", "university", "institution", "school name"]):
        return FieldClassificationResult(
            category=QuestionCategory.EDUCATION,
            profile_key="college",
            can_be_filled_from_profile=True,
            explanation="Matched college / university"
        )

    # DEGREE / EDUCATION
    if any(w in text for w in ["degree", "qualification", "academic discipline", "major", "field of study"]):
        return FieldClassificationResult(
            category=QuestionCategory.EDUCATION,
            profile_key="degree",
            can_be_filled_from_profile=True,
            explanation="Matched degree / education"
        )

    # GRADUATION YEAR
    if any(w in text for w in ["graduation year", "year of graduation", "grad year", "passing year"]):
        return FieldClassificationResult(
            category=QuestionCategory.EDUCATION,
            profile_key="graduation_year",
            can_be_filled_from_profile=True,
            explanation="Matched graduation year"
        )

    # SKILLS
    if any(w in text for w in ["skills", "technologies", "tech stack", "programming languages"]):
        return FieldClassificationResult(
            category=QuestionCategory.PERSONAL_INFO,
            profile_key="skills",
            can_be_filled_from_profile=True,
            explanation="Matched skills"
        )

    # EXPERIENCE YEARS
    if any(w in text for w in ["years of experience", "experience years", "total experience", "yoe"]):
        return FieldClassificationResult(
            category=QuestionCategory.PERSONAL_INFO,
            profile_key="experience_years",
            can_be_filled_from_profile=True,
            explanation="Matched experience years"
        )

    # WORK AUTHORIZATION
    if any(w in text for w in ["authorized to work", "legally authorized", "work authorization", "visa sponsorship"]):
        return FieldClassificationResult(
            category=QuestionCategory.WORK_AUTHORIZATION,
            profile_key="work_authorization",
            can_be_filled_from_profile=True,
            explanation="Matched work authorization"
        )

    # RELOCATION
    if any(w in text for w in ["willing to relocate", "relocation"]):
        return FieldClassificationResult(
            category=QuestionCategory.LOCATION,
            profile_key="willing_to_relocate",
            can_be_filled_from_profile=True,
            explanation="Matched relocation preference"
        )

    # SALARY / STIPEND
    if any(w in text for w in ["expected salary", "expected ctc", "desired salary", "expected stipend", "salary expectation"]):
        return FieldClassificationResult(
            category=QuestionCategory.SALARY,
            profile_key="expected_salary_stipend",
            can_be_filled_from_profile=True,
            explanation="Matched salary / stipend expectation"
        )

    # AVAILABILITY / NOTICE PERIOD
    if any(w in text for w in ["notice period", "availability", "how soon can you start", "earliest start date"]):
        return FieldClassificationResult(
            category=QuestionCategory.AVAILABILITY,
            profile_key="notice_period",
            can_be_filled_from_profile=True,
            explanation="Matched notice period / availability"
        )

    # 3. Check for Descriptive / Open-Ended Questions requiring LLM
    # COVER LETTER
    if any(w in question_text for w in ["cover letter", "cover note", "message to the hiring team", "message to hiring manager", "letter of intent"]):
        return FieldClassificationResult(
            category=QuestionCategory.COVER_LETTER,
            requires_llm=True,
            explanation="Requires customized cover letter generation"
        )

    # WHY COMPANY
    if (
        ("why" in question_text and any(w in question_text for w in ["join us", "work here", "this company", "work with us", "our mission", "interest in us", "interest in working at"])) or
        "what excites you about" in question_text or
        "why do you want to work at" in question_text or
        "why do you want to join" in question_text
    ):
        return FieldClassificationResult(
            category=QuestionCategory.WHY_COMPANY,
            requires_llm=True,
            explanation="Requires company-specific motivation generation"
        )

    # WHY ROLE / INTERNSHIP
    if (
        ("why" in question_text and any(w in question_text for w in ["this role", "this position", "this internship", "this job", "good fit", "hire you", "choose you"])) or
        "what makes you a good fit" in question_text or
        "why should we hire you" in question_text or
        "why are you interested in this" in question_text
    ):
        return FieldClassificationResult(
            category=QuestionCategory.WHY_ROLE,
            requires_llm=True,
            explanation="Requires role-fit explanation generation"
        )

    # PROJECT DESCRIPTION
    if (
        any(w in question_text for w in ["explain a project", "tell us about a project", "describe a project", "most relevant project", "project you're proud of", "challenging project", "technical project", "portfolio project"]) or
        ("project" in question_text and any(w in question_text for w in ["describe", "explain", "detail", "built", "share"]))
    ):
        return FieldClassificationResult(
            category=QuestionCategory.PROJECT_DESCRIPTION,
            requires_llm=True,
            explanation="Requires candidate project description generation"
        )

    # ACHIEVEMENT
    if any(w in question_text for w in ["achievement", "greatest accomplishment", "proudest moment", "key achievement"]):
        return FieldClassificationResult(
            category=QuestionCategory.ACHIEVEMENT,
            requires_llm=True,
            explanation="Requires candidate achievement elaboration"
        )

    # EXPERIENCE
    if any(w in question_text for w in ["previous experience", "past experience", "describe your experience", "tell us about your background"]):
        return FieldClassificationResult(
            category=QuestionCategory.EXPERIENCE,
            requires_llm=True,
            explanation="Requires candidate experience summary"
        )

    # GENERAL DESCRIPTIVE TEXTAREA / OPEN-ENDED
    if tag == "textarea" or (field_type == "text" and len(label) > 30):
        # Open ended question
        return FieldClassificationResult(
            category=QuestionCategory.DESCRIPTIVE,
            requires_llm=True,
            explanation="Open-ended descriptive question"
        )

    # 4. Check YES/NO or MULTIPLE CHOICE
    if field_type in ["radio", "checkbox"] or tag == "select":
        return FieldClassificationResult(
            category=QuestionCategory.MULTIPLE_CHOICE,
            can_be_filled_from_profile=False,
            requires_llm=False,
            explanation="Multiple choice or toggle field"
        )

    # 5. Lightweight LLM Classification Fallback if ambiguous & requested
    if use_llm_fallback and len(question_text) > 15:
        try:
            llm = get_llm_provider()
            if llm.is_configured():
                prompt = f"""
Classify this job application question into ONE category:
[PERSONAL_INFO, CONTACT_INFO, EDUCATION, LINK, WORK_AUTHORIZATION, LOCATION, SALARY, AVAILABILITY, PROJECT_DESCRIPTION, WHY_COMPANY, WHY_ROLE, ACHIEVEMENT, EXPERIENCE, COVER_LETTER, DESCRIPTIVE, SENSITIVE_LEGAL, UNKNOWN]

Question: "{question_text}"
Field Tag: {tag}, Type: {field_type}

Return ONLY the category name.
"""
                resp = llm.generate([{"role": "user", "content": prompt}], max_tokens=20).strip().upper()
                for cat in QuestionCategory:
                    if cat.value in resp:
                        req_llm = cat in [
                            QuestionCategory.DESCRIPTIVE,
                            QuestionCategory.PROJECT_DESCRIPTION,
                            QuestionCategory.WHY_COMPANY,
                            QuestionCategory.WHY_ROLE,
                            QuestionCategory.ACHIEVEMENT,
                            QuestionCategory.EXPERIENCE,
                            QuestionCategory.COVER_LETTER
                        ]
                        return FieldClassificationResult(
                            category=cat,
                            requires_llm=req_llm,
                            is_sensitive=(cat == QuestionCategory.SENSITIVE_LEGAL),
                            explanation=f"Classified via LLM into {cat.value}"
                        )
        except Exception as e:
            print(f"[Classifier] LLM fallback notice: {e}")

    return FieldClassificationResult(
        category=QuestionCategory.UNKNOWN,
        can_be_filled_from_profile=False,
        requires_llm=False,
        explanation="Unknown field type"
    )
