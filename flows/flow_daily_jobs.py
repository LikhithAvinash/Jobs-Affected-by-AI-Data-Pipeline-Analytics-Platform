"""
Flow 1: Extract Job Listings (Daily)

Pulls job postings from Adzuna, USAJobs, and The Muse,
cleans them, and loads them into PostgreSQL.
"""

import logging

from prefect import flow, task

from src.extractors.adzuna import AdzunaExtractor
from src.extractors.indianapi import IndianAPIExtractor
from src.extractors.themuse import TheMuseExtractor
from src.transformers.cleaners import clean_jobs
from src.loaders.db_loader import load_jobs

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "data engineer",
    "machine learning engineer",
    "AI engineer",
    "data scientist",
    "MLOps engineer",
]


@task(name="extract_adzuna_jobs", retries=2, retry_delay_seconds=60)
def extract_adzuna(queries: list, max_pages: int = 3):
    """Extract jobs from Adzuna for multiple queries."""
    extractor = AdzunaExtractor()
    all_jobs = []
    for q in queries:
        jobs = extractor.search_jobs(query=q, max_pages=max_pages)
        all_jobs.extend(jobs)
        logger.info("Adzuna '%s': %d jobs", q, len(jobs))
    return all_jobs


@task(name="extract_indianapi_jobs", retries=2, retry_delay_seconds=60)
def extract_indianapi(queries: list, limit: int = 10):
    """Extract jobs from IndianAPI for multiple queries."""
    extractor = IndianAPIExtractor()
    all_jobs = []
    for q in queries:
        jobs = extractor.search_jobs(title=q, limit=limit)
        all_jobs.extend(jobs)
        logger.info("IndianAPI '%s': %d jobs", q, len(jobs))
    return all_jobs


@task(name="extract_themuse_jobs", retries=2, retry_delay_seconds=60)
def extract_themuse():
    """Extract jobs from The Muse."""
    extractor = TheMuseExtractor()
    categories = ["Data Science", "Engineering", "IT"]
    all_jobs = []
    for cat in categories:
        jobs = extractor.search_jobs(category=cat, max_pages=3)
        all_jobs.extend(jobs)
        logger.info("The Muse '%s': %d jobs", cat, len(jobs))
    return all_jobs


@task(name="transform_jobs")
def transform(raw_jobs: list):
    """Clean and normalise job data."""
    return clean_jobs(raw_jobs)


@task(name="load_jobs_to_db")
def load(df):
    """Load cleaned jobs into PostgreSQL."""
    count = load_jobs(df)
    logger.info("Loaded %d new jobs", count)
    return count


@flow(name="daily_job_extraction", log_prints=True)
def daily_job_extraction():
    """
    Daily flow: Extract → Transform → Load job listings.
    """
    print("🚀 Starting daily job extraction pipeline...")

    # Extract from all sources in parallel
    adzuna_jobs = extract_adzuna(SEARCH_QUERIES)
    indianapi_jobs = extract_indianapi(SEARCH_QUERIES)
    muse_jobs = extract_themuse()

    # Combine all results
    all_raw = adzuna_jobs + indianapi_jobs + muse_jobs
    print(f"📊 Total raw jobs extracted: {len(all_raw)}")

    # Transform
    df = transform(all_raw)
    print(f"🧹 After cleaning: {len(df)} jobs")

    # Load
    inserted = load(df)
    print(f"✅ Inserted {inserted} new jobs into PostgreSQL")

    return inserted


if __name__ == "__main__":
    daily_job_extraction()
