# backend/app/repositories/application_repository.py
import json
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.models.application import ApplicationStatus, AgentSettings, ApplicationSession


class ApplicationRepository:
    def create_application(
        self,
        job_url: str,
        user_id: str = "user_default",
        job_title: str = "",
        company: str = "",
        apply_url: str = "",
        job_id: str = "",
        status: str = "APPLY_STARTED",
        settings: Optional[Dict[str, Any]] = None,
        result: Any = None
    ) -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            result_json = json.dumps(result, ensure_ascii=False) if result is not None else "{}"
            settings_json = json.dumps(settings, ensure_ascii=False) if settings is not None else "{}"

            cursor.execute("""
                INSERT INTO applications (user_id, job_id, job_title, company, job_url, apply_url, status, result_json, settings_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, job_id, job_title, company, job_url, apply_url or job_url, status, result_json, settings_json))
            app_id = cursor.lastrowid
            conn.commit()
            return app_id

    def update_application(
        self,
        app_id: int,
        status: str,
        result: Any = None,
        error_message: Optional[str] = None
    ):
        with get_db() as conn:
            cursor = conn.cursor()
            result_json = json.dumps(result, ensure_ascii=False) if result is not None else "{}"

            cursor.execute("""
                UPDATE applications
                SET status = ?, result_json = ?, error_message = ?
                WHERE id = ?
            """, (status, result_json, error_message, app_id))
            conn.commit()

    def get_applications(self, user_id: str = "user_default", limit: int = 50) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM applications
                WHERE user_id = ? OR user_id = 'user_default'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()

            result = []
            for row in rows:
                r_dict = dict(row)
                try:
                    res_data = json.loads(r_dict["result_json"]) if r_dict.get("result_json") else {}
                except Exception:
                    res_data = {}

                try:
                    sett_data = json.loads(r_dict["settings_json"]) if r_dict.get("settings_json") else {}
                except Exception:
                    sett_data = {}

                result.append({
                    "id": r_dict.get("id"),
                    "user_id": r_dict.get("user_id", "user_default"),
                    "job_id": r_dict.get("job_id", ""),
                    "job_url": r_dict.get("job_url", ""),
                    "apply_url": r_dict.get("apply_url", ""),
                    "job_title": r_dict.get("job_title", ""),
                    "company": r_dict.get("company", ""),
                    "status": r_dict.get("status", "APPLY_STARTED"),
                    "result": res_data,
                    "settings": sett_data,
                    "error_message": r_dict.get("error_message"),
                    "timestamp": r_dict.get("timestamp")
                })
            return result

    def get_by_id(self, app_id: int) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE id = ? LIMIT 1", (app_id,))
            row = cursor.fetchone()
            if not row:
                return None
            r_dict = dict(row)
            try:
                res_data = json.loads(r_dict["result_json"]) if r_dict.get("result_json") else {}
            except Exception:
                res_data = {}
            return {
                "id": r_dict.get("id"),
                "user_id": r_dict.get("user_id", "user_default"),
                "job_id": r_dict.get("job_id", ""),
                "job_url": r_dict.get("job_url", ""),
                "apply_url": r_dict.get("apply_url", ""),
                "job_title": r_dict.get("job_title", ""),
                "company": r_dict.get("company", ""),
                "status": r_dict.get("status", "APPLY_STARTED"),
                "result": res_data,
                "timestamp": r_dict.get("timestamp")
            }

    def save_application_field(
        self,
        application_id: int,
        field_name: str,
        question: str,
        detected_type: str,
        source: str = "PROFILE",
        generated_answer: str = "",
        filled_successfully: bool = True,
        error: Optional[str] = None
    ) -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO application_fields (
                    application_id, field_name, question, detected_type, source,
                    generated_answer, filled_successfully, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                application_id,
                field_name[:200],
                question[:500],
                detected_type,
                source,
                generated_answer,
                1 if filled_successfully else 0,
                error
            ))
            field_id = cursor.lastrowid
            conn.commit()
            return field_id

    def get_application_fields(self, application_id: int) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM application_fields
                WHERE application_id = ?
                ORDER BY id ASC
            """, (application_id,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "application_id": r["application_id"],
                    "field_name": r["field_name"],
                    "question": r["question"],
                    "detected_type": r["detected_type"],
                    "source": r["source"],
                    "generated_answer": r["generated_answer"],
                    "filled_successfully": bool(r["filled_successfully"]),
                    "error": r["error"],
                    "created_at": r["created_at"]
                }
                for r in rows
            ]

    def get_agent_settings(self, user_id: str = "user_default") -> AgentSettings:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_settings WHERE user_id = ? LIMIT 1", (user_id,))
            row = cursor.fetchone()
            if not row:
                return AgentSettings(user_id=user_id)
            return AgentSettings(
                user_id=row["user_id"],
                auto_answer_descriptive=bool(row["auto_answer_descriptive"]),
                auto_submit=bool(row["auto_submit"]),
                preferred_model=row["preferred_model"] or "openai/gpt-oss-120b",
                max_answer_words=row["max_answer_words"] or 150
            )

    def save_agent_settings(self, settings: AgentSettings, user_id: str = "user_default") -> AgentSettings:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_settings (
                    user_id, auto_answer_descriptive, auto_submit, preferred_model,
                    max_answer_words, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                user_id,
                1 if settings.auto_answer_descriptive else 0,
                1 if settings.auto_submit else 0,
                settings.preferred_model,
                settings.max_answer_words
            ))
            conn.commit()
            return settings

    def update_agent_settings(self, user_id: str, settings_dict: Dict[str, Any]) -> AgentSettings:
        curr = self.get_agent_settings(user_id)
        if "auto_answer_descriptive" in settings_dict:
            curr.auto_answer_descriptive = bool(settings_dict["auto_answer_descriptive"])
        if "auto_submit" in settings_dict:
            curr.auto_submit = bool(settings_dict["auto_submit"])
        if "preferred_model" in settings_dict:
            curr.preferred_model = str(settings_dict["preferred_model"])
        if "max_answer_words" in settings_dict:
            curr.max_answer_words = int(settings_dict["max_answer_words"])
        return self.save_agent_settings(curr, user_id)

    def get_user_applications(self, user_id: str = "user_default", limit: int = 50, offset: int = 0) -> List[ApplicationSession]:
        raw_list = self.get_applications(user_id=user_id, limit=limit + offset)
        sliced = raw_list[offset:offset + limit]
        return [
            ApplicationSession(
                id=str(r["id"]),
                user_id=r["user_id"],
                job_id=r.get("job_id") or "",
                status=ApplicationStatus.SUBMITTED if "SUBMIT" in r.get("status", "").upper() else (ApplicationStatus.FAILED if "FAIL" in r.get("status", "").upper() else ApplicationStatus.IN_PROGRESS),
                error_message=r.get("error_message"),
                created_at=r.get("timestamp") or "",
            )
            for r in sliced
        ]

    def get_application(self, application_id: str) -> Optional[ApplicationSession]:
        try:
            app_num = int(application_id)
        except ValueError:
            return None
        raw = self.get_by_id(app_num)
        if not raw:
            return None
        return ApplicationSession(
            id=str(raw["id"]),
            user_id=raw["user_id"],
            job_id=raw.get("job_id") or "",
            status=ApplicationStatus.SUBMITTED if "SUBMIT" in raw.get("status", "").upper() else (ApplicationStatus.FAILED if "FAIL" in raw.get("status", "").upper() else ApplicationStatus.IN_PROGRESS),
            error_message=raw.get("error_message"),
            created_at=raw.get("timestamp") or "",
        )

    def update_application_status(self, application_id: str, status: Any, error: Optional[str] = None):
        try:
            app_num = int(application_id)
        except ValueError:
            return
        status_str = status.value if hasattr(status, "value") else str(status)
        self.update_application(app_id=app_num, status=status_str, error_message=error)

    def save_field_record(self, record: Any):
        if hasattr(record, "application_id"):
            app_id = int(record.application_id) if str(record.application_id).isdigit() else 1
            field_name = getattr(record, "field_name", "")
            field_label = getattr(record, "field_label", "")
            field_type = getattr(record, "field_type", "text")
            source = getattr(record, "source", "PROFILE")
            value = getattr(record, "filled_value", "")
            status = getattr(record, "status", "FILLED")
            error = getattr(record, "error", None)
            self.save_application_field(
                application_id=app_id,
                field_name=field_name,
                question=field_label,
                detected_type=field_type,
                source=source,
                generated_answer=value,
                filled_successfully=(status == "FILLED"),
                error=error
            )


application_repo = ApplicationRepository()
app_repo = application_repo
