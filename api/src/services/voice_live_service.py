"""
Azure AI Voice Live API Service
Handles WebSocket connections and real-time audio streaming with Azure AI Voice Live API
"""

import os
import uuid
import json
import asyncio
import base64
import logging
import numpy as np
from typing import Dict, Union, Literal, Optional, Set, Callable, Awaitable, Any
from typing_extensions import AsyncIterator, TypedDict, Required
import websockets
from websockets.exceptions import WebSocketException
from typing import Union
from azure.identity import DefaultAzureCredential
from azure.core.credentials_async import AsyncTokenCredential

from ..config.settings import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)
AUDIO_SAMPLE_RATE = 24000

# Type definitions for Azure AI Voice Live API
AudioTimestampTypes = Literal["word"]

class AzureDeepNoiseSuppression(TypedDict, total=False):
    type: Literal["azure_deep_noise_suppression"]

class ServerEchoCancellation(TypedDict, total=False):
    type: Literal["server_echo_cancellation"]

class AzureSemanticDetection(TypedDict, total=False):
    model: Literal["semantic_detection_v1"]
    threshold: float
    timeout: float

EOUDetection = AzureSemanticDetection

class AzureSemanticVAD(TypedDict, total=False):
    type: Literal["azure_semantic_vad"]
    end_of_utterance_detection: EOUDetection
    threshold: float
    silence_duration_ms: int
    prefix_padding_ms: int

class Animation(TypedDict, total=False):
    outputs: Set[Literal["blendshapes", "viseme_id", "emotion"]]

class Session(TypedDict, total=False):
    voice: Dict[str, Union[str, float]]
    turn_detection: Union[AzureSemanticVAD]
    input_audio_noise_reduction: AzureDeepNoiseSuppression
    input_audio_echo_cancellation: ServerEchoCancellation
    animation: Animation
    output_audio_timestamp_types: Set[AudioTimestampTypes]

class SessionUpdateEventParam(TypedDict, total=False):
    type: Literal["session.update"]
    session: Required[Session]
    event_id: str

class AsyncVoiceLiveSessionResource:
    def __init__(self, connection: 'AsyncVoiceLiveConnection') -> None:
        self._connection = connection

    async def update(
        self,
        *,
        session: Session,
        event_id: str | None = None,
    ) -> None:
        param: SessionUpdateEventParam = {
            "type": "session.update", 
            "session": session, 
            "event_id": event_id or str(uuid.uuid4())
        }
        data = json.dumps(param)
        await self._connection.send(data)

class AsyncVoiceLiveConnection:
    session: AsyncVoiceLiveSessionResource
    _connection: Any

    def __init__(self, url: str, additional_headers: Dict[str, str]) -> None:
        self._url = url
        self._additional_headers = additional_headers
        self._connection = None
        self.session = AsyncVoiceLiveSessionResource(self)

    async def __aenter__(self) -> 'AsyncVoiceLiveConnection':
        try:
            self._connection = await websockets.connect(self._url, extra_headers=self._additional_headers)
            logger.info(f"Connected to Azure Voice Live API: {self._url}")
        except WebSocketException as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            raise ValueError(f"Failed to establish a WebSocket connection: {e}")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Voice Live WebSocket connection closed")
    
    enter = __aenter__
    close = __aexit__

    async def __aiter__(self) -> AsyncIterator[str]:
        async for data in self._connection:
            yield data

    async def recv(self) -> str:
        return await self._connection.recv()

    async def recv_bytes(self) -> bytes:
        data = await self._connection.recv()
        if isinstance(data, str):
            return data.encode('utf-8')
        return data

    async def send(self, message: Union[str, bytes]) -> None:
        await self._connection.send(message)

class AsyncAzureVoiceLive:
    def __init__(
        self,
        *,
        azure_endpoint: str | None = None,
        api_version: str | None = "2025-05-01-preview",
        api_key: str | None = None,
        azure_ad_token_credential: AsyncTokenCredential | None = None,
    ) -> None:
        if azure_endpoint is None:
            azure_endpoint = os.environ.get("AZURE_VOICE_LIVE_ENDPOINT")

        if azure_endpoint is None:
            raise ValueError(
                "Must provide the 'azure_endpoint' argument, or the 'AZURE_VOICE_LIVE_ENDPOINT' environment variable"
            )

        if api_key is None and azure_ad_token_credential is None:
            api_key = os.environ.get("AZURE_VOICE_LIVE_API_KEY")

        if api_key is None and azure_ad_token_credential is None:
            raise ValueError(
                "Missing credentials. Please pass one of 'api_key', 'azure_ad_token_credential', or the 'AZURE_VOICE_LIVE_API_KEY' environment variable."
            )

        if api_key and azure_ad_token_credential:
            raise ValueError(
                "Duplicating credentials. Please pass one of 'api_key' and 'azure_ad_token_credential'"
            )

        self._api_key = api_key
        self._azure_endpoint = azure_endpoint
        self._api_version = api_version
        self._azure_ad_token_credential = azure_ad_token_credential
        self._connection = None
        self._token = self.get_token() if azure_ad_token_credential else None

    def get_token(self) -> str:
        if self._azure_ad_token_credential:
            scopes = "https://cognitiveservices.azure.com/.default"
            token = self._azure_ad_token_credential.get_token(scopes)
            return token.token
        else:
            return None

    def refresh_token(self) -> None:
        self._token = self.get_token()

    def connect(self, model: str) -> AsyncVoiceLiveConnection:
        if self._connection is not None:
            raise ValueError("Already connected to the Azure Voice Agent service.")
        if not model:
            raise ValueError("Model name is required.")
        if not isinstance(model, str):
            raise TypeError(f"The 'model' parameter must be of type 'str', but got {type(model).__name__}.")

        url = f"{self._azure_endpoint.rstrip('/')}/voice-agent/realtime?api-version={self._api_version}&model={model}"
        url = url.replace("https://", "wss://")

        auth_header = {"Authorization": f"Bearer {self._token}"} if self._token else {"api-key": self._api_key}
        request_id = uuid.uuid4()
        headers = {"x-ms-client-request-id": str(request_id), **auth_header}

        self._connection = AsyncVoiceLiveConnection(
            url,
            additional_headers=headers,
        )
        return self._connection

class VoiceLiveService:
    """Service for handling Azure AI Voice Live API integration with ACS Call Automation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger(__name__)
        self.active_connections: Dict[str, AsyncVoiceLiveConnection] = {}
        self.audio_streams: Dict[str, Any] = {}
        
    async def create_voice_live_session(self, call_connection_id: str) -> AsyncVoiceLiveConnection:
        """Create a new Voice Live session for a call"""
        try:
            client = AsyncAzureVoiceLive(
                azure_endpoint=self.config.AZURE_VOICE_LIVE_ENDPOINT,
                api_key=self.config.AZURE_VOICE_LIVE_API_KEY,
            )
            
            connection = await client.connect(model=self.config.AZURE_VOICE_LIVE_DEPLOYMENT).__aenter__()
            
            # Configure the session with vida-voice-bot agent
            await connection.session.update(
                session={
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
                        "name": "en-US-Aria:DragonHDLatestNeural",
                        "type": "azure-standard",
                        "temperature": 0.8,
                    },
                }
            )
            
            self.active_connections[call_connection_id] = connection
            self.logger.info(f"Created Voice Live session for call {call_connection_id}")
            return connection
            
        except Exception as e:
            self.logger.error(f"Failed to create Voice Live session: {e}")
            raise
    
    async def close_voice_live_session(self, call_connection_id: str):
        """Close Voice Live session for a call"""
        if call_connection_id in self.active_connections:
            try:
                connection = self.active_connections[call_connection_id]
                await connection.__aexit__(None, None, None)
                del self.active_connections[call_connection_id]
                self.logger.info(f"Closed Voice Live session for call {call_connection_id}")
            except Exception as e:
                self.logger.error(f"Error closing Voice Live session: {e}")
    
    async def send_audio_to_voice_live(self, call_connection_id: str, audio_data: bytes):
        """Send audio data to Voice Live API"""
        if call_connection_id not in self.active_connections:
            self.logger.error(f"No active Voice Live connection for call {call_connection_id}")
            return
            
        try:
            connection = self.active_connections[call_connection_id]
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            param = {
                "type": "input_audio_buffer.append", 
                "audio": audio_base64, 
                "event_id": str(uuid.uuid4())
            }
            await connection.send(json.dumps(param))
        except Exception as e:
            self.logger.error(f"Error sending audio to Voice Live: {e}")
    
    async def receive_voice_live_events(self, call_connection_id: str, event_handler: Callable):
        """Receive and process events from Voice Live API"""
        if call_connection_id not in self.active_connections:
            self.logger.error(f"No active Voice Live connection for call {call_connection_id}")
            return
            
        try:
            connection = self.active_connections[call_connection_id]
            async for raw_event in connection:
                try:
                    event = json.loads(raw_event)
                    await event_handler(event)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to decode Voice Live event: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing Voice Live event: {e}")
        except Exception as e:
            self.logger.error(f"Error receiving Voice Live events: {e}")
