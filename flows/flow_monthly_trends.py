"""
Flow 3: Extract Employment & Research Trends (Monthly)

Pulls arXiv papers and BLS employment data.
"""

import logging

from prefect import flow, task

from src.extractors.arxiv import ArxivExtractor
from src.extractors.bls import BLSExtractor
from src.transformers.cleaners import clean_arxiv_papers, clean_bls_trends
from src.loaders.db_loader import load_arxiv_papers

logger = logging.getLogger(__name__)


@task(name="extract_arxiv_papers", retries=2, retry_delay_seconds=120)
def extract_arxiv():
    """Fetch recent AI/ML papers from arXiv."""
    extractor = ArxivExtractor()
    return extractor.search_papers(max_results=200)


@task(name="extract_bls_data", retries=2, retry_delay_seconds=60)
def extract_bls():
    """Fetch employment trends from BLS."""
    extractor = BLSExtractor()
    return extractor.fetch_occupation_trends()


@task(name="transform_arxiv")
def transform_arxiv(raw_papers: list):
    """Clean arXiv paper data."""
    return clean_arxiv_papers(raw_papers)


@task(name="load_papers")
def load_papers(df):
    """Load arXiv papers to DB."""
    return load_arxiv_papers(df)


@flow(name="monthly_trend_extraction", log_prints=True)
def monthly_trend_extraction():
    """
    Monthly flow: Refresh research and employment trend data.
    """
    print("🚀 Starting monthly trend extraction...")

    # arXiv pipeline
    raw_papers = extract_arxiv()
    print(f"📄 Extracted {len(raw_papers)} arXiv papers")

    df_papers = transform_arxiv(raw_papers)
    print(f"🧹 After cleaning: {len(df_papers)} papers")

    paper_count = load_papers(df_papers)
    print(f"✅ Loaded {paper_count} new arXiv papers")

    # BLS pipeline
    bls_data = extract_bls()
    total_points = sum(len(v) for v in bls_data.values())
    print(f"📊 Fetched {total_points} BLS data points across {len(bls_data)} occupations")

    return {"papers": paper_count, "bls_points": total_points}


if __name__ == "__main__":
    monthly_trend_extraction()
