# backend/app/core/database.py
import sqlite3
import os
from contextlib import contextmanager
from typing import Generator
from app.core.config import settings
from app.core.logging import logger


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initializes all database tables and indexes with multi-user isolation."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO users (id, email, name) VALUES (?, ?, ?)",
                   (settings.DEFAULT_USER_ID, "candidate@jobmate.ai", "Default Candidate"))

    # 2. Candidate Profiles table (User scoped)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            skills TEXT,
            experience_years TEXT,
            education TEXT,
            resume_filename TEXT,
            resume_path TEXT,
            full_profile_json TEXT,
            extracted_fields_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON candidate_profiles(user_id);")

    # Maintain backward compatibility profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            skills TEXT,
            experience_years TEXT,
            education TEXT,
            resume_filename TEXT,
            resume_path TEXT,
            full_profile_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Normalized Jobs table (Global shared job pool with rich intelligence)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            external_id TEXT,
            title TEXT,
            company TEXT,
            company_domain TEXT,
            company_tier TEXT DEFAULT 'emerging',
            location TEXT,
            remote_type TEXT DEFAULT 'Remote',
            employment_type TEXT DEFAULT 'Full-time',
            description TEXT,
            requirements TEXT,
            responsibilities TEXT,
            skills TEXT,
            salary TEXT,
            posted_at TEXT,
            discovered_at TEXT,
            verified_at TEXT,
            is_verified INTEGER DEFAULT 1,
            job_url TEXT UNIQUE,
            apply_url TEXT,
            source TEXT DEFAULT 'ATS',
            source_type TEXT DEFAULT 'greenhouse',
            ats TEXT DEFAULT 'custom',
            freshness_score REAL DEFAULT 80.0,
            company_score REAL DEFAULT 70.0,
            match_score REAL DEFAULT 85.0,
            final_score REAL DEFAULT 80.0,
            url_validated INTEGER DEFAULT 1,
            why_recommended TEXT,
            status TEXT DEFAULT 'VERIFIED',
            job_hash TEXT,
            raw_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_job_hash ON jobs(job_hash);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_final_score ON jobs(final_score);")

    # 4. User-Job Match table (User-personalized job rankings)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_job_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            job_id TEXT NOT NULL,
            match_score REAL DEFAULT 0.0,
            freshness_score REAL DEFAULT 0.0,
            company_score REAL DEFAULT 0.0,
            final_score REAL DEFAULT 0.0,
            why_recommended TEXT,
            is_saved INTEGER DEFAULT 0,
            is_dismissed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, job_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_job_user_id ON user_job_matches(user_id);")

    # 5. Search Tasks table (Asynchronous concurrent search tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_tasks (
            task_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            target_role TEXT,
            target_location TEXT,
            status TEXT DEFAULT 'PENDING',
            progress INTEGER DEFAULT 0,
            total_found INTEGER DEFAULT 0,
            result_job_ids TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_tasks_user_id ON search_tasks(user_id);")

    # 6. Applications table (User scoped)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'user_default',
            job_id TEXT,
            job_title TEXT,
            company TEXT,
            job_url TEXT,
            apply_url TEXT,
            status TEXT DEFAULT 'APPLY_STARTED',
            result_json TEXT,
            settings_json TEXT,
            error_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);")

    # 7. Application Fields table (Detailed per-field decision trace)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS application_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER,
            field_name TEXT,
            question TEXT,
            detected_type TEXT,
            source TEXT DEFAULT 'PROFILE',
            generated_answer TEXT,
            filled_successfully INTEGER DEFAULT 1,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_fields_app_id ON application_fields(application_id);")

    # 8. Application Answers Cache table (Scoped to user with optional global fallback)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS application_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'user_default',
            candidate_id INTEGER DEFAULT 1,
            question TEXT,
            normalized_question TEXT,
            question_type TEXT,
            answer TEXT,
            job_id TEXT,
            company TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_norm_q ON application_answers(normalized_question);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_user_id ON application_answers(user_id);")

    # 9. Agent Settings table (User scoped)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE DEFAULT 'user_default',
            auto_answer_descriptive INTEGER DEFAULT 1,
            auto_submit INTEGER DEFAULT 0,
            preferred_model TEXT DEFAULT 'openai/gpt-oss-120b',
            max_answer_words INTEGER DEFAULT 150,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO agent_settings (id, user_id, auto_answer_descriptive, auto_submit, preferred_model, max_answer_words)
        VALUES (1, 'user_default', 1, 0, 'openai/gpt-oss-120b', 150)
    """)

    conn.commit()
    conn.close()
    logger.info("Database schema and indexes initialized successfully.")
