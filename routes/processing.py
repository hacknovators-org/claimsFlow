import asyncio
import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from pipeline_singleton import pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/processing", tags=["processing"])

DEFAULT_SENDER_EMAIL = os.getenv("CLAIMS_SENDER_EMAIL", "Maundu@kenyare.co.ke")


@router.post("/start")
async def start_processing(sender_email: str = DEFAULT_SENDER_EMAIL):
    """Fire-and-forget trigger: starts the pipeline in the background and
    returns immediately. Progress is observed over the /ws broadcast channel,
    not this response."""
    if pipeline.get_active_agents():
        return {"started": False, "reason": "A processing run is already active"}

    asyncio.create_task(pipeline.start_processing(sender_email))
    return {"started": True, "sender_email": sender_email}


@router.get("/status")
async def get_status():
    return pipeline.get_pipeline_stats()


@router.get("/history")
async def get_history(limit: int = 50):
    return {"history": pipeline.get_processing_history(limit)}


@router.get("/result/{agent_id}")
async def get_result(agent_id: str):
    result = pipeline.get_result(agent_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No result for this agent_id yet")
    return result


@router.post("/stop/{agent_id}")
async def stop_agent(agent_id: str):
    stopped = await pipeline.stop_agent(agent_id)
    return {"stopped": stopped}


@router.get("/result/{agent_id}/report.pdf")
async def get_report_pdf(agent_id: str):
    result = pipeline.get_result(agent_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No result for this agent_id yet")
    pdf_path = result.get("report_generated", {}).get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="No PDF report generated for this run")
    return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
