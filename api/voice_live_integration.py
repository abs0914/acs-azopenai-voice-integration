#!/usr/bin/env python3
"""
Azure AI Voice Live integration for ACS Call Automation
"""
import os
import json
import asyncio
import base64
import logging
import uuid
from typing import Optional

# Voice Live imports - compatible with websockets 12.0
import websockets
from websockets.exceptions import WebSocketException

logger = logging.getLogger(__name__)

# Global logging function for debugging
def log_message(message):
    """Log message to both console and global logs"""
    print(message)
    try:
        # Try to access global logs from main app
        import sys
        if hasattr(sys.modules.get('__main__'), 'voice_live_logs'):
            sys.modules['__main__'].voice_live_logs.append(message)
    except:
        pass  # Ignore if global logs not available

class VoiceLiveCallHandler:
    """Handles Voice Live integration for ACS calls"""
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_VOICE_LIVE_ENDPOINT", "https://vida-voice-live.cognitiveservices.azure.com/")
        self.deployment = os.getenv("AZURE_VOICE_LIVE_DEPLOYMENT", "vida-voice-bot")
        self.api_key = os.getenv("AZURE_VOICE_LIVE_API_KEY", "D0ccvKqf20m8g8wXHnqyF7BFypUJygfQXrjIOm2kMfJASaNvXKu0JQQJ99BGACHYHv6XJ3w3AAAAACOGv7Z2")
        self.agent_id = "asst_dEODj1Hu6Z68Ebggl13DAHPv"  # vida-voice-bot agent ID
        self.connection = None
        self.call_connection_id = None
        
    async def start_voice_conversation(self, call_connection_id: str):
        """Start a Voice Live conversation for an ACS call"""
        try:
            log_message(f"🎤 Starting Voice Live conversation for call: {call_connection_id}")
            log_message(f"🔗 Endpoint: {self.endpoint}")
            log_message(f"🤖 Agent ID: {self.agent_id}")
            log_message(f"📦 Deployment: {self.deployment}")

            self.call_connection_id = call_connection_id

            # Create WebSocket connection to Voice Live - try different URL format
            # Option 1: With agent_id parameter
            url = f"{self.endpoint.rstrip('/')}/voice-agent/realtime?api-version=2025-05-01-preview&model={self.agent_id}"
            url = url.replace("https://", "wss://")

            log_message(f"🌐 WebSocket URL: {url}")

            headers = {
                "api-key": self.api_key,
                "x-ms-client-request-id": str(uuid.uuid4())
            }

            log_message(f"📋 Headers: {list(headers.keys())}")
            log_message("🔌 Attempting WebSocket connection...")

            try:
                self.connection = await websockets.connect(url, extra_headers=headers)
                log_message("✅ WebSocket connection established")
            except Exception as ws_error:
                log_message(f"❌ First connection attempt failed: {ws_error}")

                # Try alternative URL format without agent_id
                alt_url = f"{self.endpoint.rstrip('/')}/voice-agent/realtime?api-version=2025-05-01-preview&model={self.deployment}"
                alt_url = alt_url.replace("https://", "wss://")
                log_message(f"🔄 Trying alternative URL: {alt_url}")

                self.connection = await websockets.connect(alt_url, extra_headers=headers)
                log_message("✅ WebSocket connection established (alternative URL)")

            # Configure the Voice Live session
            log_message("⚙️ Configuring Voice Live session...")
            await self.configure_session()

            # Send initial greeting
            log_message("🎵 Sending initial greeting...")
            await self.send_initial_greeting()

            log_message("✅ Voice Live conversation started successfully")
            return True

        except Exception as e:
            log_message(f"❌ Failed to start Voice Live conversation: {e}")
            log_message(f"📋 Error details: {type(e).__name__}: {str(e)}")
            import traceback
            log_message(f"📋 Traceback: {traceback.format_exc()}")
            return False
    
    async def configure_session(self):
        """Configure the Voice Live session for vida-voice-bot agent"""
        session_config = {
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "azure_semantic_vad",
                    "threshold": 0.3,
                    "prefix_padding_ms": 200,
                    "silence_duration_ms": 200,
                    "remove_filler_words": False,
                    "end_of_utterance_detection": {
                        "model": "semantic_detection_v1",
                        "threshold": 0.1,
                        "timeout": 4,
                    },
                },
                "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
                "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
                "voice": {
                    "name": "en-US-Emma2:DragonHDLatestNeural",  # Emma2 Dragon HD Latest voice
                    "type": "azure-standard",
                    "temperature": 0.8,
                },
                # Agent ID is specified in the WebSocket URL
            },
            "event_id": str(uuid.uuid4())
        }
        
        print(f"📤 Sending session config: {json.dumps(session_config, indent=2)}")
        await self.connection.send(json.dumps(session_config))
        print("✅ Voice Live session configured")
    
    async def send_initial_greeting(self):
        """Send initial greeting message from vida-voice-bot"""
        greeting = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello! My Name is Emma your Vida Voice Bot. I'm your intelligent voice assistant. How can I help you today?"
                    }
                ]
            },
            "event_id": str(uuid.uuid4())
        }
        
        print(f"📤 Sending greeting: {json.dumps(greeting, indent=2)}")
        await self.connection.send(json.dumps(greeting))

        # Trigger response generation
        response_create = {
            "type": "response.create",
            "event_id": str(uuid.uuid4())
        }

        print(f"📤 Triggering response: {json.dumps(response_create, indent=2)}")
        await self.connection.send(json.dumps(response_create))
        print("✅ Initial greeting sent and response triggered")
    
    async def handle_audio_from_call(self, audio_data: bytes):
        """Handle audio data from ACS call and send to Voice Live"""
        try:
            # Convert audio to base64 and send to Voice Live
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")
            
            audio_append = {
                "type": "input_audio_buffer.append",
                "audio": audio_b64,
                "event_id": str(uuid.uuid4())
            }
            
            await self.connection.send(json.dumps(audio_append))
            
        except Exception as e:
            print(f"❌ Error handling audio from call: {e}")
    
    async def process_voice_live_responses(self, acs_call_connection):
        """Process responses from Voice Live and send to ACS call"""
        try:
            async for message in self.connection:
                event = json.loads(message)
                event_type = event.get("type")
                
                if event_type == "response.audio.delta":
                    # Get audio data from Voice Live
                    audio_delta = event.get("delta", "")
                    if audio_delta:
                        audio_bytes = base64.b64decode(audio_delta)
                        # Send audio to ACS call (you'll need to implement this)
                        await self.send_audio_to_call(acs_call_connection, audio_bytes)
                
                elif event_type == "response.done":
                    print("🎤 Voice Live response completed")
                
                elif event_type == "error":
                    print(f"❌ Voice Live error: {event}")
                
                else:
                    print(f"📝 Voice Live event: {event_type}")
                    
        except Exception as e:
            print(f"❌ Error processing Voice Live responses: {e}")
    
    async def send_audio_to_call(self, acs_call_connection, audio_bytes: bytes):
        """Send audio from Voice Live back to the ACS call"""
        try:
            # This is where you'd integrate with ACS Call Automation
            # to stream audio back to the caller
            print(f"🔊 Sending {len(audio_bytes)} bytes of audio to call")
            
            # For now, just log that we received audio
            # In a full implementation, you'd use ACS streaming APIs
            
        except Exception as e:
            print(f"❌ Error sending audio to call: {e}")
    
    async def end_conversation(self):
        """End the Voice Live conversation"""
        try:
            if self.connection:
                await self.connection.close()
                self.connection = None
                print("✅ Voice Live conversation ended")
        except Exception as e:
            print(f"❌ Error ending conversation: {e}")

# Global instance for call handling
voice_live_handler = VoiceLiveCallHandler()

async def start_voice_live_for_call(call_connection_id: str):
    """Start Voice Live conversation for a specific call"""
    return await voice_live_handler.start_voice_conversation(call_connection_id)

async def end_voice_live_for_call():
    """End Voice Live conversation"""
    await voice_live_handler.end_conversation()
