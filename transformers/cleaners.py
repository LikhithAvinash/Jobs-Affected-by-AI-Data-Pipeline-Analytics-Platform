"""
Data transformers for cleaning and normalising extracted data.

Each function takes raw extracted dicts and returns cleaned pandas DataFrames.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

# ── Skills to detect in job descriptions ──
SKILL_PATTERNS = [
    "python", "sql", "java", "javascript", "typescript", "r",
    "docker", "kubernetes", "terraform", "ansible",
    "aws", "azure", "gcp", "snowflake",
    "spark", "hadoop", "kafka", "airflow", "prefect", "dbt",
    "pytorch", "tensorflow", "scikit-learn", "langchain",
    "pandas", "numpy", "matplotlib",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "fastapi", "flask", "django", "react", "node.js",
    "git", "ci/cd", "linux", "agile",
    "machine learning", "deep learning", "nlp", "computer vision",
    "data engineering", "mlops", "devops",
]

# Pre-compile patterns for efficiency (word-boundary match)
_COMPILED_SKILLS = {
    skill: re.compile(rf"\b{re.escape(skill)}\b", re.IGNORECASE)
    for skill in SKILL_PATTERNS
}


def clean_jobs(raw_jobs: List[Dict]) -> pd.DataFrame:
    """
    Clean and normalise a list of raw job dicts into a DataFrame.

    Steps:
      1. Drop duplicates by (source, source_id)
      2. Standardise title casing
      3. Parse posted_date into datetime.date
      4. Coerce salary fields to float
      5. Strip HTML from descriptions
    """
    if not raw_jobs:
        return pd.DataFrame()

    df = pd.DataFrame(raw_jobs)

    # Deduplicate
    df = df.drop_duplicates(subset=["source", "source_id"], keep="first")

    # Title: title-case, strip whitespace
    df["title"] = df["title"].str.strip().str.title()

    # Company name: strip
    df["company_name"] = df["company_name"].str.strip()

    # Parse posted_date
    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce").dt.date

    # Coerce salaries
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")

    # Strip HTML tags from description
    df["description"] = df["description"].apply(_strip_html)

    logger.info("Cleaned %d job records", len(df))
    return df


def extract_skills_from_description(description: str) -> List[str]:
    """
    Extract skill mentions from a job description using regex matching.
    Returns a deduplicated list of skill names found.
    """
    if not description:
        return []

    found = []
    for skill, pattern in _COMPILED_SKILLS.items():
        if pattern.search(description):
            found.append(skill)

    return found


def clean_arxiv_papers(raw_papers: List[Dict]) -> pd.DataFrame:
    """Clean arXiv paper data."""
    if not raw_papers:
        return pd.DataFrame()

    df = pd.DataFrame(raw_papers)
    df = df.drop_duplicates(subset=["arxiv_id"], keep="first")
    df["title"] = df["title"].str.strip()
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce").dt.date

    logger.info("Cleaned %d arXiv papers", len(df))
    return df


def clean_bls_trends(raw_data: List[Dict]) -> pd.DataFrame:
    """Clean BLS time-series data."""
    if not raw_data:
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])

    logger.info("Cleaned %d BLS data points", len(df))
    return df


def _strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    if not isinstance(text, str):
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()
