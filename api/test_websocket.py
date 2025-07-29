#!/usr/bin/env python3
"""
Test script to verify WebSocket functionality for Voice Live integration
"""

import asyncio
import websockets
import json
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test the WebSocket connection to the audio stream endpoint"""
    try:
        # Connect to the WebSocket endpoint
        uri = "ws://localhost:8000/ws/audio-stream"
        logger.info(f"🔌 Connecting to WebSocket: {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket connected successfully")
            
            # Send a test audio message
            test_audio_data = b"test_audio_data_12345"  # Dummy audio data
            audio_base64 = base64.b64encode(test_audio_data).decode('utf-8')
            
            test_message = {
                "kind": "audioData",
                "audioData": {
                    "data": audio_base64,
                    "timestamp": "2025-07-29T04:17:00.000Z",
                    "participantRawID": "test-participant",
                    "silent": False
                }
            }
            
            logger.info("📤 Sending test audio message...")
            await websocket.send(json.dumps(test_message))
            logger.info("✅ Test message sent successfully")
            
            # Wait a moment for any response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"📥 Received response: {response}")
            except asyncio.TimeoutError:
                logger.info("⏰ No response received (expected for test)")
            
            logger.info("✅ WebSocket test completed successfully")
            
    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")
        return False
    
    return True

async def test_binary_websocket():
    """Test binary WebSocket communication"""
    try:
        uri = "ws://localhost:8000/ws/audio-stream"
        logger.info(f"🔌 Testing binary WebSocket: {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Binary WebSocket connected")
            
            # Send binary audio data
            test_audio_binary = b"binary_audio_test_data_67890"
            logger.info("📤 Sending binary audio data...")
            await websocket.send(test_audio_binary)
            logger.info("✅ Binary data sent successfully")
            
            logger.info("✅ Binary WebSocket test completed")
            
    except Exception as e:
        logger.error(f"❌ Binary WebSocket test failed: {e}")
        return False
    
    return True

async def main():
    """Run all WebSocket tests"""
    logger.info("🧪 Starting WebSocket tests...")
    
    # Test JSON WebSocket communication
    json_test_result = await test_websocket_connection()
    
    # Test binary WebSocket communication
    binary_test_result = await test_binary_websocket()
    
    if json_test_result and binary_test_result:
        logger.info("🎉 All WebSocket tests passed!")
        return True
    else:
        logger.error("❌ Some WebSocket tests failed")
        return False

if __name__ == "__main__":
    asyncio.run(main())
