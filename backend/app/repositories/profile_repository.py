# backend/app/repositories/profile_repository.py
import json
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from app.core.database import get_db
from app.models.profile import CandidateProfile


class ProfileRepository:
    def get_by_user_id(self, user_id: str = "user_default") -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM candidate_profiles WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
                (user_id,)
            )
            row = cursor.fetchone()
            
            # Fallback to legacy profiles table if empty
            if not row:
                cursor.execute("SELECT * FROM profiles ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                
            if not row:
                return None, None, None

            try:
                profile_dict = json.loads(row["full_profile_json"]) if row["full_profile_json"] else {}
            except Exception:
                profile_dict = {
                    "personal": {
                        "full_name": row["name"],
                        "email": row["email"],
                        "phone": row["phone"],
                        "location": row["location"]
                    },
                    "professional": {
                        "key_skills": json.loads(row["skills"]) if row["skills"] else [],
                        "experience_years": row["experience_years"]
                    },
                    "education": {
                        "college_name": row["education"]
                    }
                }

            return profile_dict, row["resume_path"], row["resume_filename"]

    def get_profile(self, user_id: str = "user_default") -> CandidateProfile:
        raw_dict, resume_path, resume_filename = self.get_by_user_id(user_id=user_id)
        if not raw_dict:
            return CandidateProfile(user_id=user_id)
        from app.services.profile_service import ProfileService
        prof = ProfileService.normalize_to_candidate_profile(raw_dict, user_id=user_id)
        prof.resume_path = resume_path or prof.resume_path
        prof.resume_filename = resume_filename or prof.resume_filename
        return prof

    def save_profile(
        self,
        profile_data: Any,
        user_id: str = "user_default",
        resume_path: str = "",
        resume_filename: str = ""
    ) -> CandidateProfile:
        if isinstance(profile_data, CandidateProfile):
            user_id = profile_data.user_id or user_id
            resume_path = profile_data.resume_path or resume_path
            resume_filename = profile_data.resume_filename or resume_filename
            p_dict = profile_data.model_dump()
        elif isinstance(profile_data, dict):
            p_dict = profile_data
        else:
            p_dict = {}

        with get_db() as conn:
            cursor = conn.cursor()

            p = p_dict.get("personal", {}) if isinstance(p_dict.get("personal"), dict) else {}
            name = p.get("full_name") or p_dict.get("name") or p_dict.get("full_name") or ""
            email = p.get("email") or p_dict.get("email") or ""
            phone = p.get("phone") or p_dict.get("phone") or ""
            location = p.get("location") or p_dict.get("location") or ""

            prof = p_dict.get("professional", {}) if isinstance(p_dict.get("professional"), dict) else {}
            skills_data = prof.get("key_skills") or p_dict.get("skills", [])
            skills = json.dumps(skills_data if isinstance(skills_data, list) else [], ensure_ascii=False)
            exp = str(prof.get("experience_years") or p_dict.get("experience_years", "") or "0")

            edu = p_dict.get("education", {}) if isinstance(p_dict.get("education"), dict) else {}
            edu_str = str(edu.get("college_name") or edu.get("degree") or p_dict.get("education", ""))

            profile_json = json.dumps(p_dict, ensure_ascii=False)
            extracted_json = json.dumps(p_dict.get("extracted_fields", []), ensure_ascii=False)

            # Ensure user exists in users table
            cursor.execute("INSERT OR IGNORE INTO users (id, name, email) VALUES (?, ?, ?)", (user_id, name or user_id, email or f"{user_id}@example.com"))

            # Check existing candidate profile
            cursor.execute("SELECT id FROM candidate_profiles WHERE user_id = ? LIMIT 1", (user_id,))
            row = cursor.fetchone()

            if row:
                cursor.execute("""
                    UPDATE candidate_profiles SET
                        name = ?, email = ?, phone = ?, location = ?, skills = ?,
                        experience_years = ?, education = ?, resume_filename = ?,
                        resume_path = ?, full_profile_json = ?, extracted_fields_json = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (name, email, phone, location, skills, exp, edu_str, resume_filename, resume_path, profile_json, extracted_json, row["id"]))
            else:
                cursor.execute("""
                    INSERT INTO candidate_profiles (
                        user_id, name, email, phone, location, skills, experience_years,
                        education, resume_filename, resume_path, full_profile_json, extracted_fields_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, name, email, phone, location, skills, exp, edu_str, resume_filename, resume_path, profile_json, extracted_json))

            # Sync legacy table
            cursor.execute("SELECT id FROM profiles ORDER BY id DESC LIMIT 1")
            legacy_row = cursor.fetchone()
            if legacy_row:
                cursor.execute("""
                    UPDATE profiles SET
                        name = ?, email = ?, phone = ?, location = ?, skills = ?,
                        experience_years = ?, education = ?, resume_filename = ?,
                        resume_path = ?, full_profile_json = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (name, email, phone, location, skills, exp, edu_str, resume_filename, resume_path, profile_json, legacy_row["id"]))
            else:
                cursor.execute("""
                    INSERT INTO profiles (
                        name, email, phone, location, skills, experience_years,
                        education, resume_filename, resume_path, full_profile_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, email, phone, location, skills, exp, edu_str, resume_filename, resume_path, profile_json))

            conn.commit()

        from app.services.profile_service import ProfileService
        return ProfileService.normalize_to_candidate_profile(p_dict, user_id=user_id)


profile_repo = ProfileRepository()
