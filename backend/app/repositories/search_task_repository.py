# backend/app/repositories/search_task_repository.py
import json
from typing import Optional, Dict, Any, List
from app.core.database import get_db
from app.models.search_task import SearchTask, TaskStatus


class SearchTaskRepository:
    def create_task(self, task: Any, user_id: str = "user_default", target_role: str = "", target_location: str = "") -> SearchTask:
        if isinstance(task, SearchTask):
            task_obj = task
        else:
            task_obj = SearchTask(
                task_id=str(task),
                user_id=user_id,
                target_role=target_role,
                target_location=target_location,
                status=TaskStatus.QUEUED,
            )

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (id, name, email) VALUES (?, ?, ?)", (task_obj.user_id, task_obj.user_id, f"{task_obj.user_id}@example.com"))
            cursor.execute("""
                INSERT INTO search_tasks (task_id, user_id, target_role, target_location, status, progress, total_found, result_job_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, '[]')
            """, (task_obj.task_id, task_obj.user_id, task_obj.target_role or task_obj.query, task_obj.target_location, task_obj.status.value, task_obj.progress, task_obj.total_found))
            conn.commit()
            return task_obj

    def update_progress(
        self,
        task_id: str,
        status: TaskStatus,
        progress: int,
        stage: str = "",
        message: str = "",
        total_found: int = 0,
        result_job_ids: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        with get_db() as conn:
            cursor = conn.cursor()
            job_ids_json = json.dumps(result_job_ids or [], ensure_ascii=False)
            cursor.execute("""
                UPDATE search_tasks
                SET status = ?, progress = ?, total_found = ?, result_job_ids = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = ?
            """, (status.value if hasattr(status, "value") else str(status), progress, total_found, job_ids_json, error, task_id))
            conn.commit()

    def update_task_progress(self, *args, **kwargs):
        return self.update_progress(*args, **kwargs)

    def get_task(self, task_id: str) -> Optional[SearchTask]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM search_tasks WHERE task_id = ? LIMIT 1", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            try:
                job_ids = json.loads(row["result_job_ids"]) if row["result_job_ids"] else []
            except Exception:
                job_ids = []

            status_str = row["status"]
            try:
                status_enum = TaskStatus(status_str)
            except ValueError:
                status_enum = TaskStatus.PENDING

            return SearchTask(
                task_id=row["task_id"],
                user_id=row["user_id"],
                target_role=row["target_role"],
                target_location=row["target_location"],
                status=status_enum,
                progress=row["progress"],
                total_found=row["total_found"],
                error_message=row["error_message"],
                error=row["error_message"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )


search_task_repo = SearchTaskRepository()
