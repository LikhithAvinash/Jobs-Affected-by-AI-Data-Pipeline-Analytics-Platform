"""
The Muse API Extractor.

Docs: https://www.themuse.com/developers/api/v2
Fetches curated job listings (no API key required for basic access).
"""

import logging
from typing import Dict, List

from src.utils.http_client import RateLimitedSession, safe_get

logger = logging.getLogger(__name__)

BASE_URL = "https://www.themuse.com/api/public/jobs"


class TheMuseExtractor:
    """Extract job listings from The Muse API v2."""

    def __init__(self):
        self.session = RateLimitedSession(calls_per_second=1.0)

    def search_jobs(
        self,
        category: str = "Data Science",
        max_pages: int = 5,
    ) -> List[Dict]:
        """
        Fetch jobs from The Muse with pagination.
        """
        all_jobs: List[Dict] = []

        for page in range(max_pages):
            params = {
                "category": category,
                "page": page,
            }

            data = safe_get(self.session, BASE_URL, params=params)
            if data is None:
                logger.warning("The Muse page %d returned no data, stopping.", page)
                break

            results = data.get("results", [])
            if not results:
                break

            for r in results:
                all_jobs.append(self._normalise(r))

            logger.info(
                "The Muse page %d: fetched %d jobs (total: %d)",
                page, len(results), len(all_jobs),
            )

        return all_jobs

    @staticmethod
    def _normalise(raw: Dict) -> Dict:
        """Map raw Muse response fields to our schema."""
        company = raw.get("company", {})
        locations = raw.get("locations", [])
        location_str = ", ".join(loc.get("name", "") for loc in locations)

        return {
            "source": "themuse",
            "source_id": str(raw.get("id", "")),
            "title": raw.get("name", "").strip(),
            "company_name": company.get("name", "").strip() if company else "",
            "location": location_str,
            "salary_min": None,  # Muse doesn't provide salary data
            "salary_max": None,
            "description": raw.get("contents", ""),
            "posted_date": raw.get("publication_date"),
        }
