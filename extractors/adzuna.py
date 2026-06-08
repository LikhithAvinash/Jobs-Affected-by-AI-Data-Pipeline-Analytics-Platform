"""
Adzuna Jobs API Extractor.

Docs: https://developer.adzuna.com/overview
Fetches job postings with pagination and returns normalised dicts.
"""

import os
import logging
from typing import Dict, List, Optional

from dotenv import load_dotenv

from src.utils.http_client import RateLimitedSession, safe_get

load_dotenv()
logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


class AdzunaExtractor:
    """Extract job listings from the Adzuna API."""

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_key: Optional[str] = None,
        country: str = "us",
    ):
        self.app_id = app_id or os.getenv("ADZUNA_APP_ID", "")
        self.app_key = app_key or os.getenv("ADZUNA_APP_KEY", "")
        self.country = country
        self.session = RateLimitedSession(calls_per_second=1.0)

    def search_jobs(
        self,
        query: str = "data engineer",
        results_per_page: int = 50,
        max_pages: int = 5,
    ) -> List[Dict]:
        """
        Search for jobs and paginate through results.

        Returns a list of normalised job dicts ready for transformation.
        """
        all_jobs: List[Dict] = []

        for page in range(1, max_pages + 1):
            url = f"{BASE_URL}/{self.country}/search/{page}"
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "what": query,
                "results_per_page": results_per_page,
                "content-type": "application/json",
            }

            data = safe_get(self.session, url, params=params)
            if data is None:
                logger.warning("Adzuna page %d returned no data, stopping.", page)
                break

            results = data.get("results", [])
            if not results:
                break

            for r in results:
                all_jobs.append(self._normalise(r))

            logger.info(
                "Adzuna page %d: fetched %d jobs (total: %d)",
                page, len(results), len(all_jobs),
            )

        return all_jobs

    @staticmethod
    def _normalise(raw: Dict) -> Dict:
        """Map raw Adzuna response fields to our schema."""
        company = raw.get("company", {})
        return {
            "source": "adzuna",
            "source_id": str(raw.get("id", "")),
            "title": raw.get("title", "").strip(),
            "company_name": company.get("display_name", "").strip() if company else "",
            "location": raw.get("location", {}).get("display_name", ""),
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "description": raw.get("description", ""),
            "posted_date": raw.get("created"),  # ISO 8601 string
        }
