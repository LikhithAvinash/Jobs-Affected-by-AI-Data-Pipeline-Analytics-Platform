"""
USAJobs API Extractor.

Docs: https://developer.usajobs.gov/api-reference/get-api-search
Fetches federal government job postings.
"""

import os
import logging
from typing import Dict, List, Optional

from dotenv import load_dotenv

from src.utils.http_client import RateLimitedSession, safe_get

load_dotenv()
logger = logging.getLogger(__name__)

BASE_URL = "https://data.usajobs.gov/api/search"


class USAJobsExtractor:
    """Extract job listings from the USAJobs API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("USAJOBS_API_KEY", "")
        self.user_agent = user_agent or os.getenv("USAJOBS_USER_AGENT", "")
        self.session = RateLimitedSession(calls_per_second=1.0)
        self.session.headers.update({
            "Authorization-Key": self.api_key,
            "User-Agent": self.user_agent,
            "Host": "data.usajobs.gov",
        })

    def search_jobs(
        self,
        keyword: str = "data engineer",
        results_per_page: int = 50,
        max_pages: int = 5,
    ) -> List[Dict]:
        """
        Search for USAJobs postings with pagination.
        """
        all_jobs: List[Dict] = []

        for page in range(1, max_pages + 1):
            params = {
                "Keyword": keyword,
                "ResultsPerPage": results_per_page,
                "Page": page,
            }

            data = safe_get(self.session, BASE_URL, params=params)
            if data is None:
                logger.warning("USAJobs page %d returned no data, stopping.", page)
                break

            search_result = data.get("SearchResult", {})
            items = search_result.get("SearchResultItems", [])
            if not items:
                break

            for item in items:
                all_jobs.append(self._normalise(item))

            logger.info(
                "USAJobs page %d: fetched %d jobs (total: %d)",
                page, len(items), len(all_jobs),
            )

        return all_jobs

    @staticmethod
    def _normalise(raw: Dict) -> Dict:
        """Map raw USAJobs response fields to our schema."""
        mp = raw.get("MatchedObjectDescriptor", {})
        position = mp.get("PositionLocation", [{}])
        location = position[0].get("LocationName", "") if position else ""

        remuneration = mp.get("PositionRemuneration", [{}])
        salary_min = None
        salary_max = None
        if remuneration:
            salary_min = remuneration[0].get("MinimumRange")
            salary_max = remuneration[0].get("MaximumRange")
            try:
                salary_min = float(salary_min) if salary_min else None
                salary_max = float(salary_max) if salary_max else None
            except (ValueError, TypeError):
                salary_min, salary_max = None, None

        return {
            "source": "usajobs",
            "source_id": mp.get("PositionID", ""),
            "title": mp.get("PositionTitle", "").strip(),
            "company_name": mp.get("OrganizationName", "").strip(),
            "location": location,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "description": mp.get("QualificationSummary", ""),
            "posted_date": mp.get("PublicationStartDate"),
        }
