import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pipeline_singleton import pipeline
from services.sms_service import send_sms

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Africa/Nairobi")


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("SMS job scheduler started")


async def _run_scheduled_processing(phone_number: str, sender_email: str):
    logger.info(f"Running scheduled claims processing requested by {phone_number}")
    result = await pipeline.start_processing(sender_email)

    if result["success"]:
        recommendation = result["results"].get("overall_recommendation", "N/A")
        send_sms(phone_number, f"Claims processing complete. Recommendation: {recommendation}")
    else:
        send_sms(phone_number, f"Claims processing failed: {result.get('error', 'unknown error')}")


def schedule_processing(run_at: datetime, phone_number: str, sender_email: str) -> str:
    job = scheduler.add_job(
        _run_scheduled_processing,
        trigger="date",
        run_date=run_at,
        args=[phone_number, sender_email],
        misfire_grace_time=300,
    )
    return job.id
