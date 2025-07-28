import asyncio
import json
import logging
import base64
import websockets
from typing import Optional, Callable
import azure.cognitiveservices.speech as speechsdk
from ..config.settings import Config

class AzureSpeechService:
    """Azure Speech Services integration for STT and TTS"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.speech_config = None
        self.speech_recognizer = None
        self.speech_synthesizer = None
        self._setup_speech_config()
    
    def _setup_speech_config(self):
        """Initialize Azure Speech Services configuration"""
        try:
            # Create speech config
            self.speech_config = speechsdk.SpeechConfig(
                subscription=Config.AZURE_SPEECH_API_KEY,
                region=Config.AZURE_SPEECH_REGION
            )
            
            # Configure speech recognition
            self.speech_config.speech_recognition_language = "en-US"
            
            # Configure speech synthesis
            self.speech_config.speech_synthesis_voice_name = Config.AZURE_SPEECH_VOICE
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm
            )
            
            self.logger.info(f"Azure Speech Services configured - Region: {Config.AZURE_SPEECH_REGION}, Voice: {Config.AZURE_SPEECH_VOICE}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Azure Speech Services: {e}")
            raise
    
    async def recognize_speech_from_audio(self, audio_data: bytes) -> Optional[str]:
        """Convert audio to text using Azure Speech Services"""
        try:
            # Create audio config from audio data
            audio_format = speechsdk.audio.AudioStreamFormat(
                samples_per_second=24000,
                bits_per_sample=16,
                channels=1
            )
            
            # Create push audio input stream
            push_stream = speechsdk.audio.PushAudioInputStream(audio_format)
            push_stream.write(audio_data)
            push_stream.close()
            
            audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                self.logger.info(f"Speech recognized: {result.text}")
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                self.logger.warning("No speech could be recognized")
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                self.logger.error(f"Speech recognition canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    self.logger.error(f"Error details: {cancellation_details.error_details}")
                return None
                
        except Exception as e:
            self.logger.error(f"Speech recognition error: {e}")
            return None
    
    async def synthesize_speech_to_audio(self, text: str) -> Optional[bytes]:
        """Convert text to audio using Azure Speech Services"""
        try:
            # Create speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # Use default audio output
            )
            
            # Perform synthesis
            result = speech_synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                self.logger.info(f"Speech synthesized for text: {text[:50]}...")
                return result.audio_data
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                self.logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    self.logger.error(f"Error details: {cancellation_details.error_details}")
                return None
                
        except Exception as e:
            self.logger.error(f"Speech synthesis error: {e}")
            return None
    
    async def process_conversation_turn(self, audio_data: bytes, context: str = "") -> Optional[bytes]:
        """Process a complete conversation turn: STT -> AI -> TTS"""
        try:
            # Step 1: Convert speech to text
            user_text = await self.recognize_speech_from_audio(audio_data)
            if not user_text:
                return None
            
            # Step 2: Generate AI response (simple echo for now)
            ai_response = f"Hello! I heard you say: {user_text}. How can I help you today?"
            
            # Step 3: Convert AI response to speech
            response_audio = await self.synthesize_speech_to_audio(ai_response)
            
            return response_audio
            
        except Exception as e:
            self.logger.error(f"Conversation turn processing error: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.speech_recognizer:
                self.speech_recognizer = None
            if self.speech_synthesizer:
                self.speech_synthesizer = None
            self.logger.info("Azure Speech Services cleaned up")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
