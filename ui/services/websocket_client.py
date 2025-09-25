import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipeline_controller import ClaimsProcessingPipeline

class WebSocketClient:
    def __init__(self):
        self.pipeline = ClaimsProcessingPipeline()
    
    async def start_processing_sync(self, sender_email: str = "Maundu@kenyare.co.ke"):
        try:
            result = await self.pipeline.start_processing(sender_email)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def start_processing(self, sender_email: str = "Maundu@kenyare.co.ke"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.start_processing_sync(sender_email))
        finally:
            loop.close()