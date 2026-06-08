"""
IndianAPI Jobs Extractor.

Docs: https://indianapi.in/documentation/jobs-api
Fetches job postings scraped from across the internet via IndianAPI.in.
"""

import os
import time
import logging
from typing import Dict, List, Optional

from dotenv import load_dotenv

from src.utils.http_client import RateLimitedSession

load_dotenv()
logger = logging.getLogger(__name__)

BASE_URL = "https://jobs.indianapi.in/jobs"


class IndianAPIExtractor:
    """Extract job listings from the IndianAPI Jobs API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("INDIANAPI_KEY", "")
        self.session = RateLimitedSession(calls_per_second=0.3)  # ~1 req per 3s for free tier
        self.session.headers.update({
            "X-Api-Key": self.api_key,
        })

    def search_jobs(
        self,
        title: Optional[str] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        experience: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Fetch job listings from IndianAPI with optional filters.

        Parameters
        ----------
        title : str, optional
            Search for jobs by title (e.g. "data engineer").
        location : str, optional
            Filter by location (e.g. "Bangalore").
        company : str, optional
            Filter by company name.
        experience : str, optional
            Filter by experience level (e.g. "Fresher", "2-5 years").
        job_type : str, optional
            Filter by type (e.g. "Full Time", "Part Time").
        limit : int
            Number of job listings to return.
        """
        params: Dict[str, str] = {"limit": str(limit)}
        time.sleep(3)  # Respect free-tier rate limits
        if title:
            params["title"] = title
        if location:
            params["location"] = location
        if company:
            params["company"] = company
        if experience:
            params["experience"] = experience
        if job_type:
            params["job_type"] = job_type

        all_jobs: List[Dict] = []

        try:
            resp = self.session.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("IndianAPI jobs request failed: %s", exc)
            return all_jobs

        # Response is a list of job dicts
        if isinstance(data, list):
            for item in data:
                all_jobs.append(self._normalise(item))
        elif isinstance(data, dict) and "jobs" in data:
            for item in data["jobs"]:
                all_jobs.append(self._normalise(item))

        logger.info(
            "IndianAPI (title=%s, location=%s): %d jobs",
            title, location, len(all_jobs),
        )
        return all_jobs

    @staticmethod
    def _normalise(raw: Dict) -> Dict:
        """Map IndianAPI response fields to our internal schema."""
        return {
            "source": "indianapi",
            "source_id": str(raw.get("id", "")),
            "title": (raw.get("job_title") or raw.get("title", "")).strip(),
            "company_name": (raw.get("company") or "").strip(),
            "location": (raw.get("location") or "").strip(),
            "salary_min": None,  # IndianAPI doesn't provide salary fields
            "salary_max": None,
            "description": (raw.get("job_description") or "").strip(),
            "posted_date": raw.get("posted_date"),
        }
