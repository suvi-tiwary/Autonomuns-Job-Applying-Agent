"""
Application Orchestrator - End-to-End Playwright Automation Agent
Executes browser automation, form field detection, question answering,
resume attachment, and field trace recording for candidate applications.
"""

import os
import time
from typing import Dict, Any, Optional, List, Callable
from app.core.logging import get_logger
from app.core.config import settings
from app.models.application import (
    ApplicationSession,
    ApplicationStatus,
    ApplicationFieldRecord,
    AgentSettings,
    QuestionCategory,
)
from app.models.profile import CandidateProfile
from app.models.job import JobSchema
from app.repositories.application_repository import ApplicationRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.job_repository import JobRepository
from app.agents.question_agent import QuestionAgent
from app.services.profile_service import ProfileService
from app.integrations.browser.playwright_adapter import PlaywrightAdapter
from app.integrations.browser.field_detector import FieldDetector

logger = get_logger(__name__)


class ApplicationOrchestrator:
    """
    Coordinates Playwright browser lifecycle, form extraction, question generation,
    field entry, and application state transitions.
    """

    def __init__(
        self,
        app_repo: Optional[ApplicationRepository] = None,
        profile_repo: Optional[ProfileRepository] = None,
        job_repo: Optional[JobRepository] = None,
        question_agent: Optional[QuestionAgent] = None,
        profile_service: Optional[ProfileService] = None,
    ):
        self.app_repo = app_repo or ApplicationRepository()
        self.profile_repo = profile_repo or ProfileRepository()
        self.job_repo = job_repo or JobRepository()
        self.question_agent = question_agent or QuestionAgent()
        self.profile_service = profile_service or ProfileService(self.profile_repo)
        self.detector = FieldDetector()

    def run_application(
        self,
        user_id: str,
        application_id: str,
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the autonomous application workflow in Playwright.
        """
        app_session = self.app_repo.get_application(application_id)
        if not app_session:
            logger.error(f"Application session {application_id} not found.")
            return {"success": False, "error": "Application session not found"}

        profile = self.profile_repo.get_profile(user_id)
        job = self.job_repo.get_job_by_id(app_session.job_id)
        agent_settings = self.app_repo.get_agent_settings(user_id)

        if not job or not job.application_url:
            self.app_repo.update_application_status(
                application_id, ApplicationStatus.FAILED, error="Invalid job application URL"
            )
            return {"success": False, "error": "Invalid job application URL"}

        def notify(stage: str, percent: int, msg: str):
            if progress_callback:
                progress_callback(stage, percent, msg)
            logger.info(f"[{application_id}] ({percent}%) {stage}: {msg}")

        # Update initial status
        self.app_repo.update_application_status(
            application_id, ApplicationStatus.IN_PROGRESS
        )
        notify("INITIALIZING", 10, f"Starting automation for {job.company} - {job.title}")

        browser_adapter = PlaywrightAdapter(
            headless=agent_settings.headless_mode,
            slow_mo=agent_settings.typing_speed_delay_ms,
        )

        try:
            # 1. Start visible browser
            if not browser_adapter.start():
                raise RuntimeError("Failed to launch Playwright browser instance.")

            # 2. Navigate to application URL
            notify("NAVIGATING", 25, f"Opening application portal: {job.application_url}")
            nav_ok = browser_adapter.navigate(job.application_url)
            if not nav_ok:
                raise RuntimeError(f"Could not load application page {job.application_url}")

            # 3. Detect and extract form fields
            notify("ANALYZING_PAGE", 40, "Scanning form fields, labels, and constraints...")
            raw_fields = browser_adapter.extract_form_fields()
            classified_fields = self.detector.detect_fields_with_context(raw_fields)

            notify("FILLING_FORM", 50, f"Found {len(classified_fields)} form elements. Answering fields...")

            filled_count = 0
            for idx, field in enumerate(classified_fields):
                field_id = field.get("id") or field.get("name") or f"field_{idx}"
                field_name = field.get("name") or field.get("label") or "Field"
                label_text = field.get("label") or field_name
                category = field.get("category") or QuestionCategory.CUSTOM
                field_type = field.get("type", "text")

                # Handle File Upload (Resume)
                if field_type == "file" or "resume" in label_text.lower() or "cv" in label_text.lower():
                    resume_path = profile.personal.resume_url or os.path.join(settings.UPLOAD_DIR, f"{user_id}_resume.pdf")
                    if os.path.exists(resume_path):
                        notify("ATTACHING_RESUME", 65, f"Attaching candidate resume: {os.path.basename(resume_path)}")
                        success = browser_adapter.upload_file(field.get("selector", "input[type='file']"), resume_path)
                        self._record_field_trace(
                            application_id=application_id,
                            field_name=field_name,
                            field_label=label_text,
                            field_type=field_type,
                            category=category,
                            value=os.path.basename(resume_path),
                            source="resume_attachment",
                            status="FILLED" if success else "FAILED",
                        )
                        if success:
                            filled_count += 1
                    continue

                # Generate Answer
                answer_value, confidence, source = self.question_agent.generate_answer(
                    user_id=user_id,
                    question_text=label_text,
                    category=category,
                    profile=profile,
                    job_title=job.title,
                    company_name=job.company,
                    job_description=job.description,
                    max_length=field.get("maxlength"),
                    max_words=field.get("max_words"),
                    options=field.get("options", []),
                )

                # Fill field in browser
                selector = field.get("selector") or f"#{field.get('id')}"
                fill_ok = browser_adapter.fill_field(
                    selector=selector,
                    value=answer_value,
                    field_type=field_type,
                )

                # Record field trace
                self._record_field_trace(
                    application_id=application_id,
                    field_name=field_name,
                    field_label=label_text,
                    field_type=field_type,
                    category=category,
                    value=answer_value,
                    source=source,
                    confidence=confidence,
                    status="FILLED" if fill_ok else "FAILED",
                )

                if fill_ok:
                    filled_count += 1

                step_percent = 50 + int((idx / max(1, len(classified_fields))) * 35)
                notify("FILLING_FORM", step_percent, f"Filled '{label_text[:30]}' ({idx+1}/{len(classified_fields)})")

            # 4. Determine final submission / review state
            notify("COMPLETING", 90, f"Completed filling {filled_count} fields.")

            if agent_settings.auto_submit_enabled:
                notify("SUBMITTING", 95, "Auto-submit enabled. Submitting application form...")
                submit_ok = browser_adapter.click_submit()
                if submit_ok:
                    self.app_repo.update_application_status(
                        application_id, ApplicationStatus.SUBMITTED
                    )
                    notify("COMPLETED", 100, "Application successfully submitted!")
                else:
                    self.app_repo.update_application_status(
                        application_id, ApplicationStatus.READY_FOR_REVIEW
                    )
                    notify("REVIEW_READY", 100, "Form filled. Ready for manual final click/review.")
            else:
                self.app_repo.update_application_status(
                    application_id, ApplicationStatus.READY_FOR_REVIEW
                )
                notify("REVIEW_READY", 100, "Form filled cleanly. Ready for candidate review!")

            # Allow user to view the completed form for a few seconds if visual mode is on
            time.sleep(3)

            return {
                "success": True,
                "application_id": application_id,
                "filled_fields": filled_count,
                "total_fields": len(classified_fields),
                "status": "READY_FOR_REVIEW" if not agent_settings.auto_submit_enabled else "SUBMITTED",
            }

        except Exception as e:
            logger.error(f"Application execution failed for {application_id}: {e}", exc_info=True)
            self.app_repo.update_application_status(
                application_id, ApplicationStatus.FAILED, error=str(e)
            )
            notify("ERROR", 100, f"Application failed: {str(e)}")
            return {"success": False, "error": str(e)}

        finally:
            # Clean up browser
            browser_adapter.close()

    def _record_field_trace(
        self,
        application_id: str,
        field_name: str,
        field_label: str,
        field_type: str,
        category: QuestionCategory,
        value: str,
        source: str,
        confidence: float = 1.0,
        status: str = "FILLED",
    ):
        """Logs a single field action into application_fields."""
        record = ApplicationFieldRecord(
            application_id=application_id,
            field_name=field_name,
            field_label=field_label,
            field_type=field_type,
            category=category,
            filled_value=value,
            confidence=confidence,
            source=source,
            status=status,
        )
        self.app_repo.save_field_record(record)
