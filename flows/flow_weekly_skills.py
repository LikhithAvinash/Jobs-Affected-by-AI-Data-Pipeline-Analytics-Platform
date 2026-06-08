"""
Flow 2: Extract Skill & Occupation Data (Weekly)

Pulls tag popularity from Stack Exchange and stores skill demand data.
"""

import logging

from prefect import flow, task

from src.extractors.stackexchange import StackExchangeExtractor
from src.models.database import SessionLocal
from src.models.schemas import Skill

logger = logging.getLogger(__name__)


@task(name="extract_skill_trends", retries=2, retry_delay_seconds=60)
def extract_skill_trends():
    """Fetch tag info from Stack Overflow."""
    extractor = StackExchangeExtractor()
    return extractor.fetch_tag_info()


@task(name="load_skills_to_db")
def load_skills(tag_data: list):
    """Ensure all tracked skills exist in the skills table."""
    session = SessionLocal()
    created = 0
    try:
        for item in tag_data:
            name = item["skill_name"]
            existing = session.query(Skill).filter_by(skill_name=name).first()
            if not existing:
                session.add(Skill(skill_name=name))
                created += 1
        session.commit()
        logger.info("Created %d new skills", created)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return created


@flow(name="weekly_skill_extraction", log_prints=True)
def weekly_skill_extraction():
    """
    Weekly flow: Refresh skill demand data from Stack Overflow.
    """
    print("🚀 Starting weekly skill extraction...")

    tag_data = extract_skill_trends()
    print(f"📊 Fetched info for {len(tag_data)} skills")

    created = load_skills(tag_data)
    print(f"✅ Created {created} new skill records")

    # Log top skills by question count
    sorted_tags = sorted(tag_data, key=lambda x: x.get("question_count", 0), reverse=True)
    print("\n📈 Top 10 Skills by SO Question Count:")
    for t in sorted_tags[:10]:
        print(f"   • {t['skill_name']}: {t['question_count']:,}")

    return tag_data


if __name__ == "__main__":
    weekly_skill_extraction()
