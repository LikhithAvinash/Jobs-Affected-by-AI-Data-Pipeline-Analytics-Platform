"""
Flow 4: Refresh Dashboard Materialized Views (Nightly)

Runs SQL aggregation queries to prepare analytics tables for Grafana.
"""

import logging

from prefect import flow, task
from sqlalchemy import text

from src.models.database import engine

logger = logging.getLogger(__name__)

# ── Analytics view definitions ──
ANALYTICS_VIEWS = {
    "vw_skill_demand": """
        CREATE OR REPLACE VIEW vw_skill_demand AS
        SELECT
            s.skill_name,
            COUNT(js.job_id) AS job_count,
            ROUND(AVG(j.salary_min)::numeric, 2) AS avg_salary_min,
            ROUND(AVG(j.salary_max)::numeric, 2) AS avg_salary_max
        FROM skills s
        JOIN job_skills js ON s.skill_id = js.skill_id
        JOIN jobs j ON js.job_id = j.job_id
        GROUP BY s.skill_name
        ORDER BY job_count DESC;
    """,

    "vw_jobs_by_source": """
        CREATE OR REPLACE VIEW vw_jobs_by_source AS
        SELECT
            source,
            COUNT(*) AS total_jobs,
            COUNT(DISTINCT company_id) AS unique_companies,
            ROUND(AVG(salary_min)::numeric, 2) AS avg_salary_min,
            ROUND(AVG(salary_max)::numeric, 2) AS avg_salary_max
        FROM jobs
        GROUP BY source;
    """,

    "vw_top_companies": """
        CREATE OR REPLACE VIEW vw_top_companies AS
        SELECT
            c.company_name,
            c.industry,
            COUNT(j.job_id) AS job_count,
            ROUND(AVG(j.salary_max)::numeric, 2) AS avg_max_salary
        FROM companies c
        JOIN jobs j ON c.company_id = j.company_id
        GROUP BY c.company_name, c.industry
        ORDER BY job_count DESC
        LIMIT 50;
    """,

    "vw_ai_research_by_category": """
        CREATE OR REPLACE VIEW vw_ai_research_by_category AS
        SELECT
            category,
            COUNT(*) AS paper_count,
            MIN(published_date) AS earliest,
            MAX(published_date) AS latest
        FROM ai_research_trends
        GROUP BY category
        ORDER BY paper_count DESC;
    """,

    "vw_daily_job_postings": """
        CREATE OR REPLACE VIEW vw_daily_job_postings AS
        SELECT
            posted_date,
            source,
            COUNT(*) AS jobs_posted
        FROM jobs
        WHERE posted_date IS NOT NULL
        GROUP BY posted_date, source
        ORDER BY posted_date DESC;
    """,
}


@task(name="refresh_analytics_view")
def refresh_view(name: str, sql: str):
    """Create or replace a single analytics view."""
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    logger.info("Refreshed view: %s", name)


@flow(name="nightly_dashboard_refresh", log_prints=True)
def nightly_dashboard_refresh():
    """
    Nightly flow: Recreate all analytics views for Grafana.
    """
    print("🚀 Refreshing analytics views...")

    for name, sql in ANALYTICS_VIEWS.items():
        refresh_view(name, sql)
        print(f"   ✅ {name}")

    print(f"✅ Refreshed {len(ANALYTICS_VIEWS)} analytics views")


if __name__ == "__main__":
    nightly_dashboard_refresh()
