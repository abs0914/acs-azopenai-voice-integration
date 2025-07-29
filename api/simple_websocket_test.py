#!/usr/bin/env python3
"""
Simple WebSocket test using websockets library directly
"""

import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_websocket():
    """Test WebSocket connection with minimal setup"""
    try:
        uri = "ws://localhost:8000/ws/audio-stream"
        logger.info(f"🔌 Attempting to connect to: {uri}")
        
        # Try to connect with more detailed error handling
        try:
            websocket = await websockets.connect(uri)
            logger.info("✅ WebSocket connected successfully!")
            
            # Send a simple message
            test_message = {"test": "hello"}
            await websocket.send(json.dumps(test_message))
            logger.info("📤 Test message sent")
            
            # Close the connection
            await websocket.close()
            logger.info("🔌 WebSocket closed")
            
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"❌ Invalid status code: {e.status_code}")
            logger.error(f"❌ Response headers: {e.response_headers}")
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"❌ WebSocket exception: {e}")
        except Exception as e:
            logger.error(f"❌ General exception: {e}")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_websocket())
