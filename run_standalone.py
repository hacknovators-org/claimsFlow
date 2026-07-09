"""CLI entrypoint to run a single claims-processing pass without the FastAPI
app, the scheduler, or SMS routes. Uses the same pipeline_singleton as every
other trigger path, so this run shows up in get_processing_history() too."""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from pipeline_singleton import pipeline

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_environment():
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "EMAIL_HOST",
        "EMAIL_APP_PASSWORD"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    logger.info("Environment validation successful")


async def run_standalone_processing(sender_email: str = "Maundu@kenyare.co.ke"):
    logger.info("Running standalone claims processing")

    result = await pipeline.start_processing(sender_email)

    if result["success"]:
        logger.info("Claims processing completed successfully")
        logger.info(f"Recommendation: {result['results']['overall_recommendation']}")
        logger.info(f"Report generated: {result['results']['report_generated']['pdf_path']}")

        if result['results']['critical_issues']:
            logger.warning("Critical issues identified:")
            for issue in result['results']['critical_issues']:
                logger.warning(f"- {issue}")
    else:
        logger.error(f"Claims processing failed: {result['error']}")


if __name__ == "__main__":
    sender = sys.argv[1] if len(sys.argv) > 1 else "Maundu@kenyare.co.ke"
    try:
        validate_environment()
        asyncio.run(run_standalone_processing(sender))
    except KeyboardInterrupt:
        logger.info("Standalone run stopped by user")
