"""
Convenience script to create all tables directly from ORM models.
Usage:  python -m src.models.create_tables

This is useful for quick local setup. For production, use Alembic migrations.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.models.database import engine, Base
import src.models.schemas  # noqa: F401 – registers models with Base


def create_all():
    """Create all tables defined in schemas.py."""
    print(f"Creating tables on: {engine.url}")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully.")
    for table_name in Base.metadata.tables:
        print(f"   • {table_name}")


if __name__ == "__main__":
    create_all()
