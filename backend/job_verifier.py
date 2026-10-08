import re
import json
import hashlib
import urllib.parse
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import requests
from bs4 import BeautifulSoup
from models import JobSchema


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def detect_ats(url: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Detect ATS provider, company slug, and external job ID from URL.
    Returns (ats_name, company, external_job_id).
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

    # 5. Generic / Custom ATS
    return "custom", None, None


def _is_individual_job_url(url: str) -> bool:
    """Check if URL points to a single job posting rather than a careers homepage."""
    ats, _, job_id = detect_ats(url)
    if ats in ["greenhouse", "lever", "ashby", "workable"] and job_id:
        return True

    clean_url = url.split("?")[0].lower()

    # Reject obvious non-job URLs
    if (
        clean_url.endswith("/careers") or
        clean_url.endswith("/jobs") or
        clean_url.endswith("/jobs/") or
        clean_url.endswith("/about") or
        "/in/" in clean_url or
        "linkedin.com/in/" in clean_url or
        "example.com" in clean_url or
        "wikipedia.org" in clean_url
    ):
        return False

    # Check for job path patterns
    patterns = [
        r"/jobs/\d+",
        r"/job/[a-zA-Z0-9\-]+",
        r"/positions/[a-zA-Z0-9\-]+",
        r"/careers/[a-zA-Z0-9\-]+/[a-zA-Z0-9\-]+",
        r"gh_jid=\d+"
    ]
    return any(re.search(p, url, re.IGNORECASE) for p in patterns)


def _extract_individual_links_from_listing(html: str, base_url: str) -> List[str]:
    """If given a careers board listing page, scrape links to individual job posts."""
    soup = BeautifulSoup(html, "html.parser")
    found_urls = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urllib.parse.urljoin(base_url, href)
        if _is_individual_job_url(full_url) and full_url != base_url:
            if full_url not in found_urls:
                found_urls.append(full_url)

    return found_urls


def verify_and_extract_job(
    url: str,
    fallback_title: Optional[str] = None,
    fallback_company: Optional[str] = None
) -> Optional[JobSchema]:
    """
    1. Fetches the URL.
    2. Validates HTTP 200 and checks for 404/closed postings.
    3. If listing page, extracts first valid individual job.
    4. Scrapes title, company, description, requirements, apply_url.
    5. Returns a verified JobSchema or None if invalid.
    """
    if not url or not url.startswith("http"):
        return None

    try:
        resp = requests.get(url, headers=HEADERS, timeout=7.0, allow_redirects=True)
        if resp.status_code != 200:
            print(f"[JobVerifier] HTTP {resp.status_code} for {url} -> Rejected")
            return None

        final_url = resp.url
        text = resp.text
        text_lower = text.lower()

        # Check for 404 / Dead / Inactive indicators
        inactive_phrases = [
            "not found - 404",
            "404 error",
            "404: page not found",
            "page not found",
            "job not found",
            "job is no longer open",
            "no longer accepting applications",
            "position has been filled",
            "this posting is closed",
            "this job is closed"
        ]
        if any(phrase in text_lower for phrase in inactive_phrases):
            print(f"[JobVerifier] Inactive/404 content detected on {final_url} -> Rejected")
            return None

        # Check if this is a listing page instead of a single job
        ats_type, company_slug, external_id = detect_ats(final_url)
        if ats_type in ["greenhouse_listing", "lever_listing"] or not _is_individual_job_url(final_url):
            individual_links = _extract_individual_links_from_listing(text, final_url)
            if individual_links:
                print(f"[JobVerifier] Extracted individual job link: {individual_links[0]} from listing {final_url}")
                return verify_and_extract_job(individual_links[0], fallback_title, fallback_company)
            else:
                print(f"[JobVerifier] {final_url} is a careers listing without distinct job links -> Rejected")
                return None

        # Parse DOM
        soup = BeautifulSoup(text, "html.parser")

        # 1. Title Extraction
        title = ""
        # Schema.org JSON-LD
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
                # Clean title like "Job Application for Backend Engineer at GitLab"
                title = re.sub(r"^(Job Application for|Apply for|Careers at)\s+", "", raw_t, flags=re.IGNORECASE)
                title = title.split(" - ")[0].split(" | ")[0].split(" at ")[0].strip()

        if not title and fallback_title:
            title = fallback_title

        # Reject generic titles
        if not title or title.lower() in ["careers", "job opening", "apply", "404", "welcome"]:
            print(f"[JobVerifier] Invalid or generic title '{title}' for {final_url} -> Rejected")
            return None

        # 2. Company Extraction
        company = ""
        if company_slug:
            company = company_slug.replace("-", " ").title()

        if not company:
            # Check meta tags
            meta_site = soup.find("meta", property="og:site_name")
            if meta_site and meta_site.get("content"):
                company = meta_site["content"].strip()

        if not company and fallback_company:
            company = fallback_company

        if not company:
            company = "Tech Company"

        # 3. Description Extraction
        desc = ""
        desc_el = (
            soup.find(id="content") or
            soup.find(class_=re.compile(r"description|content|job-details|posting-page|section-page|posting-description", re.IGNORECASE)) or
            soup.find("main") or
            soup.find("article") or
            soup.find("body")
        )
        if desc_el:
            desc = desc_el.get_text(" ", strip=True)
        else:
            desc = soup.get_text(" ", strip=True)

        # Remove excessive whitespace
        desc = re.sub(r"\s+", " ", desc)

        if len(desc) < 20:
            print(f"[JobVerifier] Insufficient description ({len(desc)} chars) for {final_url} -> Rejected")
            return None

        # 4. Requirements & Responsibilities Extraction
        requirements = []
        responsibilities = []
        skills_found = []

        # Scrape list items
        for li in soup.find_all("li"):
            li_text = li.get_text(strip=True)
            if len(li_text) > 15 and len(li_text) < 300:
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

        # 7. Generate Stable Unique ID
        raw_key = f"{ats_type}|{company.lower()}|{title.lower()}|{external_id or final_url}"
        job_id = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

        job_schema = JobSchema(
            id=job_id,
            title=title.strip(),
            company=company.strip(),
            location=location.strip(),
            remote_type=remote_type,
            employment_type="Full-time",
            description=desc[:1500].strip(),
            requirements=requirements[:6],
            responsibilities=responsibilities[:6],
            skills=skills_found,
            source=f"{ats_type.capitalize()} ATS",
            source_url=url,
            job_url=final_url,
            apply_url=apply_url,
            ats=ats_type,
            external_job_id=str(external_id) if external_id else None,
            discovered_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            verified_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            is_verified=True,
            match_score=0.0
        )

        print(f"[JobVerifier] Successfully verified job: '{job_schema.title}' at {job_schema.company} ({job_schema.job_url}) [OK]")
        return job_schema

    except Exception as err:
        print(f"[JobVerifier] Error verifying {url}: {err}")
        return None
