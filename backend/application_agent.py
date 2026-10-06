import asyncio
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from pypdf import PdfReader

from browser_agent import (
    open_browser,
    click_apply,
    detect_login_required,
    get_application_fields,
    get_page_text,
    fill_field,
    upload_resume,
    click_next,
    submit_application,
    scroll_page
)
from field_mapper import detect_profile_field
from llm_answer import generate_answer

# Default candidate profile fallback
profile = {
    "first_name": "Suvi",
    "last_name": "Tiwary",
    "full_name": "Suvi Tiwary",
    "email": "suvitiwary@example.com",
    "phone": "+919876543210",
    "linkedin": "https://linkedin.com/in/suvi-tiwary",
    "github": "https://github.com/suvi-tiwary",
    "portfolio": "https://suvitiwary.dev",
    "location": "India",
    "country": "India",
    "address": "Delhi NCR, India",
    "education": "B.Tech in Artificial Intelligence & Machine Learning",
    "college": "Institute of Technology",
    "experience_years": "1",
    "skills": "Python, Machine Learning, Deep Learning, FastAPI, React, Playwright, NLP",
}


def extract_resume_text(resume_path: str) -> str:
    if not resume_path or not os.path.isfile(resume_path):
        return ""
    try:
        reader = PdfReader(resume_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except Exception as error:
        print(f"Could not extract resume text from {resume_path}: {error}")
        return ""


def is_descriptive_question(field: dict) -> bool:
    field_type = (field.get("type") or "").lower()
    label = " ".join([
        field.get("label", ""),
        field.get("placeholder", ""),
        field.get("name", ""),
        field.get("aria_label", "")
    ]).lower()

    descriptive_words = [
        "tell us", "tell me", "describe", "explain", "why do you",
        "why are you", "why should", "interested", "interest",
        "motivation", "about yourself", "projects", "achievement",
        "accomplishment", "cover letter", "additional information",
        "anything else", "experience", "strengths", "what makes you"
    ]

    if field_type == "textarea":
        return True

    return any(word in label for word in descriptive_words)


def _format_field_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        items = []
        for item in value:
            if isinstance(item, dict):
                parts = [str(v).strip() for v in item.values() if v]
                if parts:
                    items.append(" - ".join(parts))
            elif item:
                items.append(str(item).strip())
        return ", ".join(items)
    if isinstance(value, dict):
        return ", ".join(f"{k}: {v}" for k, v in value.items() if v)
    return str(value).strip()


async def apply_to_job(
    job_url: str,
    candidate_profile: dict = None,
    resume_path: str = None,
    interactive: bool = False
) -> dict:
    """
    Automated job application agent that navigates to a job, detects fields,
    fills profile data, uses LLM for open questions, and handles multi-page forms.
    """
    if not job_url:
        return {"status": "failed", "error": "Job URL is required."}

    active_profile = profile.copy()
    if candidate_profile:
        active_profile.update(candidate_profile)
        # Parse full name
        full_name = candidate_profile.get("name") or candidate_profile.get("full_name")
        if full_name:
            active_profile["full_name"] = full_name.strip()
            parts = full_name.strip().split()
            active_profile["first_name"] = parts[0]
            active_profile["last_name"] = " ".join(parts[1:]) if len(parts) > 1 else ""
        if "years_of_experience" in candidate_profile:
            active_profile["experience_years"] = str(candidate_profile["years_of_experience"])
        if isinstance(active_profile.get("skills"), list):
            active_profile["skills"] = ", ".join(active_profile["skills"])

    playwright = None
    browser = None
    resume_text = extract_resume_text(resume_path) if resume_path else ""

    try:
        print(f"\n[Agent] Opening job: {job_url}")
        playwright, browser, page = await open_browser(job_url, headless=(not interactive))
        print(f"[Agent] Browser loaded: {page.url}")

        # Trigger dynamic components
        await scroll_page(page)

        # 1. Look for Apply / Easy Apply button
        apply_clicked = await click_apply(page)
        if apply_clicked:
            print("[Agent] Clicked Apply button.")
            await page.wait_for_timeout(1000)
            await scroll_page(page)

        # 2. Check for login requirements
        if await detect_login_required(page):
            print("[Agent] Login / Signup required.")
            if interactive:
                input("\n[Interactive] Complete login in the browser, then press ENTER...")
            else:
                return {
                    "status": "login_required",
                    "job_url": page.url,
                    "message": "This job application requires manual login / sign-in."
                }

        # 3. Upload Resume if available
        if resume_path and os.path.isfile(resume_path):
            print("[Agent] Uploading resume...")
            uploaded = await upload_resume(page, resume_path)
            if uploaded:
                print("[Agent] Resume uploaded successfully [OK]")

        # 4. Multi-step form filling loop
        max_steps = 6
        step = 0
        submitted = False

        while step < max_steps:
            step += 1
            print(f"\n[Agent] Processing form step {step}...")

            fields = await get_application_fields(page)
            job_context = await get_page_text(page)

            if fields:
                print(f"[Agent] Found {len(fields)} form fields on page.")
                for field in fields:
                    match_key = detect_profile_field(field)
                    
                    if match_key and active_profile.get(match_key):
                        val = _format_field_value(active_profile[match_key])
                        await fill_field(page, field["index"], val)
                        print(f"  [OK] Filled [{field.get('name') or field.get('label') or match_key}]: {val[:30]}")
                        continue

                    # Handle descriptive or AI question
                    if is_descriptive_question(field):
                        q_text = field.get("label") or field.get("placeholder") or field.get("name") or "Job question"
                        print(f"  [AI] Generating LLM response for: {q_text[:40]}...")
                        answer = generate_answer(
                            question=q_text,
                            profile=active_profile,
                            resume_text=resume_text,
                            job_context=job_context
                        )
                        if answer:
                            await fill_field(page, field["index"], answer)
                            print(f"  [OK] LLM filled [{q_text[:25]}]")
                        continue

                    # Handle standard checkboxes (e.g. Terms / Consent)
                    if field.get("type") == "checkbox" and field.get("required"):
                        await fill_field(page, field["index"], "true")
                        print(f"  [OK] Checked consent [{field.get('label')[:25]}]")

            # Try to Submit
            if await submit_application(page):
                print("[Agent] Submit application button clicked! [OK]")
                submitted = True
                await page.wait_for_timeout(1500)
                break

            # If not submitted, try Next step
            if await click_next(page):
                print("[Agent] Clicked Next/Continue button.")
                await page.wait_for_timeout(1000)
                await scroll_page(page)
                continue
            else:
                # No next button and no submit button found
                break

        final_text = (await get_page_text(page)).lower()
        confirmed = any(p in final_text for p in [
            "application submitted",
            "application received",
            "thank you for applying",
            "thanks for applying",
            "applied",
        print("\n[Agent] Application fields successfully populated! Keeping browser open on screen for review (25s)...")
        try:
            await page.wait_for_timeout(25000)
        except Exception:
            pass

        return {
            "status": "completed" if (submitted or confirmed) else "ready_for_review",
            "submitted": submitted or confirmed,
            "confirmed": confirmed,
            "job_url": page.url,
            "message": "Application completed successfully!" if (submitted or confirmed) else "Application form fields populated and ready for review."
        }

    except Exception as error:
        print(f"[Agent] Error during application: {error}")
        return {
            "status": "failed",
            "job_url": job_url,
            "error": str(error)
        }
    finally:
        try:
            if browser:
                await browser.close()
        finally:
            if playwright:
                await playwright.stop()



async def run_application():
    job_url = input("\nPaste the job application URL: ").strip()
    if not job_url:
        print("No URL provided.")
        return
    res = await apply_to_job(job_url, candidate_profile=profile, interactive=True)
    print("\nResult:", res)


if __name__ == "__main__":
    asyncio.run(run_application())