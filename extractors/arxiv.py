"""
arXiv API Extractor.

Docs: https://info.arxiv.org/help/api/index.html
Fetches recent AI/ML research papers via the Atom feed API.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List

from src.utils.http_client import RateLimitedSession

logger = logging.getLogger(__name__)

BASE_URL = "http://export.arxiv.org/api/query"

# arXiv Atom feed namespaces
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


class ArxivExtractor:
    """Extract AI research papers from arXiv."""

    def __init__(self):
        self.session = RateLimitedSession(calls_per_second=0.5)  # arXiv is strict

    def search_papers(
        self,
        query: str = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
        max_results: int = 200,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> List[Dict]:
        """
        Search for recent AI/ML papers on arXiv.
        """
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        resp = self.session.get(BASE_URL, params=params, timeout=60)
        resp.raise_for_status()

        return self._parse_feed(resp.text)

    @staticmethod
    def _parse_feed(xml_text: str) -> List[Dict]:
        """Parse the Atom XML feed into a list of paper dicts."""
        root = ET.fromstring(xml_text)
        papers: List[Dict] = []

        for entry in root.findall("atom:entry", NS):
            arxiv_id_url = entry.findtext("atom:id", "", NS)
            arxiv_id = arxiv_id_url.split("/abs/")[-1] if "/abs/" in arxiv_id_url else arxiv_id_url

            # Extract primary category
            primary_cat_el = entry.find("arxiv:primary_category", NS)
            category = primary_cat_el.get("term", "") if primary_cat_el is not None else ""

            papers.append({
                "arxiv_id": arxiv_id.strip(),
                "title": entry.findtext("atom:title", "", NS).strip().replace("\n", " "),
                "category": category,
                "published_date": entry.findtext("atom:published", "", NS)[:10],  # YYYY-MM-DD
            })

        logger.info("arXiv: parsed %d papers", len(papers))
        return papers
