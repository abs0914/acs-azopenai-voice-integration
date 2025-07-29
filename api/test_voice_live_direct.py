#!/usr/bin/env python3
"""
Test Voice Live directly with simulated audio to verify it works
"""

import asyncio
import websockets
import json
import uuid
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_voice_live_with_audio():
    """Test Voice Live with the exact configuration from our code"""
    try:
        # Use the same configuration as our main code
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
            
            # Configure session with EXACT same settings as our code
            session_config = {
                "type": "session.update",
                "session": {
                    "instructions": """You are a voice agent named "Emma," who acts as a friendly and knowledgeable health advisor specializing in laboratory and medical imaging services. Speak naturally and conversationally, keeping answers clear and concise—no more than five spoken sentences.""",
                    "turn_detection": {
                        "type": "azure_semantic_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 700
                    },
                    "input_audio_noise_reduction": {
                        "type": "azure_deep_noise_suppression"
                    },
                    "input_audio_echo_cancellation": {
                        "type": "server_echo_cancellation"
                    },
                    "voice": {
                        "name": "Emma2 Dragon HD Latest",
                        "type": "azure-standard",
                        "temperature": 0.8
                    },
                    "response_temperature": 0.8,
                    "proactive_engagement": True
                },
                "event_id": str(uuid.uuid4())
            }
            
            logger.info("⚙️ Configuring Voice Live session...")
            await websocket.send(json.dumps(session_config))
            
            # Wait for session update
            response = await websocket.recv()
            event = json.loads(response)
            if event.get("type") == "session.updated":
                logger.info("✅ Voice Live session configured with playground settings")
            
            # Test 1: Send greeting message (like our code does)
            logger.info("📤 Testing Voice Live greeting...")
            greeting_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "Hi, my name is Emma. I'm your health advisor. How can I help you today?"
                        }
                    ]
                },
                "event_id": str(uuid.uuid4())
            }
            
            await websocket.send(json.dumps(greeting_message))
            
            # Trigger response
            response_create = {
                "type": "response.create",
                "response": {
                    "modalities": ["audio", "text"]
                },
                "event_id": str(uuid.uuid4())
            }
            await websocket.send(json.dumps(response_create))
            
            # Listen for greeting response
            logger.info("👂 Listening for greeting response...")
            greeting_completed = False
            message_count = 0
            
            while message_count < 50 and not greeting_completed:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    event = json.loads(message)
                    event_type = event.get("type")
                    message_count += 1
                    
                    if event_type == "response.audio.delta":
                        audio_delta = event.get("delta", "")
                        logger.info(f"🔊 Greeting audio: {len(audio_delta)} chars")
                        
                    elif event_type == "response.done":
                        logger.info("✅ Greeting completed!")
                        greeting_completed = True
                        break
                        
                except asyncio.TimeoutError:
                    break
            
            if not greeting_completed:
                logger.error("❌ Greeting failed - Voice Live not working")
                return False
            
            # Test 2: Send user message (simulating "I need to schedule an MRI")
            logger.info("📤 Testing user message: 'I need to schedule an MRI'")
            
            user_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "I need to schedule an MRI appointment"
                        }
                    ]
                },
                "event_id": str(uuid.uuid4())
            }
            
            await websocket.send(json.dumps(user_message))
            
            # Trigger response
            response_create = {
                "type": "response.create",
                "response": {
                    "modalities": ["audio", "text"]
                },
                "event_id": str(uuid.uuid4())
            }
            await websocket.send(json.dumps(response_create))
            
            # Listen for Emma's response
            logger.info("👂 Listening for Emma's response to MRI request...")
            response_completed = False
            message_count = 0
            
            while message_count < 50 and not response_completed:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    event = json.loads(message)
                    event_type = event.get("type")
                    message_count += 1
                    
                    if event_type == "response.audio.delta":
                        audio_delta = event.get("delta", "")
                        logger.info(f"🔊 Response audio: {len(audio_delta)} chars")
                        
                    elif event_type == "response.text.delta":
                        text_delta = event.get("delta", "")
                        logger.info(f"📝 Response text: '{text_delta}'")
                        
                    elif event_type == "response.done":
                        logger.info("✅ Emma responded to MRI request!")
                        response_completed = True
                        break
                        
                except asyncio.TimeoutError:
                    break
            
            if response_completed:
                logger.info("🎉 Voice Live is working correctly!")
                logger.info("🔍 The issue is that caller audio isn't reaching Voice Live")
                return True
            else:
                logger.error("❌ Emma didn't respond to MRI request")
                return False
            
    except Exception as e:
        logger.error(f"❌ Voice Live test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    asyncio.run(test_voice_live_with_audio())
