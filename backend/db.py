import os
import json
import sqlite3
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from models import JobSchema, ApplicationStatus

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobmate.db")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Profiles table
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

    # Check if jobs table exists and has job_url column
    cursor.execute("PRAGMA table_info(jobs)")
    cols = [r["name"] for r in cursor.fetchall()]
    if cols and "job_url" not in cols:
        cursor.execute("DROP TABLE IF EXISTS jobs")

    # Jobs table with JobSchema columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            remote_type TEXT DEFAULT 'Remote',
            employment_type TEXT DEFAULT 'Full-time',
            description TEXT,
            requirements TEXT,
            responsibilities TEXT,
            skills TEXT,
            salary TEXT,
            posted_at TEXT,
            source TEXT,
            source_url TEXT,
            job_url TEXT UNIQUE,
            apply_url TEXT,
            ats TEXT,
            external_job_id TEXT,
            discovered_at TEXT,
            verified_at TEXT,
            is_verified INTEGER DEFAULT 1,
            match_score REAL DEFAULT 0,
            status TEXT DEFAULT 'VERIFIED',
            raw_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            job_title TEXT,
            company TEXT,
            job_url TEXT,
            apply_url TEXT,
            status TEXT,
            result_json TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Auto-migrate applications table columns
    cursor.execute("PRAGMA table_info(applications)")
    app_cols = [r["name"] for r in cursor.fetchall()]
    if "apply_url" not in app_cols:
        try:
            cursor.execute("ALTER TABLE applications ADD COLUMN apply_url TEXT")
        except Exception:
            pass
    if "job_id" not in app_cols:
        try:
            cursor.execute("ALTER TABLE applications ADD COLUMN job_id TEXT")
        except Exception:
            pass

    conn.commit()
    conn.close()


def save_profile(profile_data: Dict[str, Any], resume_path: str = "", resume_filename: str = "") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    name = profile_data.get("name") or profile_data.get("full_name") or ""
    email = profile_data.get("email") or ""
    phone = profile_data.get("phone") or ""
    location = profile_data.get("location") or ""
    skills = json.dumps(profile_data.get("skills", []), ensure_ascii=False)
    exp = str(profile_data.get("experience_years", "") or profile_data.get("experience", ""))
    edu = str(profile_data.get("education", "") or profile_data.get("college", ""))
    profile_json = json.dumps(profile_data, ensure_ascii=False)

    cursor.execute("SELECT id FROM profiles ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE profiles SET
                name = ?, email = ?, phone = ?, location = ?, skills = ?,
                experience_years = ?, education = ?, resume_filename = ?,
                resume_path = ?, full_profile_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, email, phone, location, skills, exp, edu, resume_filename, resume_path, profile_json, row["id"]))
    else:
        cursor.execute("""
            INSERT INTO profiles (
                name, email, phone, location, skills, experience_years,
                education, resume_filename, resume_path, full_profile_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, location, skills, exp, edu, resume_filename, resume_path, profile_json))

    conn.commit()
    conn.close()
    return profile_data


def get_active_profile() -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None, None, None

    try:
        profile = json.loads(row["full_profile_json"]) if row["full_profile_json"] else {}
    except Exception:
        profile = {
            "name": row["name"],
            "email": row["email"],
            "phone": row["phone"],
            "location": row["location"],
            "skills": json.loads(row["skills"]) if row["skills"] else [],
            "experience_years": row["experience_years"],
            "education": row["education"]
        }

    return profile, row["resume_path"], row["resume_filename"]


def _generate_job_id(job: Dict[str, Any]) -> str:
    if job.get("id"):
        return str(job["id"])
    url = job.get("job_url") or job.get("url") or ""
    title = job.get("title") or ""
    company = job.get("company") or ""
    raw = f"{url}|{title}|{company}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def save_jobs(jobs_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not jobs_list:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()

    saved = []
    for job in jobs_list:
        job_dict = dict(job)
        job_id = _generate_job_id(job_dict)
        job_dict["id"] = job_id

        title = job_dict.get("title") or "Untitled Role"
        company = job_dict.get("company") or "Company"
        location = job_dict.get("location") or "Remote"
        remote_type = job_dict.get("remote_type") or "Remote"
        employment_type = job_dict.get("employment_type") or "Full-time"
        description = job_dict.get("description") or ""
        requirements = json.dumps(job_dict.get("requirements", []), ensure_ascii=False)
        responsibilities = json.dumps(job_dict.get("responsibilities", []), ensure_ascii=False)
        skills = json.dumps(job_dict.get("skills", []), ensure_ascii=False)
        salary = job_dict.get("salary") or ""
        posted_at = job_dict.get("posted_at") or ""
        source = job_dict.get("source") or "ATS"
        source_url = job_dict.get("source_url") or ""
        job_url = job_dict.get("job_url") or job_dict.get("url") or f"job-{job_id}"
        apply_url = job_dict.get("apply_url") or job_url
        ats = job_dict.get("ats") or "custom"
        external_job_id = job_dict.get("external_job_id") or ""
        discovered_at = job_dict.get("discovered_at") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        verified_at = job_dict.get("verified_at") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        is_verified = 1 if job_dict.get("is_verified", True) else 0
        match_score = float(job_dict.get("match_score", 85.0) or 85.0)
        status = job_dict.get("status") or "VERIFIED"
        raw_json = json.dumps(job_dict, ensure_ascii=False)

        cursor.execute("""
            INSERT INTO jobs (
                id, title, company, location, remote_type, employment_type,
                description, requirements, responsibilities, skills, salary,
                posted_at, source, source_url, job_url, apply_url, ats,
                external_job_id, discovered_at, verified_at, is_verified,
                match_score, status, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_url) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                remote_type = excluded.remote_type,
                employment_type = excluded.employment_type,
                description = excluded.description,
                requirements = excluded.requirements,
                responsibilities = excluded.responsibilities,
                skills = excluded.skills,
                salary = excluded.salary,
                apply_url = excluded.apply_url,
                ats = excluded.ats,
                match_score = excluded.match_score,
                is_verified = excluded.is_verified,
                raw_json = excluded.raw_json
        """, (
            job_id, title, company, location, remote_type, employment_type,
            description, requirements, responsibilities, skills, salary,
            posted_at, source, source_url, job_url, apply_url, ats,
            external_job_id, discovered_at, verified_at, is_verified,
            match_score, status, raw_json
        ))
        saved.append(job_dict)

    conn.commit()
    conn.close()
    return saved


def get_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM jobs
        ORDER BY match_score DESC, created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        try:
            job_obj = json.loads(row["raw_json"]) if row["raw_json"] else {}
        except Exception:
            job_obj = {}

        # Ensure schema fields are normalized
        job_obj["id"] = row["id"]
        job_obj["title"] = row["title"]
        job_obj["company"] = row["company"]
        job_obj["location"] = row["location"]
        job_obj["remote_type"] = row["remote_type"] or "Remote"
        job_obj["job_url"] = row["job_url"]
        job_obj["url"] = row["job_url"]
        job_obj["apply_url"] = row["apply_url"] or row["job_url"]
        job_obj["ats"] = row["ats"] or "custom"
        job_obj["description"] = row["description"]
        job_obj["match_score"] = row["match_score"]
        job_obj["source"] = row["source"]
        job_obj["is_verified"] = bool(row["is_verified"])
        job_obj["created_at"] = row["created_at"]

        try:
            job_obj["requirements"] = json.loads(row["requirements"]) if row["requirements"] else []
        except Exception:
            job_obj["requirements"] = []

        try:
            job_obj["responsibilities"] = json.loads(row["responsibilities"]) if row["responsibilities"] else []
        except Exception:
            job_obj["responsibilities"] = []

        result.append(job_obj)

    return result


def clear_jobs():
    conn = get_db_connection()
    conn.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()


def save_application(
    job_url: str,
    job_title: str = "",
    company: str = "",
    apply_url: str = "",
    job_id: str = "",
    status: str = "APPLY_STARTED",
    result: Any = None
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    result_json = json.dumps(result, ensure_ascii=False) if result is not None else "{}"

    cursor.execute("""
        INSERT INTO applications (job_id, job_title, company, job_url, apply_url, status, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (job_id, job_title, company, job_url, apply_url or job_url, status, result_json))
    app_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return app_id


def update_application(app_id: int, status: str, result: Any = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    result_json = json.dumps(result, ensure_ascii=False) if result is not None else "{}"

    cursor.execute("""
        UPDATE applications
        SET status = ?, result_json = ?
        WHERE id = ?
    """, (status, result_json, app_id))
    conn.commit()
    conn.close()


def get_applications(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM applications
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        try:
            res_data = json.loads(row["result_json"]) if row["result_json"] else {}
        except Exception:
            res_data = {}

        result.append({
            "id": row["id"],
            "job_id": row["job_id"],
            "job_url": row["job_url"],
            "apply_url": row["apply_url"],
            "job_title": row["job_title"],
            "company": row["company"],
            "status": row["status"],
            "result": res_data,
            "timestamp": row["timestamp"]
        })
    return result
