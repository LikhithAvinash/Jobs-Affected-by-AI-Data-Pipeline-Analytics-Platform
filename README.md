# AI Job Market Intelligence Pipeline
<img width="1920" height="1080" alt="Screenshot from 2026-06-08 22-27-05" src="https://github.com/user-attachments/assets/f0e7f516-3807-42e5-8e34-f94269093657" />

An end-to-end data platform that analyzes AI's impact on the job market — tracking jobs growing despite AI, jobs vulnerable to automation, emerging skills, AI hiring trends, and industry-level disruption.

## Architecture

```
                     Prefect (Orchestrator)
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   Jobs APIs           Intelligence        Research
  (Adzuna,              (O*NET,            (arXiv,
  USAJobs,               BLS,            Stack Exchange)
  The Muse)          StackExchange)
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    Data Extraction
                            │
                    Data Cleaning (Pandas)
                            │
                    Data Transformation
                            │
                    PostgreSQL Data Warehouse
                            │
                    Analytics Views (SQL)
                            │
                    Grafana Dashboards
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Orchestration | Prefect 2.x |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Data Processing | Pandas |
| ML | XGBoost / scikit-learn |
| Dashboards | Grafana 11 |
| Containerisation | Docker Compose |
| CI/CD | GitHub Actions |

## Quick Start

### 1. Clone & Setup Environment

```bash
git clone <repo-url>
cd AI_replacing_Jobs
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (Adzuna, USAJobs)
```

### 3. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** on `localhost:5432`
- **Grafana** on `localhost:3000` (admin/admin)

### 4. Create Database Tables

```bash
python -m src.models.create_tables
```

### 5. Run Pipelines

```bash
# Daily job extraction
python flows/flow_daily_jobs.py

# Weekly skill trends
python flows/flow_weekly_skills.py

# Monthly research & employment trends
python flows/flow_monthly_trends.py

# Nightly dashboard view refresh
python flows/flow_nightly_refresh.py
```

### 6. Deploy Scheduled Flows (Optional)

```bash
prefect server start  # Start Prefect UI
python flows/deploy.py  # Register deployments
prefect agent start -q default  # Start worker
```

## Project Structure

```
AI_replacing_Jobs/
├── src/
│   ├── extractors/          # API clients (Adzuna, USAJobs, Muse, arXiv, BLS, StackExchange)
│   ├── transformers/        # Data cleaning & skill extraction
│   ├── loaders/             # Database upsert logic
│   ├── models/              # SQLAlchemy ORM models & DB config
│   ├── ml/                  # Automation risk ML predictor
│   └── utils/               # Shared HTTP client with rate limiting
├── flows/                   # Prefect flow definitions & deployment
├── tests/                   # pytest test suite
├── dashboards/              # Grafana provisioning configs
├── alembic/                 # Database migration scripts
├── docker-compose.yml       # PostgreSQL + Grafana
├── requirements.txt         # Python dependencies
└── .github/workflows/       # CI/CD pipeline
```

## API Keys Required

| API | Key Required | Free Tier |
|-----|-------------|-----------|
| Adzuna | Yes (App ID + Key) | Free registration |
| USAJobs | Yes (API Key + Email) | Free |
| The Muse | No | Public API |
| arXiv | No | Public API |
| BLS | Optional | 25 req/day without key |
| Stack Exchange | No | 300 req/day |

## Grafana Dashboards

The Grafana instance is auto-provisioned with a PostgreSQL datasource and a main dashboard containing:

1. **Top Skills by Job Demand** — Bar chart of most-requested skills
2. **Jobs by Source** — Pie chart breakdown across APIs
3. **Average Salary Range by Source** — Salary comparison
4. **Daily Job Posting Trends** — Time series of posting volume
5. **Top Hiring Companies** — Table of most active employers
6. **AI Research by Category** — arXiv paper distribution
7. **Skill Salary Comparison** — Salary premiums by skill

## ML Component

The optional ML module predicts automation risk for job descriptions:

```python
from src.ml.risk_predictor import predict_risk

score, category = predict_risk("Data entry clerk responsible for manual filing...")
# score: 0.85, category: "High"
```

## Testing

```bash
python -m pytest tests/ -v
```

## License

MIT
