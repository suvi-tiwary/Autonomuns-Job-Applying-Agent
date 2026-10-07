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
    # Core profile fields are never sensitive questions
    name_id = (field.get("name", "") + " " + field.get("id", "") + " " + field.get("autocomplete", "")).lower()
    if any(core in name_id for core in ["first_name", "last_name", "email", "phone", "mobile", "tel", "resume", "cv", "linkedin", "github"]):
        return False

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
        safe_starters = ["why", "tell us", "describe", "what makes you", "experience with", "share a project", "how did you"]
        if any(label.startswith(s) or s in label for s in safe_starters):
            return not is_sensitive_question(field)

    return False


def detect_profile_field(field: dict) -> str:
    """
    Maps DOM input elements to standard candidate profile attributes.
    """
    field_name = (field.get("name") or "").lower()
    field_id = (field.get("id") or "").lower()
    field_type = (field.get("type") or "").lower()
    autocomplete = (field.get("autocomplete") or "").lower()
    label = (field.get("label") or "").lower()
    placeholder = (field.get("placeholder") or "").lower()

    text = normalize(f"{field_type} {field_name} {field_id} {autocomplete} {label} {placeholder}")

    # FIRST NAME
    if (
        "first_name" in field_name or "first_name" in field_id or "firstname" in field_name or "firstname" in field_id or
        "first name" in label or "first name" in placeholder or autocomplete == "given-name" or
        "given name" in label or "forename" in label
    ):
        return "first_name"

    # LAST NAME
    if (
        "last_name" in field_name or "last_name" in field_id or "lastname" in field_name or "lastname" in field_id or
        "last name" in label or "last name" in placeholder or autocomplete == "family-name" or
        "surname" in label or "family name" in label
    ):
        return "last_name"

    # EMAIL
    if (
        "email" in field_name or "email" in field_id or field_type == "email" or
        autocomplete == "email" or "email" in label or "email" in placeholder
    ):
        return "email"

    # PHONE
    if (
        "phone" in field_name or "phone" in field_id or field_type == "tel" or autocomplete == "tel" or
        "mobile" in field_name or "mobile" in field_id or
        any(w in label for w in ["phone", "mobile", "contact number", "telephone", "cell"]) or
        any(w in placeholder for w in ["phone", "mobile"])
    ):
        return "phone"

    # FULL NAME (only if first/last not matched)
    if (
        "full_name" in field_name or "fullname" in field_name or
        any(w in label for w in ["full name", "candidate name", "your name", "applicant name"]) or
        label == "name" or label == "name *"
    ):
        return "full_name"

    # LINKEDIN
    if "linkedin" in field_name or "linkedin" in field_id or "linkedin" in label or "linkedin" in placeholder:
        return "linkedin"

    # GITHUB
    if "github" in field_name or "github" in field_id or "github" in label or "github" in placeholder:
        return "github"

    # PORTFOLIO / WEBSITE
    if (
        "portfolio" in text or "website" in text or "blog" in text or
        "personal url" in label or "website url" in label
    ):
        return "portfolio"

    # CITY / LOCATION
    if (
        "location" in field_name or "location" in field_id or "city" in field_name or "city" in field_id or
        any(w in label for w in ["current city", "current location", "where are you located", "location", "city"])
    ):
        return "location"

    # ADDRESS
    if "address" in field_name or "address" in field_id or "street address" in label:
        return "address"

    # POSTAL / ZIP
    if any(w in text for w in ["zip", "postal", "zipcode", "pincode", "pin code", "postal code"]):
        return "postal_code"

    # COUNTRY
    if "country" in field_name or "country" in field_id or "country" in label:
        return "country"

    # STATE
    if "state" in field_name or "state" in field_id or "province" in text:
        return "state"

    # COLLEGE / UNIVERSITY
    if any(w in text for w in ["college", "university", "institution", "school name"]):
        return "college"

    # DEGREE / EDUCATION
    if any(w in text for w in ["degree", "qualification", "education", "academic discipline", "major"]):
        return "education"

    # SKILLS
    if any(w in text for w in ["skills", "technologies", "tech stack"]):
        return "skills"

    # EXPERIENCE YEARS
    if any(w in text for w in ["years of experience", "experience years", "total experience", "yoe"]):
        return "experience_years"

    return None