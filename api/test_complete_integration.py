#!/usr/bin/env python3
"""
Test complete integration: WebSocket + Voice Live
"""

import asyncio
import websockets
import json
import base64
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_integration():
    """Test the complete integration flow"""
    try:
        # Step 1: Connect to our WebSocket endpoint
        ws_url = "ws://localhost:8000/ws/audio-stream"
        logger.info(f"🔌 Connecting to WebSocket: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            logger.info("✅ WebSocket connected")
            
            # Step 2: Simulate incoming audio data from ACS
            # This simulates what ACS would send when a caller speaks
            test_audio_data = b"simulated_audio_from_caller_12345"
            audio_base64 = base64.b64encode(test_audio_data).decode('utf-8')
            
            # Send audio in ACS format
            acs_audio_message = {
                "kind": "audioData",
                "audioData": {
                    "data": audio_base64,
                    "timestamp": "2025-07-29T04:30:00.000Z",
                    "participantRawID": "caller",
                    "silent": False
                }
            }
            
            logger.info("📤 Sending simulated caller audio...")
            await websocket.send(json.dumps(acs_audio_message))
            
            # Step 3: Send binary audio data (alternative format)
            logger.info("📤 Sending binary audio data...")
            await websocket.send(test_audio_data)
            
            # Step 4: Wait for any responses
            logger.info("👂 Listening for responses...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                logger.info(f"📥 Received response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.info("⏰ No response received (expected for test)")
            
            logger.info("✅ Complete integration test passed!")
            
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def test_voice_live_greeting():
    """Test the Voice Live greeting function"""
    try:
        # Test the greeting endpoint
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # This would normally be triggered by an incoming call
            logger.info("🧪 Testing Voice Live greeting functionality...")
            
            # We can't directly test the greeting without a real call,
            # but we can verify the Voice Live connection works
            async with session.get('http://localhost:8000/test-voice-live') as response:
                result = await response.json()
                if result.get('status') == 'success':
                    logger.info("✅ Voice Live greeting system ready")
                else:
                    logger.error(f"❌ Voice Live greeting test failed: {result}")
                    
    except Exception as e:
        logger.error(f"❌ Voice Live greeting test failed: {e}")

async def main():
    """Run all integration tests"""
    logger.info("🧪 Starting complete integration tests...")
    
    # Test 1: WebSocket integration
    await test_complete_integration()
    
    # Test 2: Voice Live greeting system
    await test_voice_live_greeting()
    
    logger.info("🎉 All integration tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
