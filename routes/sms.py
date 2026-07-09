import asyncio
import logging
import os

from fastapi import APIRouter, Form

from pipeline_singleton import pipeline
from services.scheduler_service import schedule_processing
from services.sms_command_parser import HELP_TEXT, parse_command
from services.sms_service import send_sms

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sms", tags=["sms"])

DEFAULT_SENDER_EMAIL = os.getenv("CLAIMS_SENDER_EMAIL", "Maundu@kenyare.co.ke")


@router.post("/incoming")
async def incoming_sms(
    text: str = Form(...),
    from_: str = Form(..., alias="from"),
    to: str = Form(default=""),
    date: str = Form(default=""),
    id: str = Form(default=""),
):
    """Africa's Talking inbound SMS webhook. AT expects a fast 200 response,
    so replies are sent back out-of-band via the SMS API rather than in the
    HTTP response body."""
    logger.info(f"Incoming SMS from {from_}: {text!r}")
    command = parse_command(text)

    if command.action == "process_now":
        send_sms(from_, "Got it - starting claims processing now. You'll get a text when it's done.")
        asyncio.create_task(_process_and_notify(from_))

    elif command.action == "schedule":
        schedule_processing(command.run_at, from_, DEFAULT_SENDER_EMAIL)
        send_sms(from_, f"Scheduled claims processing for {command.run_at.strftime('%Y-%m-%d %H:%M')} EAT.")

    elif command.action == "status":
        stats = pipeline.get_pipeline_stats()
        last = stats.get("last_processing")
        if last:
            message = (
                f"Last run: {last['status']} at {last['end_time']}. "
                f"Recommendation: {last.get('recommendation', 'N/A')}"
            )
        else:
            message = "No processing runs yet."
        send_sms(from_, message)

    else:
        send_sms(from_, HELP_TEXT)

    return {"status": "received"}


async def _process_and_notify(phone_number: str):
    result = await pipeline.start_processing(DEFAULT_SENDER_EMAIL)
    if result["success"]:
        recommendation = result["results"].get("overall_recommendation", "N/A")
        report_path = result.get("processing_record", {}).get("report_path")
        
        # Build the public URL for the report
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        if report_path:
            filename = os.path.basename(report_path)
            report_url = f"{base_url}/reports/{filename}"
            msg = f"Claims processing complete. Recommendation: {recommendation}. Report: {report_url}"
        else:
            msg = f"Claims processing complete. Recommendation: {recommendation}"
            
        send_sms(phone_number, msg)
    else:
        send_sms(phone_number, f"Claims processing failed: {result.get('error', 'unknown error')}")
