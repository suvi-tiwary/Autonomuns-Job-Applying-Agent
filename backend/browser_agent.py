from playwright.async_api import async_playwright


# =========================================================
# TEXT HELPERS
# =========================================================

def normalize(text):
    return " ".join(
        (text or "").lower().strip().split()
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

    if (
        "email" in text
        or field.get("type") == "email"
        or field.get("autocomplete") == "email"
    ):
        return "email"

    if any(word in text for word in [
        "phone",
        "mobile",
        "telephone",
        "contact number",
        "phone number"
    ]):
        return "phone"

    if any(word in text for word in [
        "first name",
        "firstname",
        "given name",
        "forename"
    ]):
        return "first_name"

    if any(word in text for word in [
        "last name",
        "lastname",
        "surname",
        "family name"
    ]):
        return "last_name"

    if any(word in text for word in [
        "full name",
        "candidate name",
        "your name"
    ]):
        return "full_name"

    if "linkedin" in text:
        return "linkedin"

    if "github" in text:
        return "github"

    if any(word in text for word in [
        "portfolio",
        "personal website",
        "website"
    ]):
        return "portfolio"

    if any(word in text for word in [
        "city",
        "location",
        "current location",
        "where are you located"
    ]):
        return "location"

    if any(word in text for word in [
        "address",
        "street address"
    ]):
        return "address"

    if any(word in text for word in [
        "college",
        "university",
        "institution",
        "school"
    ]):
        return "college"

    if any(word in text for word in [
        "degree",
        "qualification",
        "education",
        "academic"
    ]):
        return "education"

    if any(word in text for word in [
        "years of experience",
        "experience years",
        "total experience"
    ]):
        return "experience_years"

    return None


# =========================================================
# BROWSER
# =========================================================



# =========================================================
# FIND APPLY BUTTON
# =========================================================

async def click_apply(page):

    selectors = [
        "button:has-text('Apply')",
        "a:has-text('Apply')",
        "[role='button']:has-text('Apply')",
        "input[type='submit'][value*='Apply' i]",
        "button:has-text('Easy Apply')",
        "a:has-text('Easy Apply')",
        "[role='button']:has-text('Easy Apply')"
    ]

    for selector in selectors:

        try:

            locator = page.locator(selector)

            count = await locator.count()

            for i in range(count):

                element = locator.nth(i)

                if await element.is_visible():

                    await element.scroll_into_view_if_needed()

                    await element.click()

                    return True

        except Exception:
            continue

    return False


# =========================================================
# LOGIN DETECTION
# =========================================================

async def detect_login_required(page):

    text = normalize(
        await page.locator("body").inner_text()
    )

    login_words = [
        "sign in",
        "log in",
        "login",
        "create account",
        "sign up",
        "register"
    ]

    password_field = page.locator(
        "input[type='password']"
    )

    try:
        password_count = await password_field.count()

        if password_count > 0:
            return True
    except Exception:
        pass

    return any(
        word in text
        for word in login_words
    )


# =========================================================
# SCAN APPLICATION FIELDS
# =========================================================

async def get_application_fields(page):

    fields = []

    selectors = [
        "input",
        "textarea",
        "select"
    ]

    index = 0

    for selector in selectors:

        locator = page.locator(selector)

        count = await locator.count()

        for i in range(count):

            element = locator.nth(i)

            try:

                if not await element.is_visible():
                    continue

                field_type = await element.get_attribute("type") or ""

                name = await element.get_attribute("name") or ""

                placeholder = (
                    await element.get_attribute("placeholder")
                    or ""
                )

                aria_label = (
                    await element.get_attribute("aria-label")
                    or ""
                )

                autocomplete = (
                    await element.get_attribute("autocomplete")
                    or ""
                )

                label = ""

                element_id = (
                    await element.get_attribute("id")
                    or ""
                )

                if element_id:

                    label_locator = page.locator(
                        f"label[for='{element_id}']"
                    )

                    if await label_locator.count():

                        try:
                            label = await label_locator.first.inner_text()
                        except Exception:
                            pass

                if not label:

                    try:

                        parent = element.locator("xpath=..")

                        parent_text = await parent.inner_text()

                        if parent_text:
                            label = parent_text[:300]

                    except Exception:
                        pass

                fields.append({
                    "index": index,
                    "type": field_type or (
                        "textarea"
                        if selector == "textarea"
                        else "select"
                        if selector == "select"
                        else "text"
                    ),
                    "name": name,
                    "label": label.strip(),
                    "placeholder": placeholder,
                    "aria_label": aria_label,
                    "autocomplete": autocomplete
                })

                index += 1

            except Exception:
                continue

    return fields


# =========================================================
# PAGE TEXT
# =========================================================

async def get_page_text(page):

    try:

        text = await page.locator(
            "body"
        ).inner_text()

        return text[:30000]

    except Exception:

        return ""


# =========================================================
# FILL FIELD
# =========================================================

async def fill_field(
    page,
    index,
    value
):

    elements = page.locator(
        "input, textarea, select"
    )

    count = await elements.count()

    if index >= count:
        raise IndexError(
            f"Field index {index} not found. "
            f"Only {count} fields detected."
        )

    element = elements.nth(index)

    await element.scroll_into_view_if_needed()

    tag = await element.evaluate(
        "(el) => el.tagName.toLowerCase()"
    )

    if tag == "select":

        try:

            await element.select_option(
                label=str(value)
            )

        except Exception:

            await element.select_option(
                value=str(value)
            )

        return

    field_type = (
        await element.get_attribute("type")
        or ""
    ).lower()

    if field_type in [
        "checkbox",
        "radio"
    ]:

        if not await element.is_checked():

            await element.check()

        return

    await element.fill(
        str(value)
    )


# =========================================================
# RESUME UPLOAD
# =========================================================

async def upload_resume(
    page,
    resume_path
):

    inputs = page.locator(
        "input[type='file']"
    )

    count = await inputs.count()

    for i in range(count):

        try:

            element = inputs.nth(i)

            if await element.is_visible():

                await element.set_input_files(
                    resume_path
                )

                return True

        except Exception:
            continue

    # Some file inputs may technically be hidden.
    # Try them as a fallback.

    for i in range(count):

        try:

            element = inputs.nth(i)

            await element.set_input_files(
                resume_path
            )

            return True

        except Exception:
            continue

    return False


# =========================================================
# NEXT / CONTINUE
# =========================================================

async def click_next(page):

    selectors = [
        "button:has-text('Next')",
        "button:has-text('Continue')",
        "button:has-text('Save and Continue')",
        "button:has-text('Review')",
        "input[type='submit'][value*='Next' i]",
        "input[type='submit'][value*='Continue' i]",
        "[role='button']:has-text('Next')",
        "[role='button']:has-text('Continue')"
    ]

    for selector in selectors:

        try:

            locator = page.locator(selector)

            count = await locator.count()

            for i in range(count):

                element = locator.nth(i)

                if await element.is_visible():

                    await element.scroll_into_view_if_needed()

                    await element.click()

                    await page.wait_for_timeout(1500)

                    return True

        except Exception:
            continue

    return False