def normalize(text):

    return " ".join(
        text.lower().strip().split()
    )


def detect_profile_field(field):

    text = normalize(
        " ".join([
            field.get("type", ""),
            field.get("name", ""),
            field.get("placeholder", ""),
            field.get("aria_label", ""),
            field.get("autocomplete", ""),
            field.get("label", "")
        ])
    )

    # EMAIL
    if (
        "email" in text
        or field.get("type") == "email"
        or field.get("autocomplete") == "email"
    ):
        return "email"

    # PHONE
    if any(
        word in text
        for word in [
            "phone",
            "mobile",
            "telephone",
            "contact number",
            "phone number"
        ]
    ):
        return "phone"

    # FIRST NAME
    if any(
        word in text
        for word in [
            "first name",
            "firstname",
            "given name",
            "forename"
        ]
    ):
        return "first_name"

    # LAST NAME
    if any(
        word in text
        for word in [
            "last name",
            "lastname",
            "surname",
            "family name"
        ]
    ):
        return "last_name"

    # FULL NAME
    if any(
        word in text
        for word in [
            "full name",
            "candidate name",
            "your name"
        ]
    ):
        return "full_name"

    # LINKEDIN
    if "linkedin" in text:
        return "linkedin"

    # GITHUB
    if "github" in text:
        return "github"

    # PORTFOLIO
    if any(
        word in text
        for word in [
            "portfolio",
            "personal website",
            "website"
        ]
    ):
        return "portfolio"

    # LOCATION
    if any(
        word in text
        for word in [
            "city",
            "location",
            "current location",
            "where are you located"
        ]
    ):
        return "location"

    # ADDRESS
    if any(
        word in text
        for word in [
            "address",
            "street address"
        ]
    ):
        return "address"

    # COLLEGE
    if any(
        word in text
        for word in [
            "college",
            "university",
            "institution",
            "school"
        ]
    ):
        return "college"

    # DEGREE
    if any(
        word in text
        for word in [
            "degree",
            "qualification",
            "education",
            "academic"
        ]
    ):
        return "education"

    # EXPERIENCE
    if any(
        word in text
        for word in [
            "years of experience",
            "experience years",
            "total experience"
        ]
    ):
        return "experience_years"

    return None