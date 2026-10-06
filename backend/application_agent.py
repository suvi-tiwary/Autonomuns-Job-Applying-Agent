import asyncio
import os

from pypdf import PdfReader

from browser_agent import (
    open_browser,
    click_apply,
    detect_login_required,
    get_application_fields,
    get_page_text,
    fill_field,
    upload_resume,
    click_next
)

from field_mapper import detect_profile_field

from llm_answer import generate_answer


# =========================================================
# CANDIDATE PROFILE
# =========================================================

profile = {

    "first_name": "Suvi",

    "last_name": "Tiwary",

    "full_name": "Suvi Tiwary",

    "email": "",

    "phone": "",

    "linkedin": "",

    "github": "https://github.com/suvi-tiwary",

    "portfolio": "",

    "location": "India",

    "address": "",

    "education": "B.Tech Artificial Intelligence and Machine Learning",

    "college": "",

    "experience_years": "0"
}


# =========================================================
# RESUME TEXT EXTRACTION
# =========================================================

def extract_resume_text(resume_path):

    try:

        reader = PdfReader(
            resume_path
        )

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text
                text += "\n"

        return text.strip()

    except Exception as error:

        print(
            "\nCould not read resume:"
        )

        print(error)

        return ""


# =========================================================
# DESCRIPTIVE QUESTION DETECTOR
# =========================================================

def is_descriptive_question(field):

    field_type = (
        field.get(
            "type",
            ""
        )
        .lower()
    )

    label = " ".join([
        field.get("label", ""),
        field.get("placeholder", ""),
        field.get("name", ""),
        field.get("aria_label", "")
    ]).lower()

    descriptive_words = [

        "tell us",

        "tell me",

        "describe",

        "explain",

        "why do you",

        "why are you",

        "why should",

        "interested",

        "interest",

        "motivation",

        "about yourself",

        "projects",

        "achievement",

        "accomplishment",

        "cover letter",

        "additional information",

        "anything else",

        "experience",

        "strengths"
    ]

    if field_type == "textarea":

        return True

    if any(
        word in label
        for word in descriptive_words
    ):

        return True

    return False


# =========================================================
# PRINT FIELD INFORMATION
# =========================================================

def print_field(
    field,
    match
):

    print(
        "\n--------------------------------"
    )

    print(
        "INDEX:",
        field["index"]
    )

    print(
        "TYPE:",
        field["type"]
    )

    print(
        "NAME:",
        field["name"]
    )

    print(
        "LABEL:",
        field["label"]
    )

    print(
        "PLACEHOLDER:",
        field["placeholder"]
    )

    print(
        "MATCH:",
        match
    )


# =========================================================
# MAIN APPLICATION AGENT
# =========================================================

async def apply_to_job(
    job_url: str,
    candidate_profile: dict = None,
    resume_path: str = None,
    interactive: bool = False
):
    """
    Automated application agent callable via API or CLI.
    """
    if not job_url:
        print("No URL provided.")
        return

    active_profile = profile.copy()
    if candidate_profile:
        active_profile.update(candidate_profile)
        if "name" in candidate_profile and candidate_profile["name"]:
            full_name = candidate_profile["name"]
            active_profile["full_name"] = full_name
            parts = full_name.strip().split()
            if parts:
                active_profile["first_name"] = parts[0]
                active_profile["last_name"] = " ".join(parts[1:]) if len(parts) > 1 else ""
        if "years_of_experience" in candidate_profile:
            active_profile["experience_years"] = str(candidate_profile["years_of_experience"])

    playwright = None
    browser = None
    resume_text = ""

    try:
        # -------------------------------------------------
        # OPEN JOB
        # -------------------------------------------------
        print(f"\nOpening job: {job_url}")

        playwright, browser, page = await open_browser(job_url)

        print("Browser opened:", page.url)

        await page.wait_for_timeout(2000)

        # -------------------------------------------------
        # FIND APPLY
        # -------------------------------------------------
        print("\nLooking for Apply button...")

        clicked = await click_apply(page)

        if clicked:
            print("Apply button clicked.")
            await page.wait_for_timeout(2000)
        else:
            print("No Apply button found. URL may already be the application page.")

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------
        login_required = await detect_login_required(page)

        if login_required:
            print("\n" + "=" * 60)
            print("LOGIN / SIGNUP REQUIRED")
            print("=" * 60)
            print("\nPlease complete the login/signup in the browser if needed.")
            if interactive:
                input("\nWhen you are logged in and application is ready, press ENTER...")
            else:
                await page.wait_for_timeout(3000)

        # -------------------------------------------------
        # RESUME PATH
        # -------------------------------------------------
        if not resume_path and interactive:
            print("\n" + "=" * 60)
            print("RESUME")
            print("=" * 60)
            resume_path = input("\nEnter resume PDF path (press ENTER to skip): ").strip()

        if resume_path:

            if os.path.exists(
                resume_path
            ):

                # -----------------------------------------
                # READ RESUME
                # -----------------------------------------

                print(
                    "\nReading resume..."
                )

                resume_text = (
                    extract_resume_text(
                        resume_path
                    )
                )

                print(
                    "Resume text extracted:",
                    len(resume_text),
                    "characters"
                )

                # -----------------------------------------
                # UPLOAD RESUME
                # -----------------------------------------

                print(
                    "\nUploading resume..."
                )

                uploaded = (
                    await upload_resume(
                        page,
                        resume_path
                    )
                )

                if uploaded:

                    print(
                        "Resume uploaded ✓"
                    )

                else:

                    print(
                        "Could not find a usable "
                        "resume upload field."
                    )

            else:

                print(
                    "\nResume file does not exist."
                )

                print(
                    "LLM will continue without "
                    "resume text."
                )

        # -------------------------------------------------
        # SCAN APPLICATION FORM
        # -------------------------------------------------

        print(
            "\nScanning application form..."
        )

        fields = (
            await get_application_fields(
                page
            )
        )

        print(
            f"\nDetected {len(fields)} "
            "potential application fields."
        )

        unknown_fields = []

        # -------------------------------------------------
        # GET JOB CONTEXT
        # -------------------------------------------------

        print(
            "\nCollecting job context..."
        )

        job_context = (
            await get_page_text(
                page
            )
        )

        print(
            "Job context collected:",
            len(job_context),
            "characters"
        )

        # -------------------------------------------------
        # PROCESS EVERY FIELD
        # -------------------------------------------------

        for field in fields:

            match = (
                detect_profile_field(
                    field
                )
            )

            print_field(
                field,
                match
            )

            # =============================================
            # NORMAL PROFILE FIELD
            # =============================================

            if match is not None:

                if match not in profile:

                    print(
                        "STATUS: PROFILE VALUE "
                        "NOT AVAILABLE"
                    )

                    unknown_fields.append(
                        field
                    )

                    continue

                value = active_profile[
                    match
                ]

                if not value:

                    print(
                        "STATUS: VALUE EMPTY"
                    )

                    continue

                try:

                    await fill_field(
                        page,
                        field["index"],
                        value
                    )

                    print(
                        "STATUS: FILLED ✓"
                    )

                except Exception as error:

                    print(
                        "STATUS: FAILED"
                    )

                    print(
                        "ERROR:",
                        error
                    )

                continue

            # =============================================
            # LLM DESCRIPTIVE QUESTION
            # =============================================

            if is_descriptive_question(
                field
            ):

                print(
                    "\n" + "=" * 60
                )

                print(
                    "🤖 DESCRIPTIVE QUESTION DETECTED"
                )

                print(
                    "=" * 60
                )

                question = (
                    field.get("label")
                    or field.get("placeholder")
                    or field.get("aria_label")
                    or field.get("name")
                    or "Application question"
                )

                print(
                    "\nQUESTION:"
                )

                print(
                    question
                )

                print(
                    "\nSTATUS: CALLING LLM..."
                )

                try:

                    answer = generate_answer(

                        question=question,

                        profile=profile,

                        resume_text=resume_text,

                        job_context=job_context
                    )

                    if answer:

                        print(
                            "\n🤖 LLM ANSWER:"
                        )

                        print(
                            answer
                        )

                        await fill_field(

                            page,

                            field["index"],

                            answer
                        )

                        print(
                            "\nSTATUS: "
                            "LLM FILLED ✓"
                        )

                    else:

                        print(
                            "\nSTATUS: "
                            "LLM RETURNED "
                            "EMPTY ANSWER"
                        )

                        unknown_fields.append(
                            field
                        )

                except Exception as error:

                    print(
                        "\nSTATUS: "
                        "LLM FAILED"
                    )

                    print(
                        "ERROR:",
                        error
                    )

                    unknown_fields.append(
                        field
                    )

                continue

            # =============================================
            # UNKNOWN FIELD
            # =============================================

            print(
                "STATUS: UNKNOWN → "
                "MANUAL REVIEW"
            )

            unknown_fields.append(
                field
            )

        # -------------------------------------------------
        # UNKNOWN FIELDS
        # -------------------------------------------------

        if unknown_fields:

            print(
                "\n" + "=" * 60
            )

            print(
                f"{len(unknown_fields)} "
                "fields need manual review."
            )

            print(
                "=" * 60
            )

            for field in unknown_fields:

                print(
                    "\nFIELD:"
                )

                print(
                    "Label:",
                    field["label"]
                )

                print(
                    "Placeholder:",
                    field["placeholder"]
                )

                print(
                    "Type:",
                    field["type"]
                )

        # -------------------------------------------------
        # NEXT PAGE
        # -------------------------------------------------

        print(
            "\nChecking for Next/Continue..."
        )

        moved = await click_next(
            page
        )

        if moved:

            print(
                "Moved to the next "
                "application page."
            )

            print(
                "The current page has been "
                "filled where possible."
            )

        else:

            print(
                "No Next/Continue button found."
            )

        # -------------------------------------------------
        # FINAL SAFETY PAUSE
        # -------------------------------------------------

        print(
            "\n" + "=" * 60
        )

        print(
            "APPLICATION PAUSED FOR REVIEW"
        )

        print(
            "=" * 60
        )

        print(
            "\nThe agent will NOT submit "
            "the application automatically."
        )

        print(
            "Review everything in the browser."
        )

        print(
            "\nPress CTRL+C when you want "
            "to stop the agent."
        )

        await asyncio.sleep(
            100000
        )

    except Exception as error:

        print(
            "\nAGENT ERROR:"
        )

        print(
            error
        )

    finally:

        pass


async def run_application():
    job_url = input("\nPaste the job application URL: ").strip()
    if not job_url:
        print("No URL provided.")
        return
    await apply_to_job(job_url, candidate_profile=profile, interactive=True)


if __name__ == "__main__":
    asyncio.run(run_application())