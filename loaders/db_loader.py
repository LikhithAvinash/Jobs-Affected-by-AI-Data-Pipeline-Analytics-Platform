"""
Database loaders – upsert cleaned data into PostgreSQL.

Uses SQLAlchemy merge (upsert semantics) to avoid duplicates.
"""

import math
import logging
from typing import Any, List

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.models.database import SessionLocal
from src.models.schemas import (
    AIResearchTrend,
    Company,
    Job,
    JobSkill,
    Skill,
)
from src.transformers.cleaners import extract_skills_from_description

logger = logging.getLogger(__name__)


def _sanitize(value: Any) -> Any:
    """Convert pandas NaN / NaT / numpy NaN to Python None for DB safety."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    return value


def _get_or_create_company(session: Session, name: str) -> int:
    """Return company_id for the given name, creating if necessary."""
    if not name:
        return None
    company = session.query(Company).filter_by(company_name=name).first()
    if company:
        return company.company_id
    new = Company(company_name=name)
    session.add(new)
    session.flush()
    return new.company_id


def _get_or_create_skill(session: Session, name: str) -> int:
    """Return skill_id for the given name, creating if necessary."""
    skill = session.query(Skill).filter_by(skill_name=name).first()
    if skill:
        return skill.skill_id
    new = Skill(skill_name=name)
    session.add(new)
    session.flush()
    return new.skill_id


def load_jobs(df: pd.DataFrame) -> int:
    """
    Load cleaned job records into the database.
    Returns the number of new jobs inserted.
    """
    if df.empty:
        return 0

    session = SessionLocal()
    inserted = 0

    try:
        for _, row in df.iterrows():
            # Check for existing job (upsert logic)
            existing = (
                session.query(Job)
                .filter_by(source=row["source"], source_id=row["source_id"])
                .first()
            )
            if existing:
                continue

            company_id = _get_or_create_company(session, row.get("company_name"))

            job = Job(
                company_id=company_id,
                title=row["title"],
                location=row.get("location"),
                salary_min=_sanitize(row.get("salary_min")),
                salary_max=_sanitize(row.get("salary_max")),
                description=row.get("description"),
                posted_date=_sanitize(row.get("posted_date")),
                source=row["source"],
                source_id=row["source_id"],
            )
            session.add(job)
            session.flush()

            # Extract and link skills from description
            skills = extract_skills_from_description(row.get("description", ""))
            for skill_name in skills:
                skill_id = _get_or_create_skill(session, skill_name)
                js = JobSkill(job_id=job.job_id, skill_id=skill_id)
                session.add(js)

            inserted += 1

        session.commit()
        logger.info("Loaded %d new jobs into the database", inserted)
    except Exception:
        session.rollback()
        logger.exception("Failed to load jobs")
        raise
    finally:
        session.close()

    return inserted


def load_arxiv_papers(df: pd.DataFrame) -> int:
    """
    Load cleaned arXiv papers into the database.
    Returns the number of new papers inserted.
    """
    if df.empty:
        return 0

    session = SessionLocal()
    inserted = 0

    try:
        for _, row in df.iterrows():
            existing = (
                session.query(AIResearchTrend)
                .filter_by(arxiv_id=row["arxiv_id"])
                .first()
            )
            if existing:
                continue

            paper = AIResearchTrend(
                arxiv_id=row["arxiv_id"],
                title=row["title"],
                category=row.get("category"),
                published_date=row.get("published_date"),
            )
            session.add(paper)
            inserted += 1

        session.commit()
        logger.info("Loaded %d new arXiv papers", inserted)
    except Exception:
        session.rollback()
        logger.exception("Failed to load arXiv papers")
        raise
    finally:
        session.close()

    return inserted
