import asyncio
import logging
import os
from dotenv import load_dotenv
from websocket_server import start_websocket_server
from pipeline_controller import ClaimsProcessingPipeline
from websocket_manager import websocket_manager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def validate_environment():
    required_vars = [
        "OPENAI_API_KEY",
        "EMAIL_HOST", 
        "EMAIL_APP_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    logger.info("Environment validation successful")

async def run_standalone_processing():
    logger.info("Running standalone claims processing")
    
    pipeline = ClaimsProcessingPipeline()
    
    try:
        result = await pipeline.start_processing()
        
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
            
    except Exception as e:
        logger.error(f"Standalone processing error: {e}")

async def run_websocket_server():
    logger.info("Starting WebSocket server mode")
    await start_websocket_server(
        host=os.getenv("WEBSOCKET_HOST", "localhost"),
        port=int(os.getenv("WEBSOCKET_PORT", 8765))
    )

async def main():
    try:
        validate_environment()
        
        mode = os.getenv("RUN_MODE", "standalone").lower()
        
        if mode == "websocket":
            await run_websocket_server()
        elif mode == "standalone":
            await run_standalone_processing()
        else:
            logger.error(f"Invalid RUN_MODE: {mode}. Use 'standalone' or 'websocket'")
            
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise