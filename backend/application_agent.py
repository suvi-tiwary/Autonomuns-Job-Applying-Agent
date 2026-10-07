import os
import re
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from pypdf import PdfReader

from browser_agent import (
    open_browser,
    scroll_page,
    detect_login_required,
    detect_captcha,
    get_application_fields,
    fill_field,
    upload_resume,
    click_apply,
    click_next_step_only
)
from field_mapper import (
    detect_profile_field,
    is_sensitive_question,
    is_descriptive_question
)
from llm_answer import generate_answer
from models import ApplicationStatus


def extract_resume_text(file_path: str) -> str:
    if not file_path or not os.path.isfile(file_path):
        return ""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting resume text: {e}")
        return ""


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
    Automated application agent that:
    1. Opens the REAL employer application page in visible Chromium.
    2. Interacts with the real employer DOM.
    3. Fills standard profile fields & uploads resume.
    4. Generates truthful answers for safe role questions.
    5. Skips sensitive/legal questions for user review.
    6. NEVER SUBMITS - pauses and leaves browser open at READY_FOR_REVIEW.
    """
    if not job_url or not job_url.startswith("http"):
        return {
            "status": ApplicationStatus.FAILED.value,
            "error": "Valid HTTP job URL is required."
        }

    active_profile = dict(candidate_profile or {})
    # Parse names
    full_name = active_profile.get("name") or active_profile.get("full_name") or ""
    if full_name:
        active_profile["full_name"] = full_name.strip()
        parts = full_name.strip().split()
        if not active_profile.get("first_name"):
            active_profile["first_name"] = parts[0]
        if not active_profile.get("last_name"):
            active_profile["last_name"] = " ".join(parts[1:]) if len(parts) > 1 else ""

    if isinstance(active_profile.get("skills"), list):
        active_profile["skills_str"] = ", ".join(active_profile["skills"])

    resume_text = extract_resume_text(resume_path) if resume_path else ""

    playwright = None
    browser = None
    page = None

    filled_fields = []
    skipped_sensitive_fields = []
    steps_log = []

    try:
        print(f"\n[Agent] Opening REAL employer job page: {job_url}")
        steps_log.append(f"Opened real employer page: {job_url}")
        
        # Always launch visible Chromium so user sees real page automation
        playwright, browser, page = await open_browser(job_url, headless=False)
        print(f"[Agent] Loaded employer page: {page.url}")

        # Trigger dynamic elements
        await scroll_page(page)

        # 1. Look for Apply / Easy Apply button on real ATS page
        apply_clicked = await click_apply(page)
        if apply_clicked:
            print("[Agent] Clicked Apply on employer page to reveal form.")
            steps_log.append("Clicked Apply to reveal form")
            await page.wait_for_timeout(1200)
            await scroll_page(page)

        # 2. Upload Resume if available
        if resume_path and os.path.isfile(resume_path):
            print("[Agent] Uploading resume to employer form...")
            uploaded = await upload_resume(page, resume_path)
            if uploaded:
                print("[Agent] Resume attached successfully [OK]")
                steps_log.append("Uploaded candidate PDF resume")

        # 5. Multi-step form filling loop
        max_steps = 4
        step = 0

        while step < max_steps:
            step += 1
            print(f"\n[Agent] Scanning and populating form fields (Step {step})...")

            fields = await get_application_fields(page)
            job_context = (await page.evaluate("() => document.body ? document.body.innerText.substring(0, 10000) : ''"))

            if fields:
                print(f"[Agent] Found {len(fields)} interactive fields on page.")
                for field in fields:
                    field_label = field.get("label") or field.get("name") or field.get("placeholder") or "Field"

                    # Check if sensitive / legal question
                    if is_sensitive_question(field):
                        print(f"  [Sensitive] Skipping sensitive/legal question for user review: {field_label[:40]}")
                        skipped_sensitive_fields.append({
                            "name": field_label,
                            "type": field.get("type"),
                            "reason": "Requires manual applicant verification / legal consent"
                        })
                        continue

                    # Standard profile field match
                    match_key = detect_profile_field(field)
                    if match_key and active_profile.get(match_key):
                        val = _format_field_value(active_profile[match_key])
                        await fill_field(page, field["index"], val)
                        filled_fields.append({"field": field_label, "value": val[:40]})
                        print(f"  [OK] Filled [{field_label}]: {val[:30]}")
                        continue

                    # Safe motivational / role question
                    if is_descriptive_question(field):
                        print(f"  [AI] Generating truthful answer for: {field_label[:40]}...")
                        answer = generate_answer(
                            question=field_label,
                            profile=active_profile,
                            resume_text=resume_text,
                            job_context=job_context
                        )
                        if answer:
                            await fill_field(page, field["index"], answer)
                            filled_fields.append({"field": field_label, "value": answer[:60] + "..."})
                            print(f"  [OK] AI filled [{field_label[:25]}]")
                        continue

            # Check if there is a 'Next' / 'Continue' multi-step button (NEVER clicks Submit)
            clicked_next = await click_next_step_only(page)
            if clicked_next:
                print("[Agent] Clicked Next to advance multi-step application...")
                steps_log.append("Advanced to next step of multi-step application")
                await page.wait_for_timeout(1000)
                await scroll_page(page)
            else:
                break

        # Injects floating review banner onto the real employer page
        try:
            await page.evaluate("""
                () => {
                    if (document.getElementById('ai-agent-banner')) return;
                    const banner = document.createElement('div');
                    banner.id = 'ai-agent-banner';
                    banner.style.position = 'fixed';
                    banner.style.top = '12px';
                    banner.style.left = '50%';
                    banner.style.transform = 'translateX(-50%)';
                    banner.style.background = 'linear-gradient(135deg, #10ac84, #05c46b)';
                    banner.style.color = '#fff';
                    banner.style.padding = '12px 28px';
                    banner.style.borderRadius = '30px';
                    banner.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.4)';
                    banner.style.fontSize = '14px';
                    banner.style.fontWeight = 'bold';
                    banner.style.zIndex = '99999999';
                    banner.style.fontFamily = 'system-ui, -apple-system, sans-serif';
                    banner.innerText = '✨ AI filled the application using your profile. Review everything on this page before submitting.';
                    document.body.appendChild(banner);
                }
            """)
        except Exception:
            pass

        steps_log.append("Form populated. Paused at READY_FOR_REVIEW for applicant manual submission.")
        print("\n[Agent] Automation complete: Application is filled on the REAL employer page.")
        print("[Agent] Pausing at READY_FOR_REVIEW. Please review and click Submit in the open browser.")

        return {
            "status": ApplicationStatus.READY_FOR_REVIEW.value,
            "job_url": page.url,
            "message": "AI filled the application on the employer's website. Review and click Submit when ready.",
            "steps_log": steps_log,
            "filled_fields": filled_fields,
            "skipped_sensitive_fields": skipped_sensitive_fields
        }

    except Exception as error:
        print(f"[Agent] Error during application: {error}")
        return {
            "status": ApplicationStatus.FAILED.value,
            "job_url": job_url,
            "error": str(error),
            "steps_log": steps_log,
            "filled_fields": filled_fields,
            "skipped_sensitive_fields": skipped_sensitive_fields
        }
    # Notice: browser is intentionally NOT closed so user can inspect and submit on the real website!