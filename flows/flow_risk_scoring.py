"""
Flow 5: Score Jobs for AI Automation Risk

Trains the risk prediction model on existing job descriptions,
then scores every job and stores the risk_score and risk_category
back in PostgreSQL.
"""

import logging

from prefect import flow, task
from sqlalchemy import text

from src.models.database import SessionLocal, engine
from src.models.schemas import Job
from src.ml.risk_predictor import train_model, predict_risk
from src.ml.seed_occupations import seed_occupations

logger = logging.getLogger(__name__)


@task(name="seed_occupation_data")
def seed_occupations_task():
    """Populate the occupations table with known automation risk data."""
    count = seed_occupations()
    return count


@task(name="train_risk_model")
def train_risk_model():
    """Train the automation risk model on all job descriptions in the DB."""
    session = SessionLocal()
    try:
        jobs = session.query(Job).filter(Job.description.isnot(None)).all()
        descriptions = [j.description for j in jobs if j.description and len(j.description) > 20]
        print(f"   Training on {len(descriptions)} job descriptions...")

        if len(descriptions) < 10:
            print("   ⚠️  Not enough descriptions to train. Need at least 10.")
            return None

        report = train_model(descriptions)
        return report
    finally:
        session.close()


@task(name="score_all_jobs")
def score_all_jobs():
    """Score every unscored job in the database with automation risk."""
    session = SessionLocal()
    scored = 0
    try:
        jobs = (
            session.query(Job)
            .filter(Job.description.isnot(None))
            .filter(Job.risk_score.is_(None))
            .all()
        )
        print(f"   Scoring {len(jobs)} unscored jobs...")

        for job in jobs:
            if not job.description or len(job.description) < 20:
                continue
            try:
                score, category = predict_risk(job.description)
                job.risk_score = score
                job.risk_category = category
                scored += 1
            except Exception as e:
                logger.warning("Failed to score job %d: %s", job.job_id, e)
                continue

        session.commit()
        logger.info("Scored %d jobs", scored)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return scored


@task(name="create_risk_analytics_views")
def create_risk_views():
    """Create SQL views for the automation risk dashboards."""
    views = {
        "vw_risk_distribution": """
            CREATE OR REPLACE VIEW vw_risk_distribution AS
            SELECT
                risk_category,
                COUNT(*) AS job_count,
                ROUND((COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0))::numeric, 1) AS percentage
            FROM jobs
            WHERE risk_category IS NOT NULL
            GROUP BY risk_category
            ORDER BY
                CASE risk_category
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                END;
        """,
        "vw_risk_by_title": """
            CREATE OR REPLACE VIEW vw_risk_by_title AS
            SELECT
                title,
                COUNT(*) AS job_count,
                ROUND(AVG(risk_score)::numeric * 100, 1) AS avg_risk_pct,
                MODE() WITHIN GROUP (ORDER BY risk_category) AS most_common_risk
            FROM jobs
            WHERE risk_score IS NOT NULL
            GROUP BY title
            HAVING COUNT(*) >= 2
            ORDER BY avg_risk_pct DESC;
        """,
        "vw_high_risk_jobs": """
            CREATE OR REPLACE VIEW vw_high_risk_jobs AS
            SELECT
                j.title,
                c.company_name,
                j.location,
                ROUND((j.risk_score * 100)::numeric, 1) AS risk_pct,
                j.risk_category,
                j.source
            FROM jobs j
            LEFT JOIN companies c ON j.company_id = c.company_id
            WHERE j.risk_category = 'High'
            ORDER BY j.risk_score DESC;
        """,
        "vw_low_risk_jobs": """
            CREATE OR REPLACE VIEW vw_low_risk_jobs AS
            SELECT
                j.title,
                c.company_name,
                j.location,
                ROUND((j.risk_score * 100)::numeric, 1) AS risk_pct,
                j.risk_category,
                j.source
            FROM jobs j
            LEFT JOIN companies c ON j.company_id = c.company_id
            WHERE j.risk_category = 'Low'
            ORDER BY j.risk_score ASC;
        """,
        "vw_risk_by_source": """
            CREATE OR REPLACE VIEW vw_risk_by_source AS
            SELECT
                source,
                COUNT(*) AS total_jobs,
                COUNT(*) FILTER (WHERE risk_category = 'High') AS high_risk,
                COUNT(*) FILTER (WHERE risk_category = 'Medium') AS medium_risk,
                COUNT(*) FILTER (WHERE risk_category = 'Low') AS low_risk,
                ROUND(AVG(risk_score)::numeric * 100, 1) AS avg_risk_pct
            FROM jobs
            WHERE risk_score IS NOT NULL
            GROUP BY source;
        """,
        "vw_risk_by_company": """
            CREATE OR REPLACE VIEW vw_risk_by_company AS
            SELECT
                c.company_name,
                COUNT(*) AS total_jobs,
                ROUND(AVG(j.risk_score)::numeric * 100, 1) AS avg_risk_pct,
                COUNT(*) FILTER (WHERE j.risk_category = 'High') AS high_risk_jobs,
                COUNT(*) FILTER (WHERE j.risk_category = 'Low') AS low_risk_jobs
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            WHERE j.risk_score IS NOT NULL
            GROUP BY c.company_name
            HAVING COUNT(*) >= 3
            ORDER BY avg_risk_pct DESC;
        """,
        "vw_occupation_risk": """
            CREATE OR REPLACE VIEW vw_occupation_risk AS
            SELECT
                occupation_name,
                ROUND((automation_score * 100)::numeric, 1) AS automation_risk_pct,
                CASE
                    WHEN automation_score >= 0.7 THEN 'High'
                    WHEN automation_score >= 0.3 THEN 'Medium'
                    ELSE 'Low'
                END AS risk_category
            FROM occupations
            ORDER BY automation_score DESC;
        """,
    }

    with engine.connect() as conn:
        for name, sql in views.items():
            conn.execute(text(sql))
            print(f"   ✅ {name}")
        conn.commit()

    return len(views)


@flow(name="score_automation_risk", log_prints=True)
def score_automation_risk():
    """
    Full automation risk pipeline:
    1. Seed occupation data
    2. Train ML model on job descriptions
    3. Score all unscored jobs
    4. Create analytics views
    """
    print("🚀 Starting AI automation risk scoring pipeline...")

    # Step 1: Seed occupations
    occ_count = seed_occupations_task()
    print(f"📋 Seeded {occ_count} occupations with known risk data")

    # Step 2: Train model
    report = train_risk_model()
    if report:
        print(f"🤖 Model trained — Accuracy: {report.get('accuracy', 'N/A'):.1%}")
    else:
        print("⚠️  Model training skipped (not enough data)")
        return

    # Step 3: Score all jobs
    scored = score_all_jobs()
    print(f"📊 Scored {scored} jobs with automation risk")

    # Step 4: Create analytics views
    view_count = create_risk_views()
    print(f"✅ Created {view_count} risk analytics views")

    return scored


if __name__ == "__main__":
    score_automation_risk()
