"""
Bureau of Labor Statistics (BLS) API Extractor.

Docs: https://www.bls.gov/developers/
Fetches employment and salary trend data for specified occupations.
"""

import logging
from typing import Dict, List, Optional

from src.utils.http_client import RateLimitedSession

logger = logging.getLogger(__name__)

BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


class BLSExtractor:
    """Extract employment & salary trend data from BLS."""

    # Common Occupational Employment & Wage Statistics (OEWS) series IDs
    # Format: OEUM{area}{area_type}{industry}{occupation}{data_type}
    # These are national-level series for key tech occupations
    SERIES_MAP = {
        "15-2051": {  # Data Scientists
            "employment": "OEUN000000000000015205101",
            "median_wage": "OEUN000000000000015205104",
        },
        "15-1252": {  # Software Developers
            "employment": "OEUN000000000000015125201",
            "median_wage": "OEUN000000000000015125204",
        },
        "15-2031": {  # Operations Research Analysts
            "employment": "OEUN000000000000015203101",
            "median_wage": "OEUN000000000000015203104",
        },
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key  # Optional; unauthenticated = 25 req/day
        self.session = RateLimitedSession(calls_per_second=0.5)

    def fetch_series(
        self,
        series_ids: List[str],
        start_year: int = 2019,
        end_year: int = 2025,
    ) -> List[Dict]:
        """
        Fetch time-series data for the given BLS series IDs.
        """
        payload = {
            "seriesid": series_ids,
            "startyear": str(start_year),
            "endyear": str(end_year),
        }
        if self.api_key:
            payload["registrationkey"] = self.api_key

        resp = self.session.post(BASE_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results: List[Dict] = []
        for series in data.get("Results", {}).get("series", []):
            sid = series.get("seriesID", "")
            for dp in series.get("data", []):
                results.append({
                    "series_id": sid,
                    "year": int(dp.get("year", 0)),
                    "period": dp.get("period", ""),
                    "value": dp.get("value", ""),
                })

        logger.info("BLS: fetched %d data points across %d series", len(results), len(series_ids))
        return results

    def fetch_occupation_trends(
        self, start_year: int = 2019, end_year: int = 2025
    ) -> Dict[str, List[Dict]]:
        """
        Convenience method: fetch employment & wage data for all mapped occupations.
        Returns a dict keyed by occupation code.
        """
        trends: Dict[str, List[Dict]] = {}

        for occ_code, series in self.SERIES_MAP.items():
            all_ids = list(series.values())
            raw = self.fetch_series(all_ids, start_year, end_year)
            trends[occ_code] = raw

        return trends
