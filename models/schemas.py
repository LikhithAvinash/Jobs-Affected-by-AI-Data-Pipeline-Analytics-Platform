"""
SQLAlchemy ORM models for the Job Market Intelligence data warehouse.

Tables:
  - companies
  - jobs
  - skills
  - job_skills  (association)
  - occupations
  - employment_trends
  - ai_research_trends
"""

from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.models.database import Base


# ──────────────────────────────────────────────
# Companies
# ──────────────────────────────────────────────
class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, unique=True)
    industry = Column(String(255))
    website = Column(String(512))

    # relationships
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(id={self.company_id}, name='{self.company_name}')>"


# ──────────────────────────────────────────────
# Jobs
# ──────────────────────────────────────────────
class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=True)
    title = Column(String(512), nullable=False)
    location = Column(String(255))
    salary_min = Column(Float)
    salary_max = Column(Float)
    description = Column(Text)
    posted_date = Column(Date)
    source = Column(String(50))  # e.g. 'adzuna', 'indianapi', 'themuse'
    source_id = Column(String(255))  # original id from the source API
    risk_score = Column(Float)       # 0.0 – 1.0 automation risk
    risk_category = Column(String(20))  # 'Low', 'Medium', 'High'

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_job_source"),
    )

    # relationships
    company = relationship("Company", back_populates="jobs")
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.job_id}, title='{self.title}')>"


# ──────────────────────────────────────────────
# Skills
# ──────────────────────────────────────────────
class Skill(Base):
    __tablename__ = "skills"

    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    skill_name = Column(String(255), nullable=False, unique=True)

    # relationships
    jobs = relationship("JobSkill", back_populates="skill")

    def __repr__(self):
        return f"<Skill(id={self.skill_id}, name='{self.skill_name}')>"


# ──────────────────────────────────────────────
# Job ↔ Skill association
# ──────────────────────────────────────────────
class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id = Column(Integer, ForeignKey("jobs.job_id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.skill_id"), primary_key=True)

    # relationships
    job = relationship("Job", back_populates="skills")
    skill = relationship("Skill", back_populates="jobs")


# ──────────────────────────────────────────────
# Occupations (O*NET data)
# ──────────────────────────────────────────────
class Occupation(Base):
    __tablename__ = "occupations"

    occupation_id = Column(Integer, primary_key=True, autoincrement=True)
    onet_code = Column(String(20), unique=True)
    occupation_name = Column(String(512), nullable=False)
    automation_score = Column(Float)  # 0.0 – 1.0

    # relationships
    trends = relationship(
        "EmploymentTrend", back_populates="occupation", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Occupation(id={self.occupation_id}, name='{self.occupation_name}')>"


# ──────────────────────────────────────────────
# Employment Trends (BLS data)
# ──────────────────────────────────────────────
class EmploymentTrend(Base):
    __tablename__ = "employment_trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    occupation_id = Column(
        Integer, ForeignKey("occupations.occupation_id"), nullable=False
    )
    year = Column(Integer, nullable=False)
    growth_rate = Column(Float)
    median_salary = Column(Float)

    __table_args__ = (
        UniqueConstraint("occupation_id", "year", name="uq_trend_occ_year"),
    )

    # relationships
    occupation = relationship("Occupation", back_populates="trends")

    def __repr__(self):
        return f"<EmploymentTrend(occ={self.occupation_id}, year={self.year})>"


# ──────────────────────────────────────────────
# AI Research Trends (arXiv data)
# ──────────────────────────────────────────────
class AIResearchTrend(Base):
    __tablename__ = "ai_research_trends"

    paper_id = Column(Integer, primary_key=True, autoincrement=True)
    arxiv_id = Column(String(50), unique=True)
    title = Column(Text, nullable=False)
    category = Column(String(50))
    published_date = Column(Date)

    def __repr__(self):
        return f"<AIResearchTrend(id={self.paper_id}, title='{self.title[:40]}...')>"
