"""
Shared utilities for API extractors.

Provides:
  - RateLimitedSession: requests.Session with built-in rate limiting & retries
  - safe_get: convenience wrapper for GET requests with error handling
"""

import time
import logging
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class RateLimitedSession(requests.Session):
    """
    A requests.Session subclass that enforces a minimum delay between
    consecutive requests and retries on transient failures.
    """

    def __init__(self, calls_per_second: float = 2.0, retries: int = 3):
        super().__init__()
        self._min_interval = 1.0 / calls_per_second
        self._last_call = 0.0

        # Mount a retry adapter for transient HTTP errors
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.mount("https://", adapter)
        self.mount("http://", adapter)

    def request(self, method, url, **kwargs):
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

        self._last_call = time.time()
        return super().request(method, url, **kwargs)


def safe_get(
    session: requests.Session,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Optional[Dict]:
    """
    Perform a GET request and return the JSON response.
    Returns None on failure instead of raising.
    """
    try:
        resp = session.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        logger.error("GET %s failed: %s", url, exc)
        return None
