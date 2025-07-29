"""
Complete Azure Communication Services Call Automation + Voice Live API Integration
This integrates incoming PSTN calls with Azure AI Voice Live API for natural conversations
"""

import os
import json
import asyncio
import base64
import logging
import uuid
import websockets
from typing import Dict, Optional
from quart import Quart, request, Response, websocket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from azure.communication.callautomation import CallAutomationClient

# Import MediaStreaming classes for preview SDK version (1.4.0b1+)
try:
    from azure.communication.callautomation import (
        MediaStreamingOptions,
        MediaStreamingContentType,
        MediaStreamingAudioChannelType,
        MediaStreamingTransportType
    )
    MEDIA_STREAMING_AVAILABLE = True
    print("✅ MediaStreaming classes imported successfully from preview SDK")
except ImportError as e:
    print(f"⚠️  MediaStreaming classes not available. Error: {e}")
    print("⚠️  Please upgrade to preview SDK: pip install --upgrade azure-communication-callautomation==1.4.0b1")
    MEDIA_STREAMING_AVAILABLE = False
    # Create dummy classes to prevent import errors
    class MediaStreamingOptions:
        def __init__(self, **kwargs):
            pass
    class MediaStreamingContentType:
        AUDIO = "audio"
    class MediaStreamingAudioChannelType:
        MIXED = "mixed"
    class MediaStreamingTransportType:
        WEBSOCKET = "websocket"
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceLiveCallHandler:
    """Enhanced Voice Live handler with proper ACS integration"""
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_VOICE_LIVE_ENDPOINT", "https://vida-voice-live.cognitiveservices.azure.com/")
        self.api_key = os.getenv("AZURE_VOICE_LIVE_API_KEY")
        # Use the correct model from environment or default to realtime preview
        self.model = os.getenv("AZURE_VOICE_LIVE_MODEL", "gpt-4o-realtime-preview")
        if self.model == "gpt-4o":
            self.model = "gpt-4o-realtime-preview"  # Ensure we use the realtime model
        
        # Voice Live WebSocket connection
        self.voice_live_ws = None
        self.call_connection_id = None
        self.is_connected = False
        
    async def connect_to_voice_live(self, call_connection_id: str):
        """Connect to Voice Live API with proper configuration"""
        try:
            self.call_connection_id = call_connection_id
            logger.info(f"🎤 Connecting to Voice Live for call: {call_connection_id}")

            # Validate required configuration
            if not self.api_key:
                raise ValueError("AZURE_VOICE_LIVE_API_KEY is required")
            if not self.endpoint:
                raise ValueError("AZURE_VOICE_LIVE_ENDPOINT is required")

            # Construct WebSocket URL for Voice Live API
            ws_url = f"{self.endpoint.rstrip('/').replace('https://', 'wss://')}/voice-live/realtime"
            ws_url += f"?api-version=2025-05-01-preview&model={self.model}"

            headers = {
                "api-key": self.api_key,
                "x-ms-client-request-id": str(uuid.uuid4())
            }

            logger.info(f"🌐 Connecting to: {ws_url}")
            logger.info(f"🔑 Using model: {self.model}")

            # Connect to Voice Live with timeout
            self.voice_live_ws = await asyncio.wait_for(
                websockets.connect(ws_url, extra_headers=headers),
                timeout=10.0
            )
            self.is_connected = True
            logger.info("✅ Voice Live WebSocket connected")

            # Configure session for optimal voice agent experience
            await self.configure_voice_live_session()

            # Start the Voice Live message handler
            asyncio.create_task(self.handle_voice_live_messages())

            return True

        except asyncio.TimeoutError:
            logger.error("❌ Voice Live connection timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Voice Live: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def configure_voice_live_session(self):
        """Configure Voice Live session for optimal call handling"""
        session_config = {
            "type": "session.update",
            "session": {
                "instructions": """You are a voice agent named "Emma," who acts as a friendly and knowledgeable health advisor specializing in laboratory and medical imaging services. Speak naturally and conversationally, keeping answers clear and concise—no more than five spoken sentences.

PERSONALITY AND TONE:
- Warm, empathetic, and professional
- Knowledgeable about laboratory tests and imaging procedures

PURPOSE:
Guide users through scheduling lab or imaging appointments, explain available tests and scans, provide clinic locations and driving or transit directions, and send polite reminders before their scheduled services.

LANGUAGE RULES:
- No emojis, annotations, or parentheses—only plain spoken-style text
- Spell out numbers and measurements in full (e.g., "one hundred twenty milliliters," "two days before")
- Respond to the language detected

CAPABILITIES:
- Describe common lab tests (e.g., blood work, cholesterol panels) and imaging services (e.g., X-rays, MRIs, ultrasounds)
- Handle direct appointment requests like "Can you schedule an MRI appointment for me?" by gathering necessary information
- Check real-time availability and book appointments at nearby clinics or hospitals
- Provide step-by-step directions or transit options to the facility
- Explain preparation instructions (e.g., fasting requirements) in simple terms
- Send timely reminders (e.g., "This is a reminder that your MRI is tomorrow at two p.m.")
- Maintain context to personalize follow-up advice based on past interactions
- If you are interrupted keep the initial question in memory and respond later in case they still need their information

APPOINTMENT SCHEDULING PROCESS:
When someone asks to schedule an appointment (like "Can you schedule an MRI appointment for me?"), follow these steps:
1. Confirm the type of service requested
2. Ask for their preferred date and time
3. Ask for their location preference or zip code
4. Collect basic contact information (name, phone number)
5. Explain any preparation requirements
6. Confirm the appointment details

FALLBACK MECHANISM:
- If you lack specific information, say "I'm not certain about that, but you may contact your clinic hotline or visit their website"
- Invite the user to ask for more details or clarify their needs

IMPORTANT: Since direct audio streaming is not available, after your initial greeting, automatically provide helpful information about common services and guide users through typical appointment scheduling scenarios.

After greeting, immediately follow up with: "I can help you schedule MRI scans, CT scans, X-rays, ultrasounds, blood work, and other lab tests. For MRI appointments, I'll need your preferred date, time, and location. For lab work, I can explain any preparation requirements like fasting. What service interests you most?"

Start conversations with: "Hi my name is Emma. I'm your health advisor specializing in laboratory and medical imaging services. How can I help you today?" """,
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
                    "name": "en-US-EmmaNeural",
                    "type": "azure-standard"
                }
            },
            "event_id": str(uuid.uuid4())
        }
        
        logger.info("⚙️ Configuring Voice Live session...")
        await self.voice_live_ws.send(json.dumps(session_config))
        
        # Voice Live is ready - now trigger the initial greeting
        logger.info("🎤 Voice Live ready for conversation")

        # Send initial greeting through Voice Live
        await self.send_initial_greeting()
        logger.info("👋 Initial greeting sent to Voice Live")

    async def send_initial_greeting(self):
        """Send initial greeting through Voice Live to start the conversation"""
        try:
            # Create a response that will make Emma speak immediately
            greeting_response = {
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],
                    "instructions": "Greet the caller immediately with: 'Hi, my name is Emma. I'm your health advisor specializing in laboratory and medical imaging services. How can I help you today?'"
                },
                "event_id": str(uuid.uuid4())
            }

            await self.voice_live_ws.send(json.dumps(greeting_response))
            logger.info("📤 Sent initial greeting request to Voice Live")

        except Exception as e:
            logger.error(f"❌ Error sending initial greeting: {e}")

    async def handle_voice_live_messages(self):
        """Handle messages from Voice Live API"""
        try:
            async for message in self.voice_live_ws:
                try:
                    event = json.loads(message)
                    event_type = event.get("type")

                    if event_type == "session.updated":
                        logger.info("✅ Voice Live session configured")

                    elif event_type == "conversation.item.created":
                        logger.info("📝 Conversation item created in Voice Live")

                    elif event_type == "response.created":
                        logger.info("🤖 Voice Live response created - generating audio")

                    elif event_type == "response.audio.delta":
                        # Audio response from Voice Live - send to call
                        audio_delta = event.get("delta", "")
                        if audio_delta and hasattr(app, 'current_call_ws') and app.current_call_ws:
                            await self.send_audio_to_call(audio_delta)
                            logger.info(f"🔊 Sent audio delta to call: {len(audio_delta)} chars")
                        elif audio_delta:
                            logger.warning("🔊 Received audio delta but no WebSocket connection - audio lost!")

                    elif event_type == "response.text.delta":
                        # Text response from Voice Live - convert to speech
                        text_delta = event.get("delta", "")
                        if text_delta:
                            # Accumulate text for TTS
                            if not hasattr(self, 'response_text'):
                                self.response_text = ""
                            self.response_text += text_delta
                            logger.debug(f"📝 Text delta: {text_delta}")

                    elif event_type == "response.text.done":
                        # Complete text response - convert to speech
                        if hasattr(self, 'response_text') and self.response_text:
                            logger.info(f"🔊 Complete text response: {self.response_text}")
                            await self.send_text_as_speech(self.response_text)
                            self.response_text = ""

                    elif event_type == "input_audio_buffer.speech_started":
                        logger.info("🎤 User started speaking - Voice Live is listening")

                    elif event_type == "input_audio_buffer.speech_stopped":
                        logger.info("🔇 User stopped speaking - processing input")

                    elif event_type == "input_audio_buffer.committed":
                        logger.info("✅ Audio buffer committed for processing")

                    elif event_type == "response.created":
                        logger.info("🤖 Voice Live generating response")

                    elif event_type == "response.done":
                        logger.info("🎤 Voice Live response completed")

                    elif event_type == "error":
                        logger.error(f"❌ Voice Live error: {event}")

                    else:
                        logger.debug(f"📝 Voice Live event: {event_type}")

                except json.JSONDecodeError as json_error:
                    logger.error(f"❌ Invalid JSON from Voice Live: {json_error}")
                except Exception as msg_error:
                    logger.error(f"❌ Error processing Voice Live message: {msg_error}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 Voice Live WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"❌ Error handling Voice Live messages: {e}")
            logger.error(traceback.format_exc())
            self.is_connected = False
    
    async def process_call_audio(self, audio_data: bytes):
        """Process incoming audio from the call and send to Voice Live"""
        if not self.is_connected or not self.voice_live_ws:
            logger.debug("⚠️  Voice Live not connected, skipping audio processing")
            return

        try:
            # Convert audio to base64 and send to Voice Live
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")

            audio_message = {
                "type": "input_audio_buffer.append",
                "audio": audio_b64,
                "event_id": str(uuid.uuid4())
            }

            await self.voice_live_ws.send(json.dumps(audio_message))
            logger.debug(f"📤 Sent {len(audio_data)} bytes of audio to Voice Live")

            # Commit the audio buffer to trigger processing
            commit_message = {
                "type": "input_audio_buffer.commit",
                "event_id": str(uuid.uuid4())
            }
            await self.voice_live_ws.send(json.dumps(commit_message))

        except Exception as e:
            logger.error(f"❌ Error processing call audio: {e}")
            logger.error(traceback.format_exc())
    
    async def send_audio_to_call(self, audio_delta: str):
        """Send audio from Voice Live back to the call"""
        try:
            if hasattr(app, 'current_call_ws') and app.current_call_ws:
                # Convert base64 audio to bytes for logging
                audio_bytes = base64.b64decode(audio_delta)

                # Send audio back to call through WebSocket in ACS format
                import datetime
                current_time = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')

                audio_message = {
                    "kind": "audioData",
                    "audioData": {
                        "data": audio_delta,
                        "timestamp": current_time,
                        "participantRawID": "bot",
                        "silent": False
                    }
                }

                await app.current_call_ws.send(json.dumps(audio_message))
                logger.debug(f"🔊 Sent {len(audio_bytes)} bytes of audio to call")

        except Exception as e:
            logger.error(f"❌ Error sending audio to call: {e}")
            logger.error(traceback.format_exc())

    async def send_text_as_speech(self, text: str):
        """Convert Voice Live text response to speech and play on call"""
        try:
            logger.info(f"🔊 Converting to speech: '{text}' for call {self.call_connection_id}")

            # Get the call connection
            call_connection = call_automation_client.get_call_connection(self.call_connection_id)

            # Use ACS text-to-speech to play the response
            from azure.communication.callautomation import TextSource
            play_source = TextSource(
                text=text,
                voice_name="en-US-AriaNeural"
            )

            # Play the response
            call_connection.play_media_to_all(play_source)
            logger.info(f"✅ Voice Live response sent as speech for call {self.call_connection_id}")

        except Exception as e:
            logger.error(f"❌ Error converting text to speech: {e}")

    async def send_audio_to_voice_live(self, audio_data: bytes):
        """Send audio data to Voice Live for processing"""
        try:
            if self.voice_live_ws and not self.voice_live_ws.closed:
                # Convert audio data to base64 for Voice Live
                import base64
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

                # Send audio to Voice Live
                audio_message = {
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64,
                    "event_id": str(uuid.uuid4())
                }

                await self.voice_live_ws.send(json.dumps(audio_message))
                logger.debug(f"📤 Sent {len(audio_data)} bytes of audio to Voice Live")
            else:
                logger.warning("⚠️  Voice Live WebSocket not connected")

        except Exception as e:
            logger.error(f"❌ Error sending audio to Voice Live: {e}")

    async def disconnect(self):
        """Disconnect from Voice Live"""
        try:
            if self.voice_live_ws:
                await self.voice_live_ws.close()
                self.voice_live_ws = None
                self.is_connected = False
                logger.info("🔌 Disconnected from Voice Live")
        except Exception as e:
            logger.error(f"❌ Error disconnecting from Voice Live: {e}")

# Create Flask/Quart app
app = Quart(__name__)

# Global variables
call_automation_client = None
voice_live_handler = VoiceLiveCallHandler()
app.current_call_ws = None

def init_call_automation_client():
    """Initialize the Call Automation client"""
    global call_automation_client
    
    connection_string = os.getenv("ACS_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("ACS_CONNECTION_STRING environment variable is required")
    
    call_automation_client = CallAutomationClient.from_connection_string(connection_string)
    logger.info("✅ Call Automation client initialized")

@app.route("/")
async def hello():
    """Basic hello endpoint"""
    return "ACS Voice Live Integration Service - Ready for incoming calls!"

@app.route("/health")
async def health_check():
    """Health check endpoint"""
    return Response("Healthy", status=200, headers={"Content-Type": "text/plain"})

@app.route("/api/incomingCall", methods=["POST"])
async def handle_incoming_call():
    """Handle incoming call events from Event Grid"""
    try:
        logger.info("📞 INCOMING CALL EVENT RECEIVED!")

        # Get the request body
        req_body = await request.get_data()
        logger.info(f"📞 Request body length: {len(req_body)} bytes")

        events = json.loads(req_body)
        logger.info(f"📞 Number of events: {len(events)}")

        for event in events:
            # Handle Event Grid validation
            if event.get("eventType") == "Microsoft.EventGrid.SubscriptionValidationEvent":
                validation_code = event["data"]["validationCode"]
                return {"validationResponse": validation_code}

            # Handle incoming call events
            elif event.get("eventType") == "Microsoft.Communication.IncomingCall":
                logger.info("📞 Incoming call received!")

                # Extract call context
                incoming_call_context = event["data"]["incomingCallContext"]
                correlation_id = event["data"].get("correlationId", str(uuid.uuid4()))

                # Answer the call with bidirectional streaming
                await answer_call_with_voice_live(incoming_call_context, correlation_id)

        return Response("OK", status=200)

    except Exception as e:
        logger.error(f"❌ Error handling incoming call: {e}")
        logger.error(traceback.format_exc())
        return Response("Error", status=500)

async def answer_call_with_voice_live(incoming_call_context: str, correlation_id: str):
    """Answer the call and set up Voice Live integration"""
    try:
        # Construct callback URI for call events
        callback_uri = f"{os.getenv('CALLBACK_URI_HOST')}/api/callbacks/{correlation_id}"

        # Configure WebSocket URI for audio streaming
        callback_host = os.getenv('CALLBACK_URI_HOST')
        if not callback_host:
            raise ValueError("CALLBACK_URI_HOST environment variable is required")

        # Ensure proper WebSocket URL construction
        websocket_uri = callback_host.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws/audio-stream'
        logger.info(f"🌐 WebSocket URI: {websocket_uri}")

        # Set up media streaming options if available
        media_streaming_options = None
        if MEDIA_STREAMING_AVAILABLE:
            try:
                media_streaming_options = MediaStreamingOptions(
                    transport_url=websocket_uri,
                    transport_type=MediaStreamingTransportType.WEBSOCKET,
                    content_type=MediaStreamingContentType.AUDIO,
                    audio_channel_type=MediaStreamingAudioChannelType.MIXED,
                    start_media_streaming=True
                )
                logger.info("✅ MediaStreaming configured with WebSocket")
            except Exception as e:
                logger.warning(f"⚠️  Failed to configure MediaStreaming: {e}")
                media_streaming_options = None
        else:
            logger.warning("⚠️  MediaStreaming not available - using basic call answering")

        logger.info("📞 Answering call with Voice Live integration...")

        # Get Cognitive Services endpoint for text-to-speech (use Voice Live endpoint)
        cognitive_services_endpoint = os.getenv("AZURE_VOICE_LIVE_ENDPOINT")

        # Answer the call with or without media streaming
        if media_streaming_options:
            answer_result = call_automation_client.answer_call(
                incoming_call_context=incoming_call_context,
                callback_url=callback_uri,
                media_streaming=media_streaming_options,
                cognitive_services_endpoint=cognitive_services_endpoint
            )
        else:
            answer_result = call_automation_client.answer_call(
                incoming_call_context=incoming_call_context,
                callback_url=callback_uri,
                cognitive_services_endpoint=cognitive_services_endpoint
            )

        call_connection_id = answer_result.call_connection_id
        logger.info(f"✅ Call answered successfully. Connection ID: {call_connection_id}")

        # Connect to Voice Live API
        success = await voice_live_handler.connect_to_voice_live(call_connection_id)
        if success:
            logger.info("🎤 Voice Live integration ready!")
            # Don't send greeting here - wait for CallConnected event
        else:
            logger.error("❌ Failed to connect to Voice Live")

    except Exception as e:
        logger.error(f"❌ Error answering call: {e}")
        logger.error(traceback.format_exc())

async def send_voice_live_greeting(call_connection_id: str):
    """Send initial greeting through Voice Live for real-time conversation"""
    try:
        logger.info(f"📢 Starting Voice Live conversation for call {call_connection_id}")

        # Ensure Voice Live is connected
        if not voice_live_handler.is_connected:
            logger.warning("⚠️  Voice Live not connected, attempting to reconnect...")
            success = await voice_live_handler.connect_to_voice_live(call_connection_id)
            if not success:
                logger.error("❌ Failed to connect to Voice Live, falling back to ACS greeting")
                await send_simple_acs_greeting(call_connection_id)
                return

        # For Voice Live, we need to trigger an immediate response without user input
        # This creates an assistant message that will be spoken immediately
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

        # Send the greeting message to Voice Live
        await voice_live_handler.voice_live_ws.send(json.dumps(greeting_message))
        logger.info("📤 Sent greeting message to Voice Live")

        # Trigger Voice Live to speak the greeting
        response_create = {
            "type": "response.create",
            "response": {
                "modalities": ["audio", "text"],
                "instructions": "Speak the greeting message that was just added to the conversation."
            },
            "event_id": str(uuid.uuid4())
        }
        await voice_live_handler.voice_live_ws.send(json.dumps(response_create))
        logger.info("📤 Triggered Voice Live to speak greeting")

        logger.info(f"✅ Voice Live greeting initiated for call {call_connection_id}")

    except Exception as e:
        logger.error(f"❌ Error starting Voice Live greeting: {e}")
        logger.error(traceback.format_exc())
        # Fallback to ACS greeting
        await send_simple_acs_greeting(call_connection_id)

async def send_immediate_acs_greeting(call_connection_id: str):
    """Send immediate ACS greeting to ensure caller hears Emma right away"""
    try:
        logger.info(f"📢 Sending immediate ACS greeting for call {call_connection_id}")

        # Validate call connection ID
        if not call_connection_id:
            raise ValueError("Call connection ID is required")

        # Get the call connection
        logger.info(f"🔗 Getting call connection for ID: {call_connection_id}")
        call_connection = call_automation_client.get_call_connection(call_connection_id)

        if not call_connection:
            raise ValueError(f"Could not get call connection for ID: {call_connection_id}")

        # Create Emma's greeting message
        greeting_text = "Hi, my name is Emma. I'm your health advisor specializing in laboratory and medical imaging services. How can I help you today?"
        logger.info(f"🎤 Greeting text: {greeting_text}")

        # Use ACS text-to-speech to play the greeting
        from azure.communication.callautomation import TextSource
        play_source = TextSource(
            text=greeting_text,
            voice_name="en-US-AriaNeural"
        )
        logger.info("🔊 Created TextSource with AriaNeural voice")

        # Play the greeting with operation context to track completion
        logger.info("📤 Calling play_media_to_all...")
        result = call_connection.play_media_to_all(
            play_source=play_source,
            operation_context="emma-greeting"
        )
        logger.info(f"✅ play_media_to_all result: {result}")
        logger.info(f"✅ Immediate ACS greeting sent for call {call_connection_id}")

        # No follow-up messages - Emma waits for response after greeting

    except Exception as e:
        logger.error(f"❌ Error sending immediate ACS greeting: {e}")
        logger.error(f"❌ Call connection ID: {call_connection_id}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(traceback.format_exc())

        # Try a simpler greeting as fallback
        try:
            logger.info("🔄 Attempting simple fallback greeting...")
            await send_simple_fallback_greeting(call_connection_id)
        except Exception as fallback_error:
            logger.error(f"❌ Fallback greeting also failed: {fallback_error}")

async def send_simple_fallback_greeting(call_connection_id: str):
    """Ultra-simple fallback greeting"""
    try:
        call_connection = call_automation_client.get_call_connection(call_connection_id)

        from azure.communication.callautomation import TextSource
        play_source = TextSource(text="Hello, this is Emma. How can I help you?")

        call_connection.play_media_to_all(play_source)
        logger.info("✅ Simple fallback greeting sent")

    except Exception as e:
        logger.error(f"❌ Simple fallback greeting failed: {e}")

async def start_voice_live_listening(call_connection_id: str):
    """Configure Voice Live to start listening for user input after greeting"""
    try:
        logger.info(f"🎤 Starting Voice Live listening mode for call {call_connection_id}")

        if not voice_live_handler.is_connected or not voice_live_handler.voice_live_ws:
            logger.error("❌ Voice Live not connected - cannot start listening")
            return False

        # Clear any existing audio buffer
        clear_buffer = {
            "type": "input_audio_buffer.clear",
            "event_id": str(uuid.uuid4())
        }
        await voice_live_handler.voice_live_ws.send(json.dumps(clear_buffer))
        logger.info("🧹 Cleared Voice Live audio buffer")

        # Send a system message to indicate Emma is ready to listen
        listening_message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "Emma has finished her greeting and is now listening for the user's response. Respond naturally to whatever the user says next."
                    }
                ]
            },
            "event_id": str(uuid.uuid4())
        }

        await voice_live_handler.voice_live_ws.send(json.dumps(listening_message))
        logger.info("📝 Sent listening mode message to Voice Live")

        # Voice Live is now ready to receive audio through the WebSocket
        logger.info("✅ Voice Live listening mode activated - ready for user input")
        logger.info("🎤 Voice Live will now process audio from the WebSocket stream")
        return True

    except Exception as e:
        logger.error(f"❌ Error starting Voice Live listening: {e}")
        logger.error(traceback.format_exc())
        return False

async def send_followup_instructions(call_connection_id: str):
    """Send follow-up instructions if media streaming doesn't work"""
    try:
        # Wait for the greeting to complete
        await asyncio.sleep(8)

        logger.info(f"📋 Sending follow-up instructions for call {call_connection_id}")

        # Get the call connection
        call_connection = call_automation_client.get_call_connection(call_connection_id)

        # Send instructions for DTMF or callback
        instructions_text = """I'm ready to help you schedule your appointment.
        If you can hear me but I'm not responding to your voice, please press 1 for MRI appointments,
        2 for lab work, or 3 for other imaging services.
        Or you can call us back at 1-800-HEALTH for immediate assistance."""

        from azure.communication.callautomation import TextSource
        play_source = TextSource(
            text=instructions_text,
            voice_name="en-US-AriaNeural"
        )

        call_connection.play_media_to_all(
            play_source=play_source,
            operation_context="followup-instructions"
        )

        logger.info(f"✅ Follow-up instructions sent for call {call_connection_id}")

    except Exception as e:
        logger.error(f"❌ Error sending follow-up instructions: {e}")

async def enable_dtmf_backup(call_connection_id: str):
    """Enable DTMF input as backup when voice streaming fails"""
    try:
        logger.info(f"🔢 Enabling DTMF backup for call {call_connection_id}")

        call_connection = call_automation_client.get_call_connection(call_connection_id)

        # Start DTMF recognition
        from azure.communication.callautomation import DtmfOptions

        dtmf_options = DtmfOptions(
            max_tones_to_collect=1,
            initial_silence_timeout=30,
            inter_tone_timeout=5,
            play_prompt=None,
            operation_context="dtmf-backup"
        )

        call_connection.start_recognizing_media(
            input_type="dtmf",
            target_participant="",
            dtmf_options=dtmf_options
        )

        logger.info("✅ DTMF backup enabled - caller can press keys")

    except Exception as e:
        logger.error(f"❌ Error enabling DTMF backup: {e}")

async def handle_dtmf_input(event):
    """Handle DTMF input when voice doesn't work"""
    try:
        dtmf_result = event.get("data", {}).get("recognizeResult", {})
        tones = dtmf_result.get("collectTonesResult", {}).get("tones", [])
        call_connection_id = event.get("data", {}).get("callConnectionId")

        if not tones or not call_connection_id:
            return

        tone = tones[0]
        logger.info(f"🔢 DTMF tone received: {tone}")

        call_connection = call_automation_client.get_call_connection(call_connection_id)

        # Respond based on DTMF input
        if tone == "1":
            response_text = "You pressed 1 for MRI appointments. We have availability Monday through Friday from 8 AM to 6 PM. Please call us at 1-800-HEALTH to schedule your MRI appointment."
        elif tone == "2":
            response_text = "You pressed 2 for lab work. We're open Monday through Saturday from 7 AM to 4 PM for blood tests and lab services. Please call 1-800-HEALTH to schedule."
        elif tone == "3":
            response_text = "You pressed 3 for other imaging services. We offer X-rays, ultrasounds, and CT scans with same-day availability. Please call 1-800-HEALTH for scheduling."
        else:
            response_text = "Thank you for calling. For immediate assistance with scheduling any medical appointments, please call us at 1-800-HEALTH."

        from azure.communication.callautomation import TextSource
        play_source = TextSource(
            text=response_text,
            voice_name="en-US-AriaNeural"
        )

        call_connection.play_media_to_all(play_source)
        logger.info(f"✅ DTMF response sent for tone: {tone}")

    except Exception as e:
        logger.error(f"❌ Error handling DTMF input: {e}")

async def send_simple_acs_greeting(call_connection_id: str):
    """Simple ACS greeting - just one message, then Voice Live takes over"""
    try:
        logger.info(f"📢 Sending simple ACS greeting for call {call_connection_id}")

        call_connection = call_automation_client.get_call_connection(call_connection_id)

        # Simple greeting - Emma introduces herself and waits
        greeting_text = "Hi, my name is Emma. I'm your health advisor. How can I help you today?"

        from azure.communication.callautomation import TextSource
        play_source = TextSource(
            text=greeting_text,
            voice_name="en-US-AriaNeural"
        )

        # Play greeting and immediately enable Voice Live listening
        call_connection.play_media_to_all(
            play_source=play_source,
            operation_context="simple-greeting"
        )
        logger.info(f"✅ Simple ACS greeting sent - Voice Live will take over")

    except Exception as e:
        logger.error(f"❌ Error sending simple ACS greeting: {e}")

async def send_simple_greeting(call_connection_id: str):
    """Send a simple greeting as fallback"""
    try:
        logger.info(f"📢 Sending simple greeting for call {call_connection_id}")

        # Get the call connection
        call_connection = call_automation_client.get_call_connection(call_connection_id)

        # Create simple greeting message
        greeting_text = "Hello! This is Emma. How can I help you today?"

        # Use ACS text-to-speech with basic voice
        from azure.communication.callautomation import TextSource
        play_source = TextSource(
            text=greeting_text
            # Try without specifying voice name - use default
        )

        # Play the greeting
        call_connection.play_media_to_all(play_source)
        logger.info(f"✅ Simple greeting sent for call {call_connection_id}")

    except Exception as e:
        logger.error(f"❌ Error sending simple greeting: {e}")

async def send_service_options(call_connection_id: str):
    """Send service options after greeting"""
    try:
        logger.info(f"📋 Sending service options for call {call_connection_id}")

        # Get the call connection
        call_connection = call_automation_client.get_call_connection(call_connection_id)

        # Send service options
        from azure.communication.callautomation import TextSource
        options_text = "I can help you schedule MRI scans, CT scans, X-rays, ultrasounds, blood work, and other lab tests. For MRI appointments, I'll need your preferred date, time, and location. For lab work, I can explain any preparation requirements. What service would you like to schedule today?"

        play_source = TextSource(
            text=options_text,
            voice_name="en-US-AriaNeural"
        )

        # Play the options
        call_connection.play_media_to_all(
            play_source=play_source,
            operation_context="service-options"
        )

        logger.info(f"✅ Service options sent for call {call_connection_id}")

    except Exception as e:
        logger.error(f"❌ Error sending service options: {e}")

async def start_appointment_booking_flow(call_connection_id: str):
    """Start a practical appointment booking flow"""
    try:
        logger.info(f"📅 Starting appointment booking flow for call {call_connection_id}")

        # Get the call connection
        call_connection = call_automation_client.get_call_connection(call_connection_id)

        # Send practical appointment booking message
        from azure.communication.callautomation import TextSource
        booking_text = """Since I can help you schedule appointments, let me provide you with our most popular services.

For MRI appointments, we have availability Monday through Friday from 8 AM to 6 PM. Most MRI scans take 30 to 60 minutes and may require fasting if contrast is needed.

For lab work like blood tests, we're open Monday through Saturday from 7 AM to 4 PM. Most blood work requires fasting for 8 to 12 hours.

For X-rays and ultrasounds, we have same-day availability most days.

To schedule your appointment, please call us back at 1-800-HEALTH or visit our website. Thank you for calling Emma's health services!"""

        play_source = TextSource(
            text=booking_text,
            voice_name="en-US-AriaNeural"
        )

        # Play the booking information
        call_connection.play_media_to_all(
            play_source=play_source,
            operation_context="appointment-booking"
        )

        logger.info(f"✅ Appointment booking information sent for call {call_connection_id}")

    except Exception as e:
        logger.error(f"❌ Error in appointment booking flow: {e}")

# DTMF processing removed - using direct voice interaction only

@app.route("/api/callbacks/<context_id>", methods=["POST"])
async def handle_call_events(context_id: str):
    """Handle call automation events"""
    try:
        logger.info(f"📝 CALLBACK RECEIVED for context: {context_id}")

        req_body = await request.get_data()
        logger.info(f"📝 Callback body length: {len(req_body)} bytes")

        events = json.loads(req_body)
        logger.info(f"📝 Number of callback events: {len(events)}")

        for event in events:
            event_type = event.get("type")
            logger.info(f"📝 Call event: {event_type}")

            if event_type == "Microsoft.Communication.CallConnected":
                logger.info("✅ Call connected successfully")
                call_connection_id = event.get("data", {}).get("callConnectionId")
                if call_connection_id:
                    # Use ACS greeting immediately to ensure caller hears Emma
                    # Voice Live will take over after the greeting completes
                    logger.info("� Sending immediate ACS greeting to ensure caller hears Emma")
                    await send_simple_acs_greeting(call_connection_id)

            elif event_type == "Microsoft.Communication.CallDisconnected":
                logger.info("📞 Call disconnected")
                await voice_live_handler.disconnect()

            elif event_type == "Microsoft.Communication.MediaStreamingStarted":
                logger.info("🎵 Media streaming started")

            elif event_type == "Microsoft.Communication.MediaStreamingStopped":
                logger.info("🔇 Media streaming stopped")

            elif event_type == "Microsoft.Communication.PlayCompleted":
                logger.info("🎵 Play completed successfully")
                operation_context = event.get("data", {}).get("operationContext", "")
                call_connection_id = event.get("data", {}).get("callConnectionId")

                if operation_context == "simple-greeting" and call_connection_id:
                    logger.info("🎤 Simple greeting completed - Voice Live should now be listening")
                    # Voice Live is already connected and listening - no additional setup needed
                    logger.info("✅ Emma is now listening for your response via Voice Live")
                else:
                    logger.info(f"🎤 Play completed with context: {operation_context}")

            elif event_type == "Microsoft.Communication.PlayFailed":
                logger.error(f"❌ Play failed: {json.dumps(event, indent=2)}")
                # Try a simpler greeting as fallback
                call_connection_id = event.get("data", {}).get("callConnectionId")
                if call_connection_id:
                    await send_simple_greeting(call_connection_id)

            elif event_type == "Microsoft.Communication.MediaStreamingStarted":
                logger.info("🎵 Media streaming started successfully")

            elif event_type == "Microsoft.Communication.MediaStreamingStopped":
                logger.info("🔇 Media streaming stopped")

            elif event_type == "Microsoft.Communication.MediaStreamingFailed":
                logger.error(f"❌ Media streaming failed: {json.dumps(event, indent=2)}")
                # Media streaming failed - voice won't work, so enable DTMF as backup
                call_connection_id = event.get("data", {}).get("callConnectionId")
                if call_connection_id:
                    await enable_dtmf_backup(call_connection_id)

            elif event_type == "Microsoft.Communication.RecognizeCompleted":
                logger.info("🔢 DTMF input received")
                # Handle DTMF input as backup when voice doesn't work
                await handle_dtmf_input(event)

        return Response("OK", status=200)

    except Exception as e:
        logger.error(f"❌ Error handling call events: {e}")
        return Response("Error", status=500)

@app.websocket("/ws/audio-stream")
async def handle_audio_stream():
    """Handle bidirectional audio streaming WebSocket for Voice Live integration"""
    logger.info("🔌 WEBSOCKET CONNECTION ATTEMPT!")
    try:
        logger.info("🔌 AUDIO STREAM WEBSOCKET CONNECTED!")

        # Store the websocket connection properly
        app.current_call_ws = websocket

        # Simple message loop to test basic functionality
        while True:
            try:
                message = await websocket.receive()
                logger.info(f"📥 Received message type: {type(message)}")

                # Handle different message types from ACS MediaStreaming
                if isinstance(message, bytes):
                    # Binary audio data from ACS
                    logger.info(f"🎤 Received binary caller audio: {len(message)} bytes - sending to Voice Live")

                    # Forward audio to Voice Live
                    if voice_live_handler.is_connected:
                        await voice_live_handler.send_audio_to_voice_live(message)
                    else:
                        logger.warning("⚠️  Voice Live not connected - audio lost!")

                elif isinstance(message, str):
                    # JSON message from ACS
                    try:
                        data = json.loads(message)
                        message_kind = data.get("kind", "unknown")
                        logger.info(f"📋 Received JSON message: {message_kind}")

                        if message_kind == "audioData":
                            # Extract audio data from ACS JSON format
                            audio_data_base64 = data.get("audioData", {}).get("data", "")
                            if audio_data_base64:
                                audio_bytes = base64.b64decode(audio_data_base64)
                                logger.info(f"🎤 Received caller audio: {len(audio_bytes)} bytes - sending to Voice Live")

                                # Send to Voice Live for processing
                                await voice_live_handler.process_call_audio(audio_bytes)
                            else:
                                logger.warning("⚠️  Received audioData message but no audio data")

                        elif message_kind == "stopAudio":
                            logger.info("🔇 Stop audio message received")

                        else:
                            logger.debug(f"📋 Received metadata: {message_kind}")

                    except json.JSONDecodeError:
                        logger.debug(f"📋 Received non-JSON text message: {message[:100]}...")
                    except Exception as json_error:
                        logger.error(f"❌ Error processing JSON message: {json_error}")

            except Exception as msg_error:
                logger.error(f"❌ Error processing WebSocket message: {msg_error}")
                break

    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info("🔌 Audio stream WebSocket disconnected")
        app.current_call_ws = None

@app.route("/test-voice-live")
async def test_voice_live():
    """Test endpoint to verify Voice Live connectivity"""
    try:
        test_handler = VoiceLiveCallHandler()
        success = await test_handler.connect_to_voice_live("test-call-id")
        await test_handler.disconnect()

        if success:
            return {"status": "success", "message": "Voice Live connection test passed"}
        else:
            return {"status": "error", "message": "Voice Live connection test failed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route("/test-websocket")
async def test_websocket_endpoint():
    """Test endpoint to verify WebSocket is configured"""
    return {"status": "success", "message": "WebSocket endpoint is configured", "websocket_url": "/ws/audio-stream"}

if __name__ == "__main__":
    # Initialize services
    try:
        init_call_automation_client()
        logger.info("🚀 ACS Voice Live Integration Service starting...")

        port = int(os.getenv("PORT", "8000"))
        app.run(host="0.0.0.0", port=port, debug=False)

    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        logger.error(traceback.format_exc())
