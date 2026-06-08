"""
Tests for src/transformers/cleaners.py
"""

import pytest
import pandas as pd

from src.transformers.cleaners import (
    clean_jobs,
    extract_skills_from_description,
    clean_arxiv_papers,
    _strip_html,
)


class TestCleanJobs:
    """Tests for the clean_jobs transformer."""

    def test_empty_input(self):
        result = clean_jobs([])
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_deduplication(self):
        jobs = [
            {"source": "adzuna", "source_id": "1", "title": "data engineer",
             "company_name": "Acme", "location": "NYC", "salary_min": 100000,
             "salary_max": 150000, "description": "Build pipelines", "posted_date": "2025-01-15"},
            {"source": "adzuna", "source_id": "1", "title": "data engineer",
             "company_name": "Acme", "location": "NYC", "salary_min": 100000,
             "salary_max": 150000, "description": "Build pipelines", "posted_date": "2025-01-15"},
        ]
        result = clean_jobs(jobs)
        assert len(result) == 1

    def test_title_casing(self):
        jobs = [
            {"source": "test", "source_id": "1", "title": "SENIOR DATA ENGINEER",
             "company_name": "Co", "location": "", "salary_min": None,
             "salary_max": None, "description": "", "posted_date": None},
        ]
        result = clean_jobs(jobs)
        assert result.iloc[0]["title"] == "Senior Data Engineer"

    def test_salary_coercion(self):
        jobs = [
            {"source": "test", "source_id": "2", "title": "dev",
             "company_name": "Co", "location": "", "salary_min": "80000",
             "salary_max": "not_a_number", "description": "", "posted_date": None},
        ]
        result = clean_jobs(jobs)
        assert result.iloc[0]["salary_min"] == 80000.0
        assert pd.isna(result.iloc[0]["salary_max"])

    def test_html_stripping(self):
        jobs = [
            {"source": "test", "source_id": "3", "title": "dev",
             "company_name": "Co", "location": "", "salary_min": None,
             "salary_max": None, "description": "<p>Build <strong>stuff</strong></p>",
             "posted_date": None},
        ]
        result = clean_jobs(jobs)
        assert "<" not in result.iloc[0]["description"]
        assert "Build stuff" in result.iloc[0]["description"]


class TestExtractSkills:
    """Tests for skill extraction from descriptions."""

    def test_finds_python(self):
        skills = extract_skills_from_description("We need a Python developer with SQL experience")
        assert "python" in skills
        assert "sql" in skills

    def test_finds_frameworks(self):
        skills = extract_skills_from_description("Experience with PyTorch and TensorFlow required")
        assert "pytorch" in skills
        assert "tensorflow" in skills

    def test_empty_description(self):
        assert extract_skills_from_description("") == []
        assert extract_skills_from_description(None) == []

    def test_no_false_positives(self):
        skills = extract_skills_from_description("The manager will oversee the team")
        # Should not find random skills in unrelated text
        assert "python" not in skills
        assert "docker" not in skills


class TestCleanArxiv:
    """Tests for arXiv paper cleaning."""

    def test_deduplication(self):
        papers = [
            {"arxiv_id": "2401.00001", "title": "Paper A", "category": "cs.AI", "published_date": "2024-01-01"},
            {"arxiv_id": "2401.00001", "title": "Paper A dup", "category": "cs.AI", "published_date": "2024-01-01"},
        ]
        result = clean_arxiv_papers(papers)
        assert len(result) == 1


class TestStripHtml:
    """Tests for HTML stripping utility."""

    def test_removes_tags(self):
        assert _strip_html("<b>bold</b>") == "bold"

    def test_handles_none(self):
        assert _strip_html(None) == ""

    def test_handles_plain_text(self):
        assert _strip_html("no tags here") == "no tags here"
