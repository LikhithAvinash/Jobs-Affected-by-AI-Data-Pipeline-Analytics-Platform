"""
Seed the occupations table with known AI automation risk percentages.

Data based on Frey & Osborne (2017) "The Future of Employment" study
and World Economic Forum reports on automation susceptibility.

automation_score: 0.0 (no risk) to 1.0 (fully automatable)
"""

import logging
from src.models.database import SessionLocal
from src.models.schemas import Occupation

logger = logging.getLogger(__name__)

# ── Known occupation automation risk data ──
# Format: (onet_code, occupation_name, automation_score)
OCCUPATION_DATA = [
    # HIGH RISK (>70%) — Routine, repetitive tasks
    ("43-3011", "Bill and Account Collectors", 0.93),
    ("43-9021", "Data Entry Keyers", 0.99),
    ("43-3021", "Billing and Posting Clerks", 0.94),
    ("43-4051", "Customer Service Representatives", 0.55),
    ("43-6014", "Secretaries and Administrative Assistants", 0.96),
    ("43-9061", "Office Clerks, General", 0.96),
    ("41-2011", "Cashiers", 0.97),
    ("41-2031", "Retail Salespersons", 0.92),
    ("43-4171", "Receptionists and Information Clerks", 0.96),
    ("43-5071", "Shipping and Receiving Clerks", 0.95),
    ("51-2092", "Team Assemblers", 0.97),
    ("53-3032", "Heavy and Tractor-Trailer Truck Drivers", 0.79),
    ("43-3031", "Bookkeeping, Accounting, and Auditing Clerks", 0.98),
    ("27-2022", "Coaches and Scouts", 0.15),
    ("13-2011", "Accountants and Auditors", 0.94),
    ("43-4111", "Interviewers", 0.94),
    ("51-4011", "CNC Machine Tool Operators", 0.86),
    ("51-9198", "Helpers—Production Workers", 0.93),
    ("43-5052", "Postal Service Mail Carriers", 0.68),
    ("35-3023", "Fast Food and Counter Workers", 0.92),

    # MEDIUM RISK (30-70%) — Mix of routine and cognitive
    ("15-1252", "Software Developers", 0.42),
    ("15-1211", "Computer Systems Analysts", 0.61),
    ("15-1244", "Network and Computer Systems Administrators", 0.65),
    ("15-2051", "Data Scientists", 0.31),
    ("13-1161", "Market Research Analysts", 0.61),
    ("15-1256", "Software Quality Assurance Analysts", 0.54),
    ("13-2051", "Financial Analysts", 0.46),
    ("27-3031", "Public Relations Specialists", 0.46),
    ("15-1231", "Computer Network Support Specialists", 0.65),
    ("25-1011", "Business Teachers, Postsecondary", 0.41),
    ("17-2061", "Computer Hardware Engineers", 0.52),
    ("17-2071", "Electrical Engineers", 0.51),
    ("13-1111", "Management Analysts", 0.49),
    ("15-1232", "Computer User Support Specialists", 0.65),
    ("11-3021", "Computer and Information Systems Managers", 0.35),
    ("13-2061", "Financial Examiners", 0.67),
    ("15-1241", "Computer Network Architects", 0.53),
    ("29-2034", "Radiologic Technologists", 0.63),
    ("15-1243", "Database Administrators", 0.64),
    ("15-1242", "Database Architects", 0.49),

    # LOW RISK (<30%) — Creative, strategic, human-centric
    ("15-2031", "Operations Research Analysts", 0.28),
    ("15-1221", "Computer and Information Research Scientists", 0.15),
    ("15-1299", "AI/Machine Learning Engineers", 0.08),
    ("15-1253", "Software Quality Assurance Engineers", 0.33),
    ("21-1014", "Mental Health Counselors", 0.04),
    ("29-1141", "Registered Nurses", 0.09),
    ("11-1021", "General and Operations Managers", 0.16),
    ("11-2021", "Marketing Managers", 0.14),
    ("27-1024", "Graphic Designers", 0.43),
    ("15-1254", "Web Developers", 0.40),
    ("11-9111", "Medical and Health Services Managers", 0.11),
    ("25-1021", "Computer Science Teachers, Postsecondary", 0.31),
    ("19-1042", "Medical Scientists", 0.09),
    ("15-1255", "Web and Digital Interface Designers", 0.26),
    ("29-1228", "Physicians (All Other)", 0.07),
    ("11-1011", "Chief Executives", 0.15),
    ("11-3031", "Financial Managers", 0.23),
    ("29-1171", "Nurse Practitioners", 0.06),
    ("11-2022", "Sales Managers", 0.25),
    ("19-3022", "Survey Researchers", 0.23),

    # Data Engineering & MLOps specific
    ("15-1245", "Data Engineers", 0.35),
    ("15-1246", "MLOps Engineers", 0.22),
    ("15-1247", "DevOps Engineers", 0.38),
    ("15-1248", "Cloud Architects", 0.28),
    ("15-1249", "Full Stack Developers", 0.40),
    ("15-1250", "Frontend Developers", 0.45),
    ("15-1251", "Backend Developers", 0.38),
    ("15-1257", "Cybersecurity Analysts", 0.21),
    ("15-1258", "Blockchain Developers", 0.30),
    ("15-1259", "Mobile App Developers", 0.42),
]


def seed_occupations():
    """Insert occupation automation risk data into the database."""
    session = SessionLocal()
    created = 0
    updated = 0

    try:
        for onet_code, name, score in OCCUPATION_DATA:
            existing = session.query(Occupation).filter_by(onet_code=onet_code).first()
            if existing:
                existing.automation_score = score
                existing.occupation_name = name
                updated += 1
            else:
                occ = Occupation(
                    onet_code=onet_code,
                    occupation_name=name,
                    automation_score=score,
                )
                session.add(occ)
                created += 1

        session.commit()
        logger.info("Seeded occupations: %d created, %d updated", created, updated)
        print(f"✅ Seeded occupations: {created} created, {updated} updated")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return created + updated


if __name__ == "__main__":
    seed_occupations()
