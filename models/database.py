"""
Database connection engine and session factory.

Reads DATABASE_URL from environment (.env) and exposes:
  - engine:        SQLAlchemy Engine (singleton)
  - SessionLocal:  Session factory for per-request usage
  - Base:          Declarative base for ORM models
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pipeline_user:pipeline_pass@localhost:5432/job_market_db",
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session():
    """Yield a database session, ensuring it is closed after use."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
