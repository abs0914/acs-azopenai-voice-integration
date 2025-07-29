#!/usr/bin/env python3
"""
Test the Voice Live greeting flow
"""

import asyncio
import websockets
import json
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_voice_live_greeting_direct():
    """Test Voice Live greeting directly"""
    try:
        # Connect to Voice Live directly
        endpoint = "https://vida-voice-live.cognitiveservices.azure.com/"
        api_key = "D0ccvKqf20m8g8wXHnqyF7BFypUJygfQXrjIOm2kMfJASaNvXKu0JQQJ99BGACHYHv6XJ3w3AAAAACOGv7Z2"
        model = "gpt-4o-realtime-preview"
        
        ws_url = f"{endpoint.rstrip('/').replace('https://', 'wss://')}/voice-live/realtime"
        ws_url += f"?api-version=2025-05-01-preview&model={model}"
        
        headers = {
            "api-key": api_key,
            "x-ms-client-request-id": str(uuid.uuid4())
        }
        
        logger.info(f"🌐 Connecting to Voice Live: {ws_url}")
        
        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            logger.info("✅ Connected to Voice Live")
            
            # Configure session
            session_config = {
                "type": "session.update",
                "session": {
                    "instructions": "You are Emma, a friendly health advisor. Always start with a greeting.",
                    "turn_detection": {
                        "type": "azure_semantic_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 700
                    },
                    "voice": {
                        "name": "en-US-Emma2:DragonHDLatestNeural",
                        "type": "azure-standard",
                        "temperature": 0.7
                    }
                },
                "event_id": str(uuid.uuid4())
            }
            
            logger.info("⚙️ Configuring Voice Live session...")
            await websocket.send(json.dumps(session_config))
            
            # Wait for session update
            response = await websocket.recv()
            event = json.loads(response)
            if event.get("type") == "session.updated":
                logger.info("✅ Voice Live session configured")
            
            # Test the greeting approach from our code
            logger.info("📤 Testing assistant greeting message...")
            
            # Create assistant greeting message
            greeting_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "Hi, my name is Emma. I'm your health advisor specializing in laboratory and medical imaging services. How can I help you today?"
                        }
                    ]
                },
                "event_id": str(uuid.uuid4())
            }
            
            await websocket.send(json.dumps(greeting_message))
            logger.info("📤 Sent greeting message")
            
            # Trigger response
            response_create = {
                "type": "response.create",
                "response": {
                    "modalities": ["audio", "text"],
                    "instructions": "Speak the greeting message that was just added to the conversation."
                },
                "event_id": str(uuid.uuid4())
            }
            await websocket.send(json.dumps(response_create))
            logger.info("📤 Triggered response creation")
            
            # Listen for responses
            logger.info("👂 Listening for Voice Live responses...")
            response_count = 0
            max_responses = 20
            
            while response_count < max_responses:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    event = json.loads(message)
                    event_type = event.get("type")
                    
                    logger.info(f"📝 Received event: {event_type}")
                    
                    if event_type == "conversation.item.created":
                        logger.info("✅ Conversation item created")
                        
                    elif event_type == "response.created":
                        logger.info("🤖 Response created - should generate audio")
                        
                    elif event_type == "response.audio.delta":
                        audio_delta = event.get("delta", "")
                        logger.info(f"🔊 Received audio delta: {len(audio_delta)} chars")
                        
                    elif event_type == "response.done":
                        logger.info("✅ Response completed!")
                        response_count += 1
                        break
                        
                    elif event_type == "error":
                        logger.error(f"❌ Voice Live error: {event}")
                        break
                        
                except asyncio.TimeoutError:
                    logger.info("⏰ No more responses")
                    break
                except Exception as e:
                    logger.error(f"❌ Error receiving message: {e}")
                    break
            
            if response_count > 0:
                logger.info("🎉 Voice Live greeting test PASSED!")
            else:
                logger.error("❌ Voice Live greeting test FAILED - no audio generated")
            
    except Exception as e:
        logger.error(f"❌ Voice Live greeting test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_voice_live_greeting_direct())
