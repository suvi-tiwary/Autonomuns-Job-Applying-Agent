def normalize(text):
    return " ".join((text or "").lower().strip().split())


def detect_profile_field(field):
    text = normalize(" ".join([
        field.get("type", ""),
        field.get("name", ""),
        field.get("placeholder", ""),
        field.get("aria_label", ""),
        field.get("autocomplete", ""),
        field.get("label", "")
    ]))

    # EMAIL
    if "email" in text or field.get("type") == "email" or field.get("autocomplete") == "email":
        return "email"

    # PHONE
    if any(word in text for word in ["phone", "mobile", "telephone", "contact number", "phone number", "cell"]):
        return "phone"

    # FIRST NAME
    if any(word in text for word in ["first name", "firstname", "given name", "forename"]):
        return "first_name"

    # LAST NAME
    if any(word in text for word in ["last name", "lastname", "surname", "family name"]):
        return "last_name"

    # FULL NAME
    if any(word in text for word in ["full name", "candidate name", "your name", "name"]):
        return "full_name"

    # LINKEDIN
    if "linkedin" in text:
        return "linkedin"

    # GITHUB
    if "github" in text:
        return "github"

    # PORTFOLIO / WEBSITE
    if any(word in text for word in ["portfolio", "personal website", "website", "blog", "url"]):
        return "portfolio"

    # CITY / LOCATION
    if any(word in text for word in ["city", "location", "current location", "where are you located"]):
        return "location"

    # ADDRESS
    if any(word in text for word in ["address", "street address", "residence"]):
        return "address"

    # POSTAL / ZIP
    if any(word in text for word in ["zip", "postal", "zipcode", "pincode", "pin code"]):
        return "postal_code"

    # COUNTRY
    if any(word in text for word in ["country", "nation"]):
        return "country"

    # STATE
    if any(word in text for word in ["state", "province", "region"]):
        return "state"

    # COLLEGE / UNIVERSITY
    if any(word in text for word in ["college", "university", "institution", "school"]):
        return "college"

    # DEGREE / EDUCATION
    if any(word in text for word in ["degree", "qualification", "education", "academic", "major"]):
        return "education"

    # SKILLS
    if any(word in text for word in ["skills", "technologies", "tech stack"]):
        return "skills"

    # EXPERIENCE
    if any(word in text for word in ["years of experience", "experience years", "total experience", "yoe"]):
        return "experience_years"

    return None