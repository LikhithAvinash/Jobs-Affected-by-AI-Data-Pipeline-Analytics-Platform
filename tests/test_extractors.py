"""
Tests for src/extractors/ – mocked API responses.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.extractors.adzuna import AdzunaExtractor
from src.extractors.themuse import TheMuseExtractor


class TestAdzunaExtractor:
    """Tests for the Adzuna API extractor."""

    @patch("src.extractors.adzuna.safe_get")
    def test_search_jobs_returns_normalised_data(self, mock_get):
        mock_get.return_value = {
            "results": [
                {
                    "id": 12345,
                    "title": "Data Engineer",
                    "company": {"display_name": "Acme Corp"},
                    "location": {"display_name": "New York, NY"},
                    "salary_min": 90000,
                    "salary_max": 130000,
                    "description": "Build data pipelines",
                    "created": "2025-01-15T00:00:00Z",
                }
            ]
        }

        extractor = AdzunaExtractor(app_id="test", app_key="test")
        jobs = extractor.search_jobs(query="data engineer", max_pages=1)

        assert len(jobs) == 1
        assert jobs[0]["source"] == "adzuna"
        assert jobs[0]["title"] == "Data Engineer"
        assert jobs[0]["company_name"] == "Acme Corp"

    @patch("src.extractors.adzuna.safe_get")
    def test_handles_empty_response(self, mock_get):
        mock_get.return_value = {"results": []}

        extractor = AdzunaExtractor(app_id="test", app_key="test")
        jobs = extractor.search_jobs(query="xyz", max_pages=1)
        assert len(jobs) == 0

    @patch("src.extractors.adzuna.safe_get")
    def test_handles_none_response(self, mock_get):
        mock_get.return_value = None

        extractor = AdzunaExtractor(app_id="test", app_key="test")
        jobs = extractor.search_jobs(query="xyz", max_pages=1)
        assert len(jobs) == 0


class TestTheMuseExtractor:
    """Tests for The Muse API extractor."""

    @patch("src.extractors.themuse.safe_get")
    def test_normalises_muse_response(self, mock_get):
        mock_get.return_value = {
            "results": [
                {
                    "id": 999,
                    "name": "ML Engineer",
                    "company": {"name": "TechCo"},
                    "locations": [{"name": "San Francisco, CA"}],
                    "contents": "<p>Train models</p>",
                    "publication_date": "2025-02-01",
                }
            ]
        }

        extractor = TheMuseExtractor()
        jobs = extractor.search_jobs(category="Data Science", max_pages=1)

        assert len(jobs) == 1
        assert jobs[0]["source"] == "themuse"
        assert jobs[0]["title"] == "ML Engineer"
        assert jobs[0]["salary_min"] is None  # Muse doesn't provide salary
