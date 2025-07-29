#!/usr/bin/env python3
"""
Test script to simulate Voice Live conversation flow
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

async def test_voice_live_conversation():
    """Test the complete Voice Live conversation flow"""
    try:
        # Connect to Voice Live directly to test conversation
        endpoint = "https://vida-voice-live.cognitiveservices.azure.com/"
        api_key = "D0ccvKqf20m8g8wXHnqyF7BFypUJygfQXrjIOm2kMfJASaNvXKu0JQQJ99BGACHYHv6XJ3w3AAAAACOGv7Z2"
        model = "gpt-4o-realtime-preview"
        
        # Construct WebSocket URL
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
                    "instructions": "You are Emma, a friendly health advisor. Respond briefly and naturally.",
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
            
            # Test conversation starter
            conversation_starter = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Hello, I need to schedule an MRI appointment."
                        }
                    ]
                },
                "event_id": str(uuid.uuid4())
            }
            
            logger.info("📤 Sending conversation starter...")
            await websocket.send(json.dumps(conversation_starter))
            
            # Trigger response
            response_create = {
                "type": "response.create",
                "event_id": str(uuid.uuid4())
            }
            await websocket.send(json.dumps(response_create))
            
            # Listen for responses
            logger.info("👂 Listening for Voice Live responses...")
            response_count = 0
            max_responses = 10
            
            while response_count < max_responses:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    event = json.loads(message)
                    event_type = event.get("type")
                    
                    if event_type == "response.audio.delta":
                        audio_delta = event.get("delta", "")
                        logger.info(f"🔊 Received audio delta: {len(audio_delta)} chars")
                        
                    elif event_type == "response.text.delta":
                        text_delta = event.get("delta", "")
                        logger.info(f"📝 Text delta: '{text_delta}'")
                        
                    elif event_type == "response.text.done":
                        logger.info("✅ Text response completed")
                        
                    elif event_type == "response.done":
                        logger.info("🎤 Voice Live response completed")
                        response_count += 1
                        
                        if response_count < 2:  # Test follow-up
                            logger.info("📤 Sending follow-up message...")
                            followup = {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_text",
                                            "text": "I need it for next week if possible."
                                        }
                                    ]
                                },
                                "event_id": str(uuid.uuid4())
                            }
                            await websocket.send(json.dumps(followup))
                            
                            response_create = {
                                "type": "response.create",
                                "event_id": str(uuid.uuid4())
                            }
                            await websocket.send(json.dumps(response_create))
                        
                    elif event_type == "error":
                        logger.error(f"❌ Voice Live error: {event}")
                        break
                        
                    else:
                        logger.debug(f"📝 Event: {event_type}")
                        
                except asyncio.TimeoutError:
                    logger.info("⏰ No more responses, ending test")
                    break
                except Exception as e:
                    logger.error(f"❌ Error receiving message: {e}")
                    break
            
            logger.info("🎉 Voice Live conversation test completed!")
            
    except Exception as e:
        logger.error(f"❌ Voice Live conversation test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_voice_live_conversation())
