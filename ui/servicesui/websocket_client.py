import asyncio
import json
import sys
import os
import websockets
from typing import Dict, Any, Callable, Optional
import streamlit as st

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pipeline_controller import ClaimsProcessingPipeline

class WebSocketClient:
    def __init__(self, websocket_url: str = "ws://localhost:8765"):
        self.websocket_url = websocket_url
        self.pipeline = ClaimsProcessingPipeline()
        self.websocket = None
        self.is_connected = False
        self.message_handlers: Dict[str, Callable] = {
            'agent_progress': self._handle_agent_progress,
            'tool_execution': self._handle_tool_execution,
            'stage_completion': self._handle_stage_completion,
            'analysis_result': self._handle_analysis_result,
            'processing_completed': self._handle_processing_completed,
            'processing_failed': self._handle_processing_failed
        }
    
    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.is_connected = True
            return True
        except Exception as e:
            self.is_connected = False
            return False
    
    async def disconnect(self):
        if self.websocket and self.is_connected:
            await self.websocket.close()
            self.is_connected = False
    
    async def send_message(self, message: Dict[str, Any]):
        if self.websocket and self.is_connected:
            await self.websocket.send(json.dumps(message))
    
    async def listen_for_messages(self):
        if not self.websocket or not self.is_connected:
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                message_type = data.get('type')
                
                if message_type in self.message_handlers:
                    await self.message_handlers[message_type](data)
        except websockets.exceptions.ConnectionClosed:
            self.is_connected = False
        except Exception as e:
            st.error(f"WebSocket error: {str(e)}")
    
    async def _handle_agent_progress(self, data: Dict[str, Any]):
        stage = data.get('stage', '')
        message = data.get('message', '')
        progress = data.get('progress', 0.0)
        
        if 'progress' not in st.session_state:
            st.session_state.progress = 0.0
        if 'current_stage' not in st.session_state:
            st.session_state.current_stage = ''
        if 'stage_message' not in st.session_state:
            st.session_state.stage_message = ''
        if 'progress_data' not in st.session_state:
            st.session_state.progress_data = []
        
        st.session_state.progress = progress
        st.session_state.current_stage = stage
        st.session_state.stage_message = message
        
        st.session_state.progress_data.append({
            'timestamp': data.get('timestamp'),
            'stage': stage,
            'message': message,
            'progress': progress
        })
    
    async def _handle_tool_execution(self, data: Dict[str, Any]):
        tool_name = data.get('tool_name', '')
        tool_description = data.get('tool_description', '')
        status = data.get('status', 'executing')
        
        if 'current_tool' not in st.session_state:
            st.session_state.current_tool = ''
        if 'tool_status' not in st.session_state:
            st.session_state.tool_status = ''
        if 'tool_description' not in st.session_state:
            st.session_state.tool_description = ''
        if 'tool_history' not in st.session_state:
            st.session_state.tool_history = []
        
        st.session_state.current_tool = tool_name
        st.session_state.tool_status = status
        st.session_state.tool_description = tool_description
        
        st.session_state.tool_history.append({
            'timestamp': data.get('timestamp'),
            'tool_name': tool_name,
            'description': tool_description,
            'status': status
        })
    
    async def _handle_stage_completion(self, data: Dict[str, Any]):
        stage = data.get('stage', '')
        duration = data.get('duration', 0.0)
        success = data.get('success', True)
        
        if 'completed_stages' not in st.session_state:
            st.session_state.completed_stages = []
        
        st.session_state.completed_stages.append({
            'stage': stage,
            'duration': duration,
            'success': success,
            'timestamp': data.get('timestamp')
        })
    
    async def _handle_analysis_result(self, data: Dict[str, Any]):
        analysis_type = data.get('analysis_type', '')
        result = data.get('result', '')
        risk_level = data.get('risk_level', 'LOW')
        
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = []
        
        st.session_state.analysis_results.append({
            'type': analysis_type,
            'result': result,
            'risk_level': risk_level,
            'timestamp': data.get('timestamp')
        })
    
    async def _handle_processing_completed(self, data: Dict[str, Any]):
        result = data.get('result', {})
        
        st.session_state.processing = False
        st.session_state.completed = True
        st.session_state.report_data = result.get('results', {})
        st.session_state.processing_result = result
        st.session_state.progress = 100.0
        st.session_state.current_stage = "Completed"
        st.session_state.stage_message = "Claims processing completed successfully"
    
    async def _handle_processing_failed(self, data: Dict[str, Any]):
        result = data.get('result', {})
        error = result.get('error', 'Unknown error')
        
        st.session_state.processing = False
        st.session_state.completed = False
        st.session_state.current_stage = "Failed"
        st.session_state.stage_message = f"Processing failed: {error}"
    
    async def start_processing_with_websocket(self, sender_email: str = "wamitinewton@gmail.com"):
        connected = await self.connect()
        
        if not connected:
            return await self.start_processing_sync(sender_email)
        
        try:
            await self.send_message({
                "type": "start_processing",
                "sender_email": sender_email
            })
            
            await self.listen_for_messages()
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await self.disconnect()
        
        return st.session_state.get('processing_result', {"success": True})
    
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