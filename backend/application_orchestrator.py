import os
import asyncio
from typing import Dict, Any, List, Optional
from models import ApplicationStatus, AgentSettings, QuestionCategory
from profile_service import (
    normalize_to_candidate_profile,
    get_profile_field_value
)
from field_detector import inspect_field_context
from question_classifier import classify_field
from job_context_service import extract_job_context
from answer_generator import generate_application_answer
from answer_validator import validate_and_refine_answer
from answer_cache import get_cached_or_adapted_answer, cache_application_answer
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
import db


async def orchestrate_application(
    job_url: str,
    candidate_profile: Any = None,
    resume_path: Optional[str] = None,
    job_data: Optional[Dict[str, Any]] = None,
    application_id: Optional[int] = None,
    settings: Optional[AgentSettings] = None
) -> Dict[str, Any]:
    """
    Main autonomous Application Orchestrator.
    Decouples browser interaction, question classification, candidate profile lookup,
    and LLM answer generation into a scalable, testable pipeline.
    """
    if not job_url or not job_url.startswith("http"):
        return {
            "status": ApplicationStatus.FAILED.value,
            "error": "A valid HTTP job application URL is required."
        }

    # Load active profile and settings if not provided
    if candidate_profile is None:
        candidate_obj, r_path, _ = db.get_active_profile()
        candidate = normalize_to_candidate_profile(candidate_obj)
        if not resume_path:
            resume_path = r_path
    else:
        candidate = normalize_to_candidate_profile(candidate_profile)

    if settings is None:
        settings = db.get_agent_settings()

    # Consolidate job context
    job_ctx = extract_job_context(job_data=job_data, job_url=job_url)

    steps_log: List[str] = []
    filled_fields: List[Dict[str, Any]] = []
    skipped_sensitive_fields: List[Dict[str, Any]] = []

    playwright = None
    browser = None
    page = None

    try:
        print(f"\n[Orchestrator] Launching visible Chromium session for: {job_url}")
        steps_log.append(f"Opened employer application page: {job_url}")

        playwright, browser, page = await open_browser(job_url, headless=False)
        print(f"[Orchestrator] Loaded page: {page.url}")

        # Trigger dynamic elements
        await scroll_page(page)

        # 1. Click Apply button to expand application form if on landing posting
        apply_clicked = await click_apply(page)
        if apply_clicked:
            steps_log.append("Activated application form container")
            await page.wait_for_timeout(1000)
            await scroll_page(page)

        # 2. Upload PDF resume if available
        if resume_path and os.path.isfile(resume_path):
            print(f"[Orchestrator] Attaching resume from {resume_path}...")
            uploaded = await upload_resume(page, resume_path)
            if uploaded:
                steps_log.append("Uploaded candidate PDF resume")
                print("  [OK] Resume uploaded successfully")

        # 3. Multi-step form filling loop
        max_steps = 4
        step = 0

        while step < max_steps:
            step += 1
            print(f"\n[Orchestrator] Inspecting form fields (Step {step})...")

            raw_fields = await get_application_fields(page)
            page_text = await page.evaluate("() => document.body ? document.body.innerText.substring(0, 8000) : ''")
            job_ctx = extract_job_context(job_data=job_data, job_url=page.url, page_text=page_text)

            if raw_fields:
                print(f"[Orchestrator] Found {len(raw_fields)} form elements on page.")

                for raw_field in raw_fields:
                    field_context = inspect_field_context(raw_field)
                    q_text = field_context.get("question") or "Field"

                    # Classify field
                    classification = classify_field(field_context, use_llm_fallback=False)

                    # A. Sensitive / Legal Declaration
                    if classification.is_sensitive:
                        print(f"  [Sensitive] Skipping legal/sensitive question: {q_text[:40]}")
                        skipped_sensitive_fields.append({
                            "name": q_text,
                            "type": field_context.get("type"),
                            "reason": classification.explanation
                        })
                        if application_id:
                            db.save_application_field(
                                application_id=application_id,
                                field_name=field_context.get("name") or q_text,
                                question=q_text,
                                detected_type=classification.category.value,
                                source="SENSITIVE_SKIPPED",
                                generated_answer="",
                                filled_successfully=False,
                                error=classification.explanation
                            )
                        continue

                    # B. Structured Candidate Profile Field
                    if classification.can_be_filled_from_profile and classification.profile_key:
                        profile_val = get_profile_field_value(candidate, classification.profile_key)
                        if profile_val:
                            await fill_field(page, field_context["index"], profile_val)
                            filled_fields.append({
                                "field": q_text,
                                "type": classification.category.value,
                                "source": "PROFILE",
                                "value": str(profile_val)[:50]
                            })
                            print(f"  [Profile] Filled [{q_text}]: {str(profile_val)[:30]}")
                            if application_id:
                                db.save_application_field(
                                application_id=application_id,
                                field_name=field_context.get("name") or q_text,
                                question=q_text,
                                detected_type=classification.category.value,
                                source="PROFILE",
                                generated_answer=str(profile_val),
                                filled_successfully=True
                            )
                            continue

                    # C. Descriptive / Open-ended Question requiring LLM
                    if classification.requires_llm:
                        if not settings.auto_answer_descriptive:
                            print(f"  [Notice] Auto-answer disabled in settings. Skipping: {q_text[:35]}")
                            if application_id:
                                db.save_application_field(
                                    application_id=application_id,
                                    field_name=field_context.get("name") or q_text,
                                    question=q_text,
                                    detected_type=classification.category.value,
                                    source="SKIPPED_BY_SETTING",
                                    generated_answer="",
                                    filled_successfully=False
                                )
                            continue

                        # Check answer cache
                        cached_ans = get_cached_or_adapted_answer(
                            question=q_text,
                            company=job_ctx.get("company", ""),
                            job_title=job_ctx.get("title", ""),
                            question_type=classification.category.value
                        )

                        if cached_ans:
                            print(f"  [Cache] Reusing cached answer for [{q_text[:35]}]")
                            final_ans = validate_and_refine_answer(cached_ans, field_context=field_context)
                            source_tag = "CACHE"
                        else:
                            print(f"  [LLM Agent] Generating truthful answer for: {q_text[:40]}...")
                            final_ans = generate_application_answer(
                                question=q_text,
                                candidate_profile=candidate,
                                job_context=job_ctx,
                                question_category=classification.category,
                                field_context=field_context,
                                default_max_words=settings.max_answer_words
                            )
                            source_tag = "LLM"
                            # Cache answer for reuse
                            cache_application_answer(
                                question=q_text,
                                answer=final_ans,
                                question_type=classification.category.value,
                                job_id=job_ctx.get("id", ""),
                                company=job_ctx.get("company", "")
                            )

                        if final_ans:
                            await fill_field(page, field_context["index"], final_ans)
                            filled_fields.append({
                                "field": q_text,
                                "type": classification.category.value,
                                "source": source_tag,
                                "value": final_ans[:60] + "..."
                            })
                            print(f"  [OK] AI filled [{q_text[:25]}]: {final_ans[:40]}...")
                            if application_id:
                                db.save_application_field(
                                    application_id=application_id,
                                    field_name=field_context.get("name") or q_text,
                                    question=q_text,
                                    detected_type=classification.category.value,
                                    source=source_tag,
                                    generated_answer=final_ans,
                                    filled_successfully=True
                                )
                        continue

                    # D. Unknown or untyped field
                    if application_id:
                        db.save_application_field(
                            application_id=application_id,
                            field_name=field_context.get("name") or q_text,
                            question=q_text,
                            detected_type="UNKNOWN",
                            source="UNKNOWN",
                            generated_answer="",
                            filled_successfully=False
                        )

            # Check if there is a 'Next' / 'Continue' multi-step button (NEVER clicks Submit)
            clicked_next = await click_next_step_only(page)
            if clicked_next:
                print("[Orchestrator] Clicked Next to advance multi-step application form...")
                steps_log.append("Advanced to next step of multi-step application form")
                await page.wait_for_timeout(1000)
                await scroll_page(page)
            else:
                break

        # Injects friendly floating review banner onto the real employer page
        try:
            await page.evaluate("""
                () => {
                    if (document.getElementById('jobmate-review-banner')) return;
                    const banner = document.createElement('div');
                    banner.id = 'jobmate-review-banner';
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
                    banner.innerText = '✨ AI filled the application using your candidate profile. Please review and submit.';
                    document.body.appendChild(banner);
                }
            """)
        except Exception:
            pass

        steps_log.append("Form populated. Browser paused at READY_FOR_REVIEW.")
        print("\n[Orchestrator] Application filled successfully. Pausing at READY_FOR_REVIEW.")

        return {
            "status": ApplicationStatus.READY_FOR_REVIEW.value,
            "job_url": page.url,
            "message": "AI filled the application on the employer's website. Review and click Submit when ready.",
            "steps_log": steps_log,
            "filled_fields": filled_fields,
            "skipped_sensitive_fields": skipped_sensitive_fields,
            "total_filled": len(filled_fields),
            "total_skipped": len(skipped_sensitive_fields)
        }

    except Exception as error:
        print(f"[Orchestrator] Error during application execution: {error}")
        return {
            "status": ApplicationStatus.FAILED.value,
            "job_url": job_url,
            "error": str(error),
            "steps_log": steps_log,
            "filled_fields": filled_fields,
            "skipped_sensitive_fields": skipped_sensitive_fields
        }
