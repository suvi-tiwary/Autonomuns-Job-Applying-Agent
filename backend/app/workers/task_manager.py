"""
Task Manager - Production-ready Async Background Worker Architecture
Executes long-running tasks (Job Searches, Playwright Applications) concurrently in background threads.
Provides task state tracking, progress monitoring, and clean abstraction for future Redis/Celery integration.
"""

import threading
import uuid
import time
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from app.core.logging import get_logger
from app.models.search_task import SearchTask, TaskStatus
from app.repositories.search_task_repository import SearchTaskRepository

logger = get_logger(__name__)


class TaskManager:
    """
    Central background task manager supporting async job searches and application runs.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, max_workers: int = 6):
        if self._initialized:
            return
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="agent_worker")
        self.task_repo = SearchTaskRepository()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self._initialized = True
        logger.info(f"TaskManager initialized with {max_workers} background worker threads.")

    def submit_job_search(
        self,
        user_id: str,
        query: str,
        target_roles: list,
        search_fn: Callable[[str, str, list, Callable[[str, int, str], None]], Any],
    ) -> str:
        """
        Creates a SearchTask record and submits the search to the background thread pool.
        """
        task_id = str(uuid.uuid4())
        task = SearchTask(
            task_id=task_id,
            user_id=user_id,
            query=query,
            status=TaskStatus.QUEUED,
            progress=0,
            stage="QUEUED",
            message="Job search queued...",
        )
        self.task_repo.create_task(task)

        def runner():
            try:
                self.task_repo.update_progress(
                    task_id=task_id,
                    status=TaskStatus.RUNNING,
                    progress=5,
                    stage="STARTED",
                    message="Initializing multi-source search...",
                )

                def callback(stage: str, percent: int, msg: str):
                    self.task_repo.update_progress(
                        task_id=task_id,
                        status=TaskStatus.RUNNING,
                        progress=percent,
                        stage=stage,
                        message=msg,
                    )

                results = search_fn(user_id, query, target_roles, callback)

                self.task_repo.update_progress(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    stage="FINISHED",
                    message=f"Discovered and ranked {len(results)} high-quality job postings.",
                    total_found=len(results),
                )
                logger.info(f"Search task {task_id} completed with {len(results)} jobs.")

            except Exception as e:
                logger.error(f"Search task {task_id} failed: {e}", exc_info=True)
                self.task_repo.update_progress(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    progress=100,
                    stage="ERROR",
                    message=str(e),
                    error=str(e),
                )

        self.executor.submit(runner)
        return task_id

    def submit_application(
        self,
        user_id: str,
        application_id: str,
        apply_fn: Callable[[str, str, Callable[[str, int, str], None]], Any],
    ) -> str:
        """
        Submits a Playwright autonomous application task to the background thread pool.
        """
        self.active_tasks[application_id] = {
            "application_id": application_id,
            "user_id": user_id,
            "status": "QUEUED",
            "progress": 0,
            "stage": "QUEUED",
            "message": "Application task queued...",
            "created_at": time.time(),
        }

        def runner():
            try:
                self.active_tasks[application_id]["status"] = "RUNNING"
                self.active_tasks[application_id]["progress"] = 5
                self.active_tasks[application_id]["stage"] = "STARTED"
                self.active_tasks[application_id]["message"] = "Initializing browser session..."

                def callback(stage: str, percent: int, msg: str):
                    if application_id in self.active_tasks:
                        self.active_tasks[application_id]["progress"] = percent
                        self.active_tasks[application_id]["stage"] = stage
                        self.active_tasks[application_id]["message"] = msg

                res = apply_fn(user_id, application_id, callback)

                if application_id in self.active_tasks:
                    self.active_tasks[application_id]["status"] = "COMPLETED" if res.get("success") else "FAILED"
                    self.active_tasks[application_id]["progress"] = 100
                    self.active_tasks[application_id]["stage"] = "DONE"
                    self.active_tasks[application_id]["message"] = (
                        "Application completed successfully." if res.get("success") else res.get("error", "Failed")
                    )

            except Exception as e:
                logger.error(f"Application task {application_id} failed: {e}", exc_info=True)
                if application_id in self.active_tasks:
                    self.active_tasks[application_id]["status"] = "FAILED"
                    self.active_tasks[application_id]["progress"] = 100
                    self.active_tasks[application_id]["stage"] = "ERROR"
                    self.active_tasks[application_id]["message"] = str(e)

        self.executor.submit(runner)
        return application_id

    def get_search_task(self, task_id: str) -> Optional[SearchTask]:
        """Fetches the current state of a search task from database."""
        return self.task_repo.get_task(task_id)

    def get_application_task(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Fetches the in-memory progress of an active application task."""
        return self.active_tasks.get(application_id)


# Global singleton task manager
task_manager = TaskManager()
