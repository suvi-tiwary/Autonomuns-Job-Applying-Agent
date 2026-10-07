import re


def normalize(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


SENSITIVE_KEYWORDS = [
    # Demographics & Diversity
    "gender", "race", "ethnicity", "hispanic", "latino", "sexual orientation",
    "pronoun", "veteran", "military", "protected veteran", "armed forces",
    # Disability & Accommodations
    "disability", "disabled", "medical condition", "physical condition", "accommodation",
    # Work Authorization & Sponsorship
    "require sponsorship", "sponsorship now or in the future", "authorized to work",
    "visa status", "h1b", "opt/cpt", "work authorization", "require visa",
    # Legal & Background
    "felony", "misdemeanor", "criminal", "convicted", "background check", "drug test",
    "security clearance", "non-compete", "nda",
    # Salary & Relocation (unless configured)
    "salary expectation", "desired salary", "compensation requirement", "expected ctc",
    "willing to relocate", "relocation assistance",
    # Attestation & Legal Consent
    "i certify", "i declare", "under penalty", "signature", "sign here", "attest",
    "terms and conditions", "privacy notice consent"
]


def is_sensitive_question(field: dict) -> bool:
    """
    Returns True if the field touches sensitive legal, demographic, disability,
    veteran, sponsorship, criminal, or personal attestation topics.
    These fields must NOT be automatically filled and should be left for manual user review.
    """
    text = normalize(" ".join([
        field.get("label", ""),
        field.get("placeholder", ""),
        field.get("name", ""),
        field.get("aria_label", "")
    ]))

    return any(keyword in text for keyword in SENSITIVE_KEYWORDS)


def is_descriptive_question(field: dict) -> bool:
    """
    Returns True if the field is a safe open-ended motivational or technical question.
    """
    tag = field.get("tag", "").lower()
    field_type = field.get("type", "").lower()
    label = field.get("label", "").lower()

    if tag == "textarea":
        return not is_sensitive_question(field)

    if field_type == "text" and len(label) > 25:
        # Long prompt like "Why do you want to work at Company?"
        safe_starters = ["why", "tell us", "describe", "what makes you", "experience with", "share a project", "how did you"]
        if any(label.startswith(s) or s in label for s in safe_starters):
            return not is_sensitive_question(field)

    return False


def detect_profile_field(field: dict) -> str:
    """
    Maps DOM input elements to standard candidate profile attributes.
    """
    # If it's a sensitive topic, do not auto-map to standard profile fields
    if is_sensitive_question(field):
        return None

    text = normalize(" ".join([
        field.get("type", ""),
        field.get("name", ""),
        field.get("placeholder", ""),
        field.get("aria_label", ""),
        field.get("autocomplete", ""),
        field.get("label", ""),
        field.get("id", "")
    ]))

    # EMAIL
    if "email" in text or field.get("type") == "email" or field.get("autocomplete") == "email":
        return "email"

    # PHONE
    if any(word in text for word in ["phone", "mobile", "telephone", "contact number", "phone number", "cell", "tel"]):
        return "phone"

    # FIRST NAME
    if any(word in text for word in ["first name", "firstname", "given name", "forename", "first_name"]):
        return "first_name"

    # LAST NAME
    if any(word in text for word in ["last name", "lastname", "surname", "family name", "last_name"]):
        return "last_name"

    # FULL NAME (only if not specific first/last)
    if any(word in text for word in ["full name", "candidate name", "your name", "full_name", "applicant name"]):
        return "full_name"
    if text == "name" or text == "name *":
        return "full_name"

    # LINKEDIN
    if "linkedin" in text:
        return "linkedin"

    # GITHUB
    if "github" in text:
        return "github"

    # PORTFOLIO / WEBSITE
    if any(word in text for word in ["portfolio", "personal website", "website", "blog", "portfolio url"]):
        return "portfolio"

    # CITY / LOCATION
    if any(word in text for word in ["city", "current city", "current location", "where are you located", "location"]):
        return "location"

    # ADDRESS
    if any(word in text for word in ["street address", "residence address", "address line"]):
        return "address"

    # POSTAL / ZIP
    if any(word in text for word in ["zip", "postal", "zipcode", "pincode", "pin code", "postal code"]):
        return "postal_code"

    # COUNTRY
    if any(word in text for word in ["country", "nation"]):
        return "country"

    # STATE
    if any(word in text for word in ["state", "province", "region"]):
        return "state"

    # COLLEGE / UNIVERSITY
    if any(word in text for word in ["college", "university", "institution", "school name"]):
        return "college"

    # DEGREE / EDUCATION
    if any(word in text for word in ["degree", "qualification", "education", "academic discipline", "major"]):
        return "education"

    # SKILLS
    if any(word in text for word in ["skills", "technologies", "tech stack"]):
        return "skills"

    # EXPERIENCE YEARS
    if any(word in text for word in ["years of experience", "experience years", "total experience", "yoe"]):
        return "experience_years"

    return None