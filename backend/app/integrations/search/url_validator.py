# backend/app/integrations/search/url_validator.py
import re
import json
import hashlib
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
import requests
from bs4 import BeautifulSoup
from app.models.job import JobSchema, CompanyTier
from app.core.logging import logger

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class JobURLValidator:
    @staticmethod
    def detect_ats(url: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Detect ATS provider, company slug, and external job ID from URL.
        Returns (ats_name, company_slug, external_job_id).
        """
        if not url:
            return "custom", None, None

        clean_url = url.split("?")[0].rstrip("/")

        # 1. Greenhouse
        gh_match = re.search(
            r"https?://(?:job-boards\.(?:eu\.)?greenhouse\.io|boards\.greenhouse\.io|boards\.eu\.greenhouse\.io)/([^/]+)/jobs/(\d+)",
            clean_url,
            re.IGNORECASE
        )
        if gh_match:
            return "greenhouse", gh_match.group(1), gh_match.group(2)

        gh_alt = re.search(
            r"https?://(?:job-boards\.(?:eu\.)?greenhouse\.io|boards\.greenhouse\.io|boards\.eu\.greenhouse\.io)/([^/]+)",
            clean_url,
            re.IGNORECASE
        )
        if gh_alt and "jobs" not in clean_url:
            return "greenhouse_listing", gh_alt.group(1), None

        # 2. Lever
        lever_match = re.search(
            r"https?://jobs\.lever\.co/([^/]+)/([a-f0-9\-]{10,})",
            clean_url,
            re.IGNORECASE
        )
        if lever_match:
            return "lever", lever_match.group(1), lever_match.group(2)

        lever_alt = re.search(
            r"https?://jobs\.lever\.co/([^/]+)",
            clean_url,
            re.IGNORECASE
        )
        if lever_alt:
            return "lever_listing", lever_alt.group(1), None

        # 3. Ashby
        ashby_match = re.search(
            r"https?://jobs\.ashbyhq\.com/([^/]+)/([a-f0-9\-]{10,})",
            clean_url,
            re.IGNORECASE
        )
        if ashby_match:
            return "ashby", ashby_match.group(1), ashby_match.group(2)

        # 4. Workable
        workable_match = re.search(
            r"https?://apply\.workable\.com/([^/]+)/j/([a-zA-Z0-9]+)",
            clean_url,
            re.IGNORECASE
        )
        if workable_match:
            return "workable", workable_match.group(1), workable_match.group(2)

        return "custom", None, None

    @staticmethod
    def is_generic_career_page(url: str) -> bool:
        """Returns True if the URL is a generic career portal rather than an individual job listing."""
        if not url:
            return True
        return not JobURLValidator.is_individual_job_url(url)

    @staticmethod
    def is_ats_url(url: str) -> bool:
        """Checks if URL belongs to a known Applicant Tracking System."""
        if not url:
            return False
        clean = url.lower()
        ats_domains = ["greenhouse.io", "lever.co", "ashbyhq.com", "workable.com", "myworkdayjobs.com", "smartrecruiters.com", "icims.com"]
        return any(d in clean for d in ats_domains)

    @staticmethod
    def normalize_url(url: str) -> str:
        """Strips tracking UTM query parameters, hash anchors, and trailing slashes."""
        if not url:
            return ""
        parsed = urllib.parse.urlparse(url)
        # Filter out tracking query params
        query_params = urllib.parse.parse_qsl(parsed.query)
        filtered_params = [
            (k, v) for k, v in query_params 
            if not k.lower().startswith(("utm_", "gh_src", "ref", "source"))
        ]
        clean_query = urllib.parse.urlencode(filtered_params)
        clean_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/"),
            "",
            clean_query,
            ""
        ))
        return clean_url

    @staticmethod
    def is_individual_job_url(url: str) -> bool:
        """Check if URL points to a specific job posting rather than a generic careers portal."""
        ats, _, job_id = JobURLValidator.detect_ats(url)
        if ats in ["greenhouse", "lever", "ashby", "workable"] and job_id:
            return True

        clean_url = url.split("?")[0].lower()

        # Reject generic non-job pages
        generic_suffixes = [
            "/careers", "/careers/", "/jobs", "/jobs/", "/about", "/search",
            "/categories", "/open-positions", "/teams", "/culture"
        ]
        if any(clean_url.endswith(s) for s in generic_suffixes):
            return False

        if any(bad in clean_url for bad in ["linkedin.com/in/", "wikipedia.org", "glassdoor.com/Reviews", "indeed.com/cmp"]):
            return False

        # Check for specific job indicators
        job_patterns = [
            r"/jobs/\d+",
            r"/job/[a-zA-Z0-9\-]+",
            r"/positions/[a-zA-Z0-9\-]+",
            r"/careers/[a-zA-Z0-9\-]+/[a-zA-Z0-9\-]+",
            r"gh_jid=\d+",
            r"/o/[a-zA-Z0-9\-]+"
        ]
        return any(re.search(p, url, re.IGNORECASE) for p in job_patterns)

    @staticmethod
    def extract_links_from_listing(html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        found = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urllib.parse.urljoin(base_url, href)
            if JobURLValidator.is_individual_job_url(full_url) and full_url != base_url:
                if full_url not in found:
                    found.append(full_url)
        return found

    @staticmethod
    def extract_posted_date(soup: BeautifulSoup, text: str) -> Tuple[Optional[str], float]:
        """
        Extracts posted date and computes freshness score (0-100).
        """
        now = datetime.utcnow()
        posted_at_str = None
        days_old = None

        # 1. JSON-LD datePosted
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("datePosted"):
                    posted_at_str = str(data["datePosted"])[:10]
                    break
            except Exception:
                pass

        # 2. Meta tags
        if not posted_at_str:
            meta_date = soup.find("meta", property=re.compile(r"date|posted|time", re.IGNORECASE))
            if meta_date and meta_date.get("content"):
                posted_at_str = str(meta_date["content"])[:10]

        # 3. Regex on text (e.g. "Posted 2 days ago", "Posted yesterday", "24 hours ago")
        if not posted_at_str:
            m = re.search(r"posted\s+(\d+)\s+days?\s+ago", text, re.IGNORECASE)
            if m:
                days_old = int(m.group(1))
                posted_at_str = (now - timedelta(days=days_old)).strftime("%Y-%m-%d")
            elif "posted yesterday" in text.lower() or "1 day ago" in text.lower():
                days_old = 1
                posted_at_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            elif "posted today" in text.lower() or "hours ago" in text.lower():
                days_old = 0
                posted_at_str = now.strftime("%Y-%m-%d")

        # Parse days_old if date string parsed
        if posted_at_str and days_old is None:
            try:
                parsed_date = datetime.strptime(posted_at_str[:10], "%Y-%m-%d")
                days_old = max(0, (now - parsed_date).days)
            except Exception:
                days_old = 3

        if days_old is None:
            days_old = 4  # Default assumption for fresh discovery

        # Compute freshness score with recency curve
        if days_old <= 2:
            freshness = 98.0 - (days_old * 2)
        elif days_old <= 7:
            freshness = 92.0 - ((days_old - 2) * 2.5)
        elif days_old <= 14:
            freshness = 79.0 - ((days_old - 7) * 2.0)
        elif days_old <= 30:
            freshness = 64.0 - ((days_old - 14) * 1.2)
        else:
            freshness = max(20.0, 44.0 - ((days_old - 30) * 0.5))

        return posted_at_str or now.strftime("%Y-%m-%d"), round(freshness, 1)

    @classmethod
    def verify_and_extract_job(
        cls,
        url: str,
        fallback_title: Optional[str] = None,
        fallback_company: Optional[str] = None
    ) -> Optional[JobSchema]:
        """
        Validates URL, follows redirect chain, extracts job metadata, and constructs verified JobSchema.
        """
        if not url or not url.startswith("http"):
            return None

        try:
            resp = requests.get(url, headers=HEADERS, timeout=7.0, allow_redirects=True)
            if resp.status_code != 200:
                return None

            final_url = resp.url
            text = resp.text
            text_lower = text.lower()

            # Reject 404/closed postings
            inactive_phrases = [
                "not found - 404", "404 error", "page not found", "job not found",
                "job is no longer open", "no longer accepting applications",
                "position has been filled", "this posting is closed", "this job is closed"
            ]
            if any(phrase in text_lower for phrase in inactive_phrases):
                return None

            # Handle listing pages
            ats_type, company_slug, external_id = cls.detect_ats(final_url)
            if ats_type in ["greenhouse_listing", "lever_listing"] or not cls.is_individual_job_url(final_url):
                links = cls.extract_links_from_listing(text, final_url)
                if links:
                    return cls.verify_and_extract_job(links[0], fallback_title, fallback_company)
                return None

            soup = BeautifulSoup(text, "html.parser")

            # 1. Title
            title = ""
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "JobPosting":
                        title = data.get("title", "")
                        break
                except Exception:
                    pass

            if not title:
                h1 = soup.find("h1")
                if h1 and h1.get_text(strip=True):
                    title = h1.get_text(strip=True)

            if not title:
                title_tag = soup.find("title")
                if title_tag:
                    raw_t = title_tag.get_text(strip=True)
                    title = re.sub(r"^(Job Application for|Apply for|Careers at)\s+", "", raw_t, flags=re.IGNORECASE)
                    title = title.split(" - ")[0].split(" | ")[0].split(" at ")[0].strip()

            if not title and fallback_title:
                title = fallback_title

            if not title or title.lower() in ["careers", "job opening", "apply", "404", "welcome"]:
                return None

            # 2. Company
            company = ""
            if company_slug:
                company = company_slug.replace("-", " ").title()

            if not company:
                meta_site = soup.find("meta", property="og:site_name")
                if meta_site and meta_site.get("content"):
                    company = meta_site["content"].strip()

            if not company and fallback_company:
                company = fallback_company

            if not company:
                company = "Tech Company"

            # 3. Description
            desc_el = (
                soup.find(id="content") or
                soup.find(class_=re.compile(r"description|content|job-details|posting-page|section-page", re.IGNORECASE)) or
                soup.find("main") or soup.find("article") or soup.find("body")
            )
            desc = desc_el.get_text(" ", strip=True) if desc_el else soup.get_text(" ", strip=True)
            desc = re.sub(r"\s+", " ", desc)

            if len(desc) < 25:
                return None

            # 4. Requirements & Responsibilities
            requirements = []
            responsibilities = []
            for li in soup.find_all("li"):
                li_text = li.get_text(strip=True)
                if 15 < len(li_text) < 300:
                    parent_text = (li.find_parent("section") or li.find_parent("div") or soup).get_text().lower()
                    if any(w in parent_text for w in ["requirement", "qualification", "what you'll need", "who you are"]):
                        requirements.append(li_text)
                    elif any(w in parent_text for w in ["responsibilit", "what you'll do", "about the role"]):
                        responsibilities.append(li_text)

            # 5. Location & Remote Type
            location = "Remote"
            loc_el = soup.find(class_=re.compile(r"location|workplace", re.IGNORECASE))
            if loc_el and loc_el.get_text(strip=True):
                location = loc_el.get_text(strip=True)

            remote_type = "Remote" if "remote" in (location + " " + desc[:500]).lower() else "Hybrid / On-site"

            # 6. Apply URL
            apply_url = final_url
            if ats_type == "lever" and not final_url.endswith("/apply"):
                apply_url = f"{final_url}/apply"
            elif ats_type == "greenhouse" and "#app" not in final_url:
                apply_url = f"{final_url}#app"

            # 7. Posted date & Freshness
            posted_at, freshness_score = cls.extract_posted_date(soup, text)

            # 8. Unique ID
            raw_key = f"{ats_type}|{company.lower()}|{title.lower()}|{external_id or final_url}"
            job_id = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

            return JobSchema(
                id=job_id,
                external_id=str(external_id) if external_id else None,
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                remote_type=remote_type,
                employment_type="Full-time",
                description=desc[:1600].strip(),
                requirements=requirements[:6],
                responsibilities=responsibilities[:6],
                posted_at=posted_at,
                job_url=final_url,
                apply_url=apply_url,
                ats=ats_type,
                source=f"{ats_type.capitalize()} ATS",
                source_type="direct_ats",
                freshness_score=freshness_score,
                is_verified=True,
                url_validated=True
            )
        except Exception as e:
            logger.warning(f"Error validating {url}: {e}")
            return None
