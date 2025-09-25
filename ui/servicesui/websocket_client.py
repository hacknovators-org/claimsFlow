import asyncio
import sys
import os

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pipeline_controller import ClaimsProcessingPipeline

class WebSocketClient:
    def __init__(self):
        self.pipeline = ClaimsProcessingPipeline()
    
    async def start_processing_sync(self, sender_email: str = "wamitinewton@gmail.com"):
        try:
            result = await self.pipeline.start_processing(sender_email)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def start_processing(self, sender_email: str = "wamitinewton@gmail.com"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.start_processing_sync(sender_email))
        finally:
            loop.close()