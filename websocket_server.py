import asyncio
import json
import logging
from typing import Dict, Any
import websockets
from websockets.server import WebSocketServerProtocol
from websocket_manager import websocket_manager
from pipeline_controller import ClaimsProcessingPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pipeline = ClaimsProcessingPipeline(websocket_manager)

async def handle_client_message(websocket: WebSocketServerProtocol, message: Dict[str, Any]):
    try:
        message_type = message.get("type")
        
        if message_type == "start_processing":
            sender_email = message.get("sender_email", "wamitinewton@gmail.com")
            
            await websocket_manager.send_to_client(websocket, {
                "type": "processing_started",
                "message": f"Starting claims processing for {sender_email}",
                "timestamp": asyncio.get_event_loop().time()
            })
            
            result = await pipeline.start_processing(sender_email)
            
            await websocket_manager.send_to_client(websocket, {
                "type": "processing_completed" if result["success"] else "processing_failed",
                "result": result,
                "timestamp": asyncio.get_event_loop().time()
            })
            
        elif message_type == "get_agent_status":
            agent_id = message.get("agent_id")
            if agent_id:
                status = await pipeline.get_agent_status(agent_id)
                await websocket_manager.send_to_client(websocket, {
                    "type": "agent_status",
                    "agent_id": agent_id,
                    "status": status,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
        elif message_type == "stop_agent":
            agent_id = message.get("agent_id")
            if agent_id:
                stopped = await pipeline.stop_agent(agent_id)
                await websocket_manager.send_to_client(websocket, {
                    "type": "agent_stopped",
                    "agent_id": agent_id,
                    "success": stopped,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
        elif message_type == "get_active_agents":
            active_agents = pipeline.get_active_agents()
            await websocket_manager.send_to_client(websocket, {
                "type": "active_agents",
                "agents": active_agents,
                "timestamp": asyncio.get_event_loop().time()
            })
            
        elif message_type == "get_pipeline_stats":
            stats = pipeline.get_pipeline_stats()
            await websocket_manager.send_to_client(websocket, {
                "type": "pipeline_stats",
                "stats": stats,
                "timestamp": asyncio.get_event_loop().time()
            })
            
        elif message_type == "get_processing_history":
            limit = message.get("limit", 50)
            history = pipeline.get_processing_history(limit)
            await websocket_manager.send_to_client(websocket, {
                "type": "processing_history",
                "history": history,
                "timestamp": asyncio.get_event_loop().time()
            })
            
        elif message_type == "ping":
            await websocket_manager.send_to_client(websocket, {
                "type": "pong",
                "timestamp": asyncio.get_event_loop().time()
            })
            
        else:
            await websocket_manager.send_to_client(websocket, {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": asyncio.get_event_loop().time()
            })
            
    except Exception as e:
        logger.error(f"Error handling client message: {e}")
        await websocket_manager.send_to_client(websocket, {
            "type": "error",
            "message": f"Error processing request: {str(e)}",
            "timestamp": asyncio.get_event_loop().time()
        })

async def websocket_handler(websocket: WebSocketServerProtocol, path: str):
    session_id = await websocket_manager.register(websocket)
    
    try:
        await websocket_manager.send_to_client(websocket, {
            "type": "welcome",
            "session_id": session_id,
            "message": "Connected to Claims Processing Pipeline",
            "available_commands": [
                "start_processing",
                "get_agent_status", 
                "stop_agent",
                "get_active_agents",
                "get_pipeline_stats",
                "get_processing_history",
                "ping"
            ],
            "timestamp": asyncio.get_event_loop().time()
        })
        
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_client_message(websocket, data)
            except json.JSONDecodeError:
                await websocket_manager.send_to_client(websocket, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": asyncio.get_event_loop().time()
                })
            except Exception as e:
                logger.error(f"Error in websocket handler: {e}")
                await websocket_manager.send_to_client(websocket, {
                    "type": "error",
                    "message": f"Server error: {str(e)}",
                    "timestamp": asyncio.get_event_loop().time()
                })
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {session_id} disconnected")
    except Exception as e:
        logger.error(f"Websocket handler error: {e}")
    finally:
        await websocket_manager.unregister(websocket)

async def start_websocket_server(host: str = "localhost", port: int = 8765):
    logger.info(f"Starting Enhanced WebSocket server on {host}:{port}")
    
    server = await websockets.serve(
        websocket_handler, 
        host, 
        port,
        ping_interval=20,
        ping_timeout=10
    )
    
    logger.info(f"Enhanced WebSocket server started successfully")
    logger.info(f"Real-time updates enabled for claims processing")
    
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        logger.info("Shutting down WebSocket server")
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_websocket_server())