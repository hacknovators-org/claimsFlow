"""
Test script to verify WebSocket connection
Run this before starting the Streamlit app to ensure server is accessible
"""
import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test WebSocket connection"""
    uri = "ws://localhost:8785"
    
    try:
        logger.info(f"Testing connection to {uri}...")
        
        async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as websocket:
            logger.info("✅ Successfully connected to WebSocket server!")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            logger.info(f"Received welcome: {welcome_data.get('message')}")
            logger.info(f"Available commands: {welcome_data.get('available_commands')}")
            
            # Test ping
            logger.info("\nTesting ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            pong = await websocket.recv()
            pong_data = json.loads(pong)
            logger.info(f"✅ Received pong: {pong_data.get('type')}")
            
            # Test get_active_agents
            logger.info("\nTesting get_active_agents...")
            await websocket.send(json.dumps({"type": "get_active_agents"}))
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"✅ Received: {response_data.get('type')}")
            
            logger.info("\n✅ All tests passed! WebSocket server is working correctly.")
            return True
            
    except ConnectionRefusedError:
        logger.error("❌ Connection refused. Is the WebSocket server running?")
        logger.error("   Start the server with: python websocket_server.py")
        return False
        
    except asyncio.TimeoutError:
        logger.error("❌ Connection timeout. Server is not responding.")
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Connection Test")
    print("=" * 60)
    
    success = asyncio.run(test_connection())
    
    print("=" * 60)
    if success:
        print("✅ Test completed successfully!")
        print("You can now start the Streamlit app.")
    else:
        print("❌ Test failed!")
        print("Please ensure the WebSocket server is running on port 8785.")
    print("=" * 60)