#!/usr/bin/env python3
"""
Test the WebSocket endpoint directly to see if it's reachable
"""

import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_endpoint():
    """Test if our WebSocket endpoint is reachable from outside"""
    try:
        # Test the exact WebSocket URL that ACS would use
        websocket_url = "wss://v2vhskmw-8000.asse.devtunnels.ms/ws/audio-stream"
        
        logger.info(f"🔌 Testing WebSocket URL: {websocket_url}")
        
        # Try to connect
        async with websockets.connect(websocket_url) as websocket:
            logger.info("✅ WebSocket connection successful!")
            
            # Send a test message
            test_message = {
                "kind": "audioData",
                "audioData": {
                    "data": "dGVzdCBhdWRpbyBkYXRh",  # base64 "test audio data"
                    "timestamp": "2025-07-29T06:30:00.000Z",
                    "participantRawID": "test-caller",
                    "silent": False
                }
            }
            
            logger.info("📤 Sending test audio message...")
            await websocket.send(json.dumps(test_message))
            logger.info("✅ Test message sent successfully!")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            logger.info("🎉 WebSocket endpoint is working correctly!")
            return True
            
    except websockets.exceptions.InvalidURI as e:
        logger.error(f"❌ Invalid WebSocket URI: {e}")
        return False
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"❌ WebSocket connection closed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        return False

async def main():
    """Run WebSocket test"""
    logger.info("🧪 Testing WebSocket endpoint accessibility...")
    
    success = await test_websocket_endpoint()
    
    if success:
        logger.info("✅ WebSocket endpoint is accessible - media streaming should work")
    else:
        logger.error("❌ WebSocket endpoint is not accessible - this is why media streaming fails")
        logger.error("🔧 Check dev tunnel configuration and firewall settings")

if __name__ == "__main__":
    asyncio.run(main())
