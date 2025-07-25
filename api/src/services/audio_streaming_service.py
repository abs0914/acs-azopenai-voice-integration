"""
Audio Streaming Service for Azure Communication Services and Azure AI Voice Live integration
Handles bidirectional audio streaming between ACS calls and Voice Live API
"""

import asyncio
import json
import base64
import uuid
import numpy as np
from typing import Dict, Any, Optional, Callable
from azure.communication.callautomation import CallAutomationClient

from ..config.settings import Config
from ..services.voice_live_service import VoiceLiveService
from ..utils.logger import setup_logger

def resample_audio(audio_data: bytes, source_rate: int = 24000, target_rate: int = 16000) -> bytes:
    """
    Resample audio data from source sample rate to target sample rate

    Args:
        audio_data: Raw PCM audio data as bytes
        source_rate: Source sample rate (default: 24000 Hz from Voice Live)
        target_rate: Target sample rate (default: 16000 Hz for ACS)

    Returns:
        Resampled audio data as bytes
    """
    try:
        # Convert bytes to numpy array (assuming 16-bit PCM)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # Calculate resampling ratio
        ratio = target_rate / source_rate

        # Calculate new length
        new_length = int(len(audio_array) * ratio)

        # Simple linear interpolation resampling
        # Create indices for the new sample points
        old_indices = np.arange(len(audio_array))
        new_indices = np.linspace(0, len(audio_array) - 1, new_length)

        # Interpolate
        resampled_array = np.interp(new_indices, old_indices, audio_array.astype(np.float32))

        # Convert back to int16 and then to bytes
        resampled_audio = resampled_array.astype(np.int16).tobytes()

        return resampled_audio

    except Exception as e:
        # If resampling fails, return original audio
        print(f"Warning: Audio resampling failed: {e}. Using original audio.")
        return audio_data

class AudioStreamingService:
    """Handles bidirectional audio streaming between ACS and Voice Live API"""
    
    def __init__(self, config: Config, call_automation_client: CallAutomationClient, voice_live_service: VoiceLiveService):
        self.config = config
        self.call_automation_client = call_automation_client
        self.voice_live_service = voice_live_service
        self.logger = setup_logger(__name__)
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
    async def start_bidirectional_streaming(self, call_connection_id: str, websocket_uri: str, websocket_connection=None) -> bool:
        """Start Voice Live session for a call with bidirectional streaming"""
        try:
            self.logger.info(f"Starting Voice Live session for call {call_connection_id}")

            # Create Voice Live session
            voice_live_connection = await self.voice_live_service.create_voice_live_session(call_connection_id)

            # Store streaming info including WebSocket connection for bidirectional streaming
            self.active_streams[call_connection_id] = {
                "voice_live_connection": voice_live_connection,
                "streaming_active": True,
                "websocket_uri": websocket_uri,
                "websocket_connection": websocket_connection
            }

            # Also store in active_sessions for audio processing
            self.active_sessions[call_connection_id] = {
                "voice_live_session_id": call_connection_id,
                "voice_live_connection": voice_live_connection,
                "streaming_active": True
            }

            # Start processing Voice Live events
            self.logger.info(f"Creating Voice Live event processing task for call {call_connection_id}")
            task = asyncio.create_task(self._process_voice_live_events(call_connection_id))
            self.logger.info(f"Voice Live event processing task created: {task}")

            # Initial response is already triggered in create_voice_live_session
            # await self._trigger_initial_response(call_connection_id)

            self.logger.info(f"Voice Live session started for call {call_connection_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error starting Voice Live session: {e}")
            return False
    
    async def stop_bidirectional_streaming(self, call_connection_id: str):
        """Stop Voice Live session for a call"""
        try:
            if call_connection_id in self.active_streams:
                # Close Voice Live session
                await self.voice_live_service.close_voice_live_session(call_connection_id)

                # Clean up
                self.active_streams[call_connection_id]["streaming_active"] = False
                del self.active_streams[call_connection_id]

                self.logger.info(f"Stopped Voice Live session for call {call_connection_id}")

        except Exception as e:
            self.logger.error(f"Error stopping Voice Live session: {e}")
    
    async def handle_incoming_audio(self, call_connection_id: str, audio_data: bytes):
        """Handle incoming audio from ACS call and forward to Voice Live API"""
        try:
            if call_connection_id in self.active_streams and self.active_streams[call_connection_id]["streaming_active"]:
                # Forward audio to Voice Live API
                await self.voice_live_service.send_audio_to_voice_live(call_connection_id, audio_data)
            else:
                self.logger.warning(f"No active stream for call {call_connection_id}")
                
        except Exception as e:
            self.logger.error(f"Error handling incoming audio: {e}")
    
    async def _process_voice_live_events(self, call_connection_id: str):
        """Process events from Voice Live API and handle audio responses"""
        try:
            self.logger.info(f"🎯 _process_voice_live_events method called for call {call_connection_id}")
            self.logger.info(f"Starting Voice Live event processing for call {call_connection_id}")
            self.logger.info(f"About to call voice_live_service.receive_voice_live_events for call {call_connection_id}")
            await self.voice_live_service.receive_voice_live_events(
                call_connection_id,
                lambda event: self._handle_voice_live_event(call_connection_id, event)
            )
            self.logger.info(f"Voice Live event processing completed for call {call_connection_id}")
        except Exception as e:
            self.logger.error(f"Error processing Voice Live events: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
    
    async def _handle_voice_live_event(self, call_connection_id: str, event: Dict[str, Any]):
        """Handle individual Voice Live API events"""
        try:
            event_type = event.get("type")
            self.logger.info(f"🎯 Handling Voice Live event type: {event_type} for call {call_connection_id}")

            if event_type == "response.audio.delta":
                # Handle audio response from Voice Live API
                self.logger.info(f"🎯 Full response.audio.delta event structure: {json.dumps(event, indent=2)}")

                # Try different possible locations for audio data
                audio_delta = None
                if "delta" in event:
                    audio_delta = event["delta"]
                    self.logger.info(f"🎯 Found audio data in 'delta' field")
                elif "audio" in event:
                    audio_delta = event["audio"]
                    self.logger.info(f"🎯 Found audio data in 'audio' field")
                elif "data" in event:
                    audio_delta = event["data"]
                    self.logger.info(f"🎯 Found audio data in 'data' field")

                self.logger.info(f"🎯 Received audio delta, length: {len(audio_delta) if audio_delta else 0} for call {call_connection_id}")
                if audio_delta:
                    # Decode base64 audio data
                    audio_data = base64.b64decode(audio_delta)
                    self.logger.info(f"🎯 Decoded audio data, length: {len(audio_data)} bytes for call {call_connection_id}")

                    # Resample audio from 24kHz (Voice Live) to 16kHz (ACS)
                    resampled_audio = resample_audio(audio_data, source_rate=24000, target_rate=16000)
                    self.logger.info(f"🎯 Resampled audio from {len(audio_data)} to {len(resampled_audio)} bytes for call {call_connection_id}")

                    # Send resampled audio back to ACS call
                    await self._send_audio_to_call(call_connection_id, resampled_audio)
                    self.logger.info(f"🎯 Sent {len(audio_data)} bytes of audio to call {call_connection_id}")
                else:
                    self.logger.warning(f"🎯 Empty audio delta received for call {call_connection_id}")
                    self.logger.warning(f"🎯 Available event keys: {list(event.keys())}")

            elif event_type == "response.done":
                self.logger.info(f"Voice Live response completed for call {call_connection_id}")

            elif event_type == "response.audio_transcript.done":
                self.logger.info(f"Voice Live audio transcript completed for call {call_connection_id}")

            elif event_type == "response.content_part.done":
                self.logger.info(f"Voice Live content part completed for call {call_connection_id}")

            elif event_type == "response.output_item.done":
                self.logger.info(f"Voice Live output item completed for call {call_connection_id}")

            elif event_type == "error":
                error_message = event.get("error", {}).get("message", "Unknown error")
                self.logger.error(f"Voice Live API error for call {call_connection_id}: {error_message}")

            elif event_type == "session.updated":
                self.logger.info(f"Voice Live session updated for call {call_connection_id}")

            else:
                self.logger.info(f"Unhandled Voice Live event type: {event_type} for call {call_connection_id}")

        except Exception as e:
            self.logger.error(f"Error handling Voice Live event: {e}")

    async def _trigger_initial_response(self, call_connection_id: str):
        """Trigger initial response from Voice Live to start conversation"""
        try:
            if call_connection_id in self.active_streams:
                voice_live_connection = self.active_streams[call_connection_id]["voice_live_connection"]

                # Check if connection is valid
                if voice_live_connection is None:
                    self.logger.error(f"Voice Live connection is None for call {call_connection_id}")
                    return

                # Check if connection has send method
                if not hasattr(voice_live_connection, 'send'):
                    self.logger.error(f"Voice Live connection does not have send method for call {call_connection_id}")
                    return

                # Initial response is now handled in create_voice_live_session
                # This method is kept for backward compatibility but does nothing
                self.logger.info(f"Initial response already triggered during session creation for call {call_connection_id}")

        except Exception as e:
            self.logger.error(f"Error in _trigger_initial_response: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")

    async def _send_audio_to_call(self, call_connection_id: str, audio_data: bytes):
        """Send audio data back to the ACS call through WebSocket"""
        try:
            self.logger.info(f"🎯 _send_audio_to_call called for call {call_connection_id}, audio length: {len(audio_data)}")

            if call_connection_id not in self.active_streams:
                self.logger.error(f"🎯 Call {call_connection_id} not found in active_streams")
                return

            stream_info = self.active_streams[call_connection_id]
            self.logger.info(f"🎯 Stream info for call {call_connection_id}: streaming_active={stream_info.get('streaming_active')}")

            if not stream_info.get("streaming_active"):
                self.logger.warning(f"🎯 Streaming not active for call {call_connection_id}")
                return

            # Get the WebSocket connection for this call
            websocket_connection = stream_info.get("websocket_connection")
            self.logger.info(f"🎯 WebSocket connection status for call {call_connection_id}: exists={websocket_connection is not None}, closed={websocket_connection.closed if websocket_connection else 'N/A'}")

            if websocket_connection and not websocket_connection.closed:
                # Convert audio data to base64 format expected by ACS
                import base64
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                self.logger.info(f"🎯 Encoded audio to base64, length: {len(audio_base64)} for call {call_connection_id}")

                # Create the JSON message format for ACS bidirectional streaming
                outbound_message = {
                    "Kind": "AudioData",
                    "AudioData": {
                        "Data": audio_base64
                    },
                    "StopAudio": None
                }

                # Send the audio data back to ACS through WebSocket
                import json
                message_json = json.dumps(outbound_message)
                self.logger.info(f"🎯 Sending WebSocket message, JSON length: {len(message_json)} for call {call_connection_id}")

                await websocket_connection.send(message_json)
                self.logger.info(f"🎯 Successfully sent {len(audio_data)} bytes of audio back to call {call_connection_id}")
            else:
                if not websocket_connection:
                    self.logger.error(f"🎯 No WebSocket connection found for call {call_connection_id}")
                else:
                    self.logger.error(f"🎯 WebSocket connection is closed for call {call_connection_id}")

        except Exception as e:
            self.logger.error(f"🎯 Error sending audio to call {call_connection_id}: {e}")
            import traceback
            self.logger.error(f"🎯 Full traceback: {traceback.format_exc()}")

    async def stop_audio_playback(self, call_connection_id: str):
        """Stop audio playback in the ACS call"""
        try:
            if call_connection_id in self.active_streams and self.active_streams[call_connection_id]["streaming_active"]:
                websocket_connection = self.active_streams[call_connection_id].get("websocket_connection")

                if websocket_connection and not websocket_connection.closed:
                    # Create stop audio message
                    stop_message = {
                        "Kind": "StopAudio",
                        "AudioData": None,
                        "StopAudio": {}
                    }

                    import json
                    message_json = json.dumps(stop_message)
                    await websocket_connection.send(message_json)

                    self.logger.debug(f"Sent stop audio command for call {call_connection_id}")

        except Exception as e:
            self.logger.error(f"Error stopping audio playback: {e}")

    def is_streaming_active(self, call_connection_id: str) -> bool:
        """Check if bidirectional streaming is active for a call"""
        return (call_connection_id in self.active_streams and 
                self.active_streams[call_connection_id].get("streaming_active", False))
    
    async def handle_media_streaming_event(self, call_connection_id: str, event_data: Dict[str, Any]):
        """Handle media streaming events from ACS"""
        try:
            event_type = event_data.get("type")
            
            if event_type == "audio":
                # Extract audio data from the event
                audio_data_base64 = event_data.get("data", "")
                if audio_data_base64:
                    audio_data = base64.b64decode(audio_data_base64)
                    await self.handle_incoming_audio(call_connection_id, audio_data)
                    
            elif event_type == "streaming_started":
                self.logger.info(f"Media streaming started for call {call_connection_id}")
                
            elif event_type == "streaming_stopped":
                self.logger.info(f"Media streaming stopped for call {call_connection_id}")
                await self.stop_bidirectional_streaming(call_connection_id)
                
            else:
                self.logger.debug(f"Unhandled media streaming event type: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling media streaming event: {e}")
    
    async def configure_voice_live_session(self, call_connection_id: str, assistant_id: Optional[str] = None):
        """Configure Voice Live session with specific assistant and settings"""
        try:
            if call_connection_id in self.active_streams:
                voice_live_connection = self.active_streams[call_connection_id]["voice_live_connection"]
                
                # Configure session with vida-voice-bot agent
                session_config = {
                    "turn_detection": {
                        "type": "azure_semantic_vad",
                        "threshold": 0.3,
                        "prefix_padding_ms": 200,
                        "silence_duration_ms": 200,
                        "remove_filler_words": False,
                        "end_of_utterance_detection": None
                    },
                    "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
                    "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
                    "voice": {
                        "name": "en-US-Aria:DragonHDLatestNeural",
                        "type": "azure-standard",
                        "temperature": 0.8,
                    },
                }
                
                # Note: assistant_id is not supported in Voice Live API session configuration
                # The vida-voice-bot agent integration would be handled differently
                
                await voice_live_connection.session.update(session=session_config)
                self.logger.info(f"Configured Voice Live session for call {call_connection_id}")
                
        except Exception as e:
            self.logger.error(f"Error configuring Voice Live session: {e}")

    async def stop_bidirectional_streaming(self, call_connection_id: str) -> bool:
        """Stop bidirectional streaming for a call"""
        try:
            self.logger.info(f"Stopping bidirectional streaming for call {call_connection_id}")

            # Stop Voice Live session
            if call_connection_id in self.active_sessions:
                session_info = self.active_sessions[call_connection_id]
                voice_live_session_id = session_info.get("voice_live_session_id")

                if voice_live_session_id:
                    await self.voice_live_service.end_session(voice_live_session_id)
                    self.logger.info(f"Voice Live session {voice_live_session_id} ended")

                # Clean up session
                del self.active_sessions[call_connection_id]
                self.logger.info(f"Cleaned up session for call {call_connection_id}")

            # Also clean up streams
            if call_connection_id in self.active_streams:
                del self.active_streams[call_connection_id]
                self.logger.info(f"Cleaned up stream for call {call_connection_id}")

            return True

        except Exception as e:
            self.logger.error(f"Error stopping bidirectional streaming for call {call_connection_id}: {e}")
            return False

    async def configure_audio_settings(self, call_connection_id: str, audio_metadata: dict):
        """Configure audio settings based on ACS metadata"""
        try:
            self.logger.info(f"Configuring audio settings for call {call_connection_id}: {audio_metadata}")

            if call_connection_id in self.active_sessions:
                session_info = self.active_sessions[call_connection_id]
                session_info["audio_metadata"] = audio_metadata

                # Extract audio settings
                encoding = audio_metadata.get("encoding", "PCM")
                sample_rate = audio_metadata.get("sampleRate", 16000)
                channels = audio_metadata.get("channels", 1)

                self.logger.info(f"Audio settings - Encoding: {encoding}, Sample Rate: {sample_rate}, Channels: {channels}")

        except Exception as e:
            self.logger.error(f"Error configuring audio settings for call {call_connection_id}: {e}")

    async def process_incoming_audio(self, call_connection_id: str, audio_data: dict):
        """Process incoming audio data from ACS and forward to Voice Live"""
        try:
            if call_connection_id not in self.active_sessions:
                self.logger.warning(f"No active session for call {call_connection_id}")
                return

            session_info = self.active_sessions[call_connection_id]
            voice_live_session_id = session_info.get("voice_live_session_id")

            if not voice_live_session_id:
                self.logger.warning(f"No Voice Live session for call {call_connection_id}")
                return

            # Extract audio data
            timestamp = audio_data.get("timestamp")
            participant_id = audio_data.get("participantRawID")
            audio_base64 = audio_data.get("data")
            is_silent = audio_data.get("silent", False)

            if not is_silent and audio_base64:
                # Decode base64 audio data
                import base64
                audio_bytes = base64.b64decode(audio_base64)

                # Forward to Voice Live
                await self.voice_live_service.send_audio_data(voice_live_session_id, audio_bytes)
                self.logger.debug(f"Forwarded {len(audio_bytes)} bytes of audio to Voice Live")

        except Exception as e:
            self.logger.error(f"Error processing incoming audio for call {call_connection_id}: {e}")
