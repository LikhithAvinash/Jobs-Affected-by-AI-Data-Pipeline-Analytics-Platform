"""
Stack Exchange API Extractor.

Docs: https://api.stackexchange.com/docs
Fetches trending tags/questions to gauge developer skill demand.
"""

import logging
from typing import Dict, List

from src.utils.http_client import RateLimitedSession, safe_get

logger = logging.getLogger(__name__)

BASE_URL = "https://api.stackexchange.com/2.3"

TRACKED_SKILLS = [
    "python", "sql", "docker", "kubernetes", "apache-spark",
    "pytorch", "tensorflow", "langchain", "pandas", "aws",
    "azure", "gcp", "postgresql", "mongodb", "redis",
    "fastapi", "flask", "react", "typescript", "rust",
]


class StackExchangeExtractor:
    """Extract developer skill trend data from Stack Overflow."""

    def __init__(self):
        self.session = RateLimitedSession(calls_per_second=2.0)

    def fetch_tag_info(self, tags: List[str] = None) -> List[Dict]:
        """Fetch info for specified tags (question count, etc.)."""
        tags = tags or TRACKED_SKILLS
        all_info: List[Dict] = []

        chunk_size = 20
        for i in range(0, len(tags), chunk_size):
            chunk = tags[i : i + chunk_size]
            tag_str = ";".join(chunk)
            url = f"{BASE_URL}/tags/{tag_str}/info"
            params = {"site": "stackoverflow", "filter": "default"}

            data = safe_get(self.session, url, params=params)
            if data is None:
                continue

            for item in data.get("items", []):
                all_info.append({
                    "skill_name": item.get("name", ""),
                    "question_count": item.get("count", 0),
                })

        logger.info("StackExchange: fetched info for %d tags", len(all_info))
        return all_info
