
import asyncio
from datetime import datetime, timezone
from typing import Any

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.report_tasks.run_due_reports", bind=True)
def run_due_reports(self) -> dict[str, Any]:
    """Find and run all reports that are due."""
    try:
        result = asyncio.run(_run_due_reports_async())
        return result
    except Exception as exc:
        logger.error("report_run_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(
    name="app.workers.report_tasks.generate_report",
    bind=True,
    max_retries=2,
)
def generate_report(self, report_id: str) -> dict[str, Any]:
    """Generate a single report."""
    try:
        result = asyncio.run(_generate_report_async(report_id))
        return result
    except Exception as exc:
        logger.error("report_generation_failed", report_id=report_id, error=str(exc))
        raise self.retry(exc=exc, countdown=120)


async def _run_due_reports_async() -> dict[str, Any]:
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.api_key import ScheduledReport

    now = datetime.now(timezone.utc)
    dispatched = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledReport).where(
                ScheduledReport.is_active == True,
                ScheduledReport.next_run_at <= now,
            )
        )
        reports = list(result.scalars().all())

        for report in reports:
            generate_report.delay(report_id=str(report.id))
            dispatched += 1

    return {"dispatched": dispatched}


async def _generate_report_async(report_id: str) -> dict[str, Any]:
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.api_key import ScheduledReport, ReportHistory
    from app.services.notification_service import NotificationService
    import uuid

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledReport).where(ScheduledReport.id == uuid.UUID(report_id))
        )
        report = result.scalar_one_or_none()

        if report is None:
            logger.warning("report_not_found", report_id=report_id)
            return {"status": "not_found"}

        try:
            # In production: use headless browser (playwright) to capture dashboard screenshot
            # For now, record a successful run
            history = ReportHistory(
                report_id=report.id,
                status="success",
                recipients_sent=report.recipients,
            )
            db.add(history)

            report.last_run_at = datetime.now(timezone.utc)
            # Update next_run_at based on schedule
            report.next_run_at = _calculate_next_run(report.schedule)

            await db.commit()

            notification_svc = NotificationService()
            for email in report.recipients:
                await notification_svc._send_email(
                    to_email=email,
                    subject=f"[Report] {report.name}",
                    html_body=f"<p>Your scheduled report <b>{report.name}</b> has been generated.</p>",
                )

            logger.info("report_generated", report_id=report_id)
            return {"status": "success", "report_id": report_id}
        except Exception as exc:
            history = ReportHistory(
                report_id=report.id,
                status="failed",
                error_message=str(exc),
                recipients_sent=[],
            )
            db.add(history)
            await db.commit()
            raise


def _calculate_next_run(schedule: str) -> datetime:
    from dateutil.relativedelta import relativedelta

    now = datetime.now(timezone.utc)
    if schedule == "daily":
        return now + relativedelta(days=1)
    elif schedule == "weekly":
        return now + relativedelta(weeks=1)
    elif schedule == "monthly":
        return now + relativedelta(months=1)
    else:
        return now + relativedelta(days=1)
