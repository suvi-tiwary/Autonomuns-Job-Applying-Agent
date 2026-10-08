# backend/app/integrations/search/tavily_client.py
import requests
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger


class TavilySearchClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.TAVILY_API_KEY).strip()

    def search_urls(self, query: str, max_results: int = 8) -> List[str]:
        if not self.api_key:
            return []

        try:
            payload = {
                "api_key": self.api_key,
                "query": query.strip(),
                "search_depth": "basic",
                "max_results": max_results
            }
            res = requests.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=10,
                headers={"User-Agent": "JobMate-AI/2.0"}
            )
            if res.status_code == 200:
                data = res.json()
                urls = []
                for item in data.get("results", []):
                    u = item.get("url", "").strip()
                    if u and u.startswith("http") and u not in urls:
                        urls.append(u)
                return urls
        except Exception as e:
            logger.warning(f"Tavily search error for '{query}': {e}")

        return []


tavily_client = TavilySearchClient()
