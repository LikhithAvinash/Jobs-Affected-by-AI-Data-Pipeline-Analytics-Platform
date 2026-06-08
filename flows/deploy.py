"""
Prefect Deployment Configuration.

Registers all flows with their schedules.
Run:  python flows/deploy.py
"""

from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

from flow_daily_jobs import daily_job_extraction
from flow_weekly_skills import weekly_skill_extraction
from flow_monthly_trends import monthly_trend_extraction
from flow_nightly_refresh import nightly_dashboard_refresh


def deploy_all():
    """Register all flow deployments with Prefect."""

    # Flow 1: Daily at 6 AM UTC
    Deployment.build_from_flow(
        flow=daily_job_extraction,
        name="daily-job-extraction",
        schedule=CronSchedule(cron="0 6 * * *", timezone="UTC"),
        work_queue_name="default",
    ).apply()
    print("✅ Deployed: daily-job-extraction (6 AM daily)")

    # Flow 2: Weekly on Sundays at 3 AM UTC
    Deployment.build_from_flow(
        flow=weekly_skill_extraction,
        name="weekly-skill-extraction",
        schedule=CronSchedule(cron="0 3 * * 0", timezone="UTC"),
        work_queue_name="default",
    ).apply()
    print("✅ Deployed: weekly-skill-extraction (3 AM Sundays)")

    # Flow 3: Monthly on the 1st at 2 AM UTC
    Deployment.build_from_flow(
        flow=monthly_trend_extraction,
        name="monthly-trend-extraction",
        schedule=CronSchedule(cron="0 2 1 * *", timezone="UTC"),
        work_queue_name="default",
    ).apply()
    print("✅ Deployed: monthly-trend-extraction (2 AM, 1st of month)")

    # Flow 4: Nightly at 1 AM UTC
    Deployment.build_from_flow(
        flow=nightly_dashboard_refresh,
        name="nightly-dashboard-refresh",
        schedule=CronSchedule(cron="0 1 * * *", timezone="UTC"),
        work_queue_name="default",
    ).apply()
    print("✅ Deployed: nightly-dashboard-refresh (1 AM daily)")


if __name__ == "__main__":
    deploy_all()
