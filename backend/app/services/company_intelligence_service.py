# backend/app/services/company_intelligence_service.py
import re
from typing import Tuple, List, Dict, Any
from app.models.job import CompanyTier


# Tier A: Globally recognized tech leaders, established enterprises & top tier tech employers
RECOGNIZABLE_COMPANIES = {
    "google", "alphabet", "amazon", "aws", "microsoft", "apple", "meta", "facebook",
    "nvidia", "netflix", "adobe", "flipkart", "walmart", "uber", "atlassian", "salesforce",
    "oracle", "ibm", "jpmorgan", "jpmorgan chase", "american express", "amex", "accenture",
    "deloitte", "cisco", "intel", "amd", "qualcomm", "stripe", "databricks", "snowflake",
    "openai", "palantir", "spotify", "airbnb", "doordash", "pinterest", "snap", "twillio",
    "mongodb", "canonical", "gitlab", "github", "elastic", "crowdstrike", "datadog",
    "vmware", "service now", "servicenow", "workday", "sap", "sony", "samsung", "target",
    "goldman sachs", "morgan stanley", "paypal", "square", "block", "intuit", "ebay"
}

# Tier B: High-signal funded startups, AI labs, scaleups, YC & top-tier VC backed unicorns
STRONG_STARTUPS = {
    "anthropic", "scale ai", "mistral", "mistral ai", "perplexity", "postman", "razorpay",
    "zepto", "swiggy", "zomato", "cohere", "cursor", "anysphere", "supabase", "vercel",
    "modal", "modal labs", "replicate", "langchain", "llamaindex", "hugging face", "huggingface",
    "together ai", "groq", "runway", "midjourney", "character ai", "jasper", "glean",
    "ramp", "brex", "rippling", "deel", "gusto", "notion", "figma", "linear", "retool",
    "airtable", "webflow", "zapier", "render", "fly.io", "railway", "neon", "pinecone",
    "weaviate", "qdrant", "chroma", "weights & biases", "wandb", "cohere health", "monzo",
    "revolut", "chime", "plaid", "robinhood", "faire", "checkr", "carta", "bolt"
}


class CompanyIntelligenceService:
    @staticmethod
    def classify_company(company_name: str) -> Tuple[CompanyTier, float]:
        """
        Classifies company into Tier A (Recognizable), Tier B (Strong Startup),
        or Tier C (Emerging), and returns (tier, company_signal_score).
        """
        if not company_name:
            return CompanyTier.EMERGING, 65.0

        clean_name = " ".join(re.sub(r"[^\w\s]", " ", company_name.lower()).split())

        # 1. Check Tier A
        for brand in RECOGNIZABLE_COMPANIES:
            if brand == clean_name or f" {brand} " in f" {clean_name} " or clean_name.startswith(f"{brand} "):
                return CompanyTier.RECOGNIZABLE, 95.0

        # 2. Check Tier B
        for startup in STRONG_STARTUPS:
            if startup == clean_name or f" {startup} " in f" {clean_name} " or clean_name.startswith(f"{startup} "):
                return CompanyTier.STRONG_STARTUP, 86.0

        # 3. Default to Tier C Emerging
        return CompanyTier.EMERGING, 72.0

    @staticmethod
    def balance_company_mix(jobs: List[Dict[str, Any]], target_count: int = 3) -> List[Dict[str, Any]]:
        """
        Ensures a diversified representation:
        - Tier A (Recognizable)
        - Tier B (Strong Startup / Scaleup)
        - Tier C (Emerging)
        Does NOT fabricate jobs; dynamically blends from available verified pool.
        """
        if not jobs:
            return []

        tier_a: List[Dict[str, Any]] = []
        tier_b: List[Dict[str, Any]] = []
        tier_c: List[Dict[str, Any]] = []

        for j in jobs:
            t = j.get("company_tier")
            if t == CompanyTier.RECOGNIZABLE.value or t == CompanyTier.RECOGNIZABLE:
                tier_a.append(j)
            elif t == CompanyTier.STRONG_STARTUP.value or t == CompanyTier.STRONG_STARTUP:
                tier_b.append(j)
            else:
                tier_c.append(j)

        # Sort each tier bucket by final_score
        tier_a.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        tier_b.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        tier_c.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        selected: List[Dict[str, Any]] = []
        seen_ids = set()

        def add_job(job_item):
            if job_item and job_item["id"] not in seen_ids:
                selected.append(job_item)
                seen_ids.add(job_item["id"])

        if target_count <= 3:
            # Ideal mix: 1 Tier A, 1 Tier B, 1 Tier C
            if tier_a: add_job(tier_a[0])
            if tier_b: add_job(tier_b[0])
            if tier_c: add_job(tier_c[0])
        elif target_count <= 6:
            # Mix: 2 Tier A, 2 Tier B, 2 Tier C
            for j in tier_a[:2]: add_job(j)
            for j in tier_b[:2]: add_job(j)
            for j in tier_c[:2]: add_job(j)
        else:
            # Mix: 4 Tier A, 3 Tier B, 3 Tier C
            for j in tier_a[:4]: add_job(j)
            for j in tier_b[:3]: add_job(j)
            for j in tier_c[:3]: add_job(j)

        # Fill remaining slots from best overall remaining jobs
        all_sorted = sorted(jobs, key=lambda x: x.get("final_score", 0), reverse=True)
        for j in all_sorted:
            if len(selected) >= target_count:
                break
            add_job(j)

        return selected


company_intel = CompanyIntelligenceService()
