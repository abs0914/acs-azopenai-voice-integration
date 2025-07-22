"""
Audio Streaming Service for Azure Communication Services and Azure AI Voice Live integration
Handles bidirectional audio streaming between ACS calls and Voice Live API
"""

import asyncio
import json
import base64
import uuid
from typing import Dict, Any, Optional, Callable
from azure.communication.callautomation import CallAutomationClient

from ..config.settings import Config
from ..services.voice_live_service import VoiceLiveService
from ..utils.logger import setup_logger

class AudioStreamingService:
    """Handles bidirectional audio streaming between ACS and Voice Live API"""
    
    def __init__(self, config: Config, call_automation_client: CallAutomationClient, voice_live_service: VoiceLiveService):
        self.config = config
        self.call_automation_client = call_automation_client
        self.voice_live_service = voice_live_service
        self.logger = setup_logger(__name__)
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        
    async def start_bidirectional_streaming(self, call_connection_id: str, websocket_uri: str) -> bool:
        """Start Voice Live session for a call (simplified without bidirectional streaming)"""
        try:
            self.logger.info(f"Starting Voice Live session for call {call_connection_id}")

            # Create Voice Live session
            voice_live_connection = await self.voice_live_service.create_voice_live_session(call_connection_id)

            # Store streaming info
            self.active_streams[call_connection_id] = {
                "voice_live_connection": voice_live_connection,
                "streaming_active": True,
                "websocket_uri": websocket_uri
            }

            # Start processing Voice Live events
            asyncio.create_task(self._process_voice_live_events(call_connection_id))

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
            await self.voice_live_service.receive_voice_live_events(
                call_connection_id, 
                lambda event: self._handle_voice_live_event(call_connection_id, event)
            )
        except Exception as e:
            self.logger.error(f"Error processing Voice Live events: {e}")
    
    async def _handle_voice_live_event(self, call_connection_id: str, event: Dict[str, Any]):
        """Handle individual Voice Live API events"""
        try:
            event_type = event.get("type")
            
            if event_type == "response.audio.delta":
                # Handle audio response from Voice Live API
                audio_delta = event.get("delta", "")
                if audio_delta:
                    # Decode base64 audio data
                    audio_data = base64.b64decode(audio_delta)
                    
                    # Send audio back to ACS call
                    await self._send_audio_to_call(call_connection_id, audio_data)
                    
            elif event_type == "response.done":
                self.logger.info(f"Voice Live response completed for call {call_connection_id}")
                
            elif event_type == "error":
                error_message = event.get("error", {}).get("message", "Unknown error")
                self.logger.error(f"Voice Live API error for call {call_connection_id}: {error_message}")
                
            elif event_type == "session.updated":
                self.logger.info(f"Voice Live session updated for call {call_connection_id}")
                
            else:
                self.logger.debug(f"Unhandled Voice Live event type: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling Voice Live event: {e}")
    
    async def _send_audio_to_call(self, call_connection_id: str, audio_data: bytes):
        """Send audio data back to the ACS call"""
        try:
            if call_connection_id in self.active_streams and self.active_streams[call_connection_id]["streaming_active"]:
                # Convert audio data to format expected by ACS
                # This would typically involve sending the audio through the bidirectional stream
                call_connection = self.call_automation_client.get_call_connection(call_connection_id)
                
                # Note: The exact method for sending audio back through bidirectional streaming
                # may vary based on the ACS SDK implementation. This is a placeholder for the
                # actual implementation that would send audio back to the call participant.
                
                # For now, we'll log that we received audio to send back
                self.logger.debug(f"Received {len(audio_data)} bytes of audio to send to call {call_connection_id}")
                
        except Exception as e:
            self.logger.error(f"Error sending audio to call: {e}")
    
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
                        "remove_filler_words": False
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
