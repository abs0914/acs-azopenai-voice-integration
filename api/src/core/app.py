import uuid
import json
from urllib.parse import urlencode
from quart import Quart, Response, request
from azure.eventgrid import EventGridEvent, SystemEventNames
from azure.core.messaging import CloudEvent
from azure.communication.callautomation import (
    PhoneNumberIdentifier,
    CallAutomationClient,
    MediaStreamingOptions,
    MediaStreamingContentType,
    MediaStreamingAudioChannelType,
    MediaStreamingTransportType,
    TextSource
)
from azure.core.exceptions import AzureError
import asyncio

from src.config.settings import Config
from src.config.constants import EventTypes, StatusCodes, ApiPayloadKeysForValidation
from src.services.call_handler import CallHandler
from src.services.cache_service import CacheService
from src.services.openai_service import OpenAIService
from src.services.voice_live_service import VoiceLiveService
from src.services.audio_streaming_service import AudioStreamingService
from src.core.event_handlers import EventHandlers
from src.services.cosmosdb_service import CosmosDBService

from src.utils.logger import setup_logger


class CallAutomationApp:
    """Main application class"""

    def __init__(self):
        self.app = Quart(__name__)
        self.config = Config()
        self.logger = setup_logger(__name__)

        # Initialize services
        self.cache_service = CacheService(self.config.REDIS_URL, self.config.REDIS_PASSWORD)
        self.call_automation_client = CallAutomationClient.from_connection_string(
            self.config.ACS_CONNECTION_STRING
        )
        self.call_handler = CallHandler(self.config, self.call_automation_client)
        self.openai_service = OpenAIService(self.config, self.cache_service)

        # Initialize CosmosDBService
        self.cosmosdb_service = CosmosDBService(self.config)

        # Initialize Voice Live services
        self.voice_live_service = VoiceLiveService(self.config)
        self.audio_streaming_service = AudioStreamingService(
            self.config,
            self.call_automation_client,
            self.voice_live_service
        )

        # Initialize event handlers with all required services
        self.event_handlers = EventHandlers(
            call_handler=self.call_handler,
            cache_service=self.cache_service,
            openai_service=self.openai_service,
            cosmosdb_service=self.cosmosdb_service,
            voice_live_service=self.voice_live_service,
            audio_streaming_service=self.audio_streaming_service,
            config=self.config,
        )

        self.setup_routes()
        self.logger.info("Application initialized successfully V1.0 - Azure AI Voice Live Integration")

    def setup_routes(self):
        """Set up application routes"""
        self.app.route("/")(self.hello)
        self.app.route("/robots933456.txt")(self.health_check)
        self.app.route("/api/callbacks/<context_id>", methods=["POST"])(
            self.handle_callback
        )
        # EventGrid webhook validation endpoint
        self.app.route("/api/callback", methods=["POST"])(
            self.handle_eventgrid_validation
        )
        self.app.route("/api/incomingCall", methods=["POST"])(
            self.incoming_call_handler
        )
        self.app.route("/api/initiateOutboundCall", methods=["POST"])(
            self.initiate_outbound_call
        )

        # Alternative solution endpoint
        self.app.route("/api/testIncomingCall", methods=["POST"])(
            self.test_incoming_call_handler
        )

        # Media streaming endpoint for Voice Live integration
        self.app.route("/api/mediaStreaming/<call_connection_id>", methods=["POST"])(
            self.handle_media_streaming
        )

        # Test endpoint for Voice Live connection
        self.app.route("/api/testVoiceLive", methods=["GET"])(
            self.test_voice_live_connection
        )

        # WebSocket endpoint for media streaming
        @self.app.websocket("/ws")
        async def websocket_handler():
            from quart import websocket
            self.logger.info("🎯 WebSocket connection attempt detected on /ws")
            self.logger.info(f"WebSocket headers: {dict(websocket.headers) if hasattr(websocket, 'headers') else 'No headers'}")
            return await self.handle_websocket_media_streaming(websocket)

        # Alternative WebSocket endpoint for media streaming
        @self.app.websocket("/api/media-streaming")
        async def websocket_handler_alt():
            from quart import websocket
            self.logger.info("🎯 WebSocket connection attempt detected on /api/media-streaming")
            self.logger.info(f"WebSocket headers: {dict(websocket.headers) if hasattr(websocket, 'headers') else 'No headers'}")
            return await self.handle_websocket_media_streaming(websocket)

        # Test endpoint for Voice Live call simulation
        self.app.route("/api/testVoiceLiveCall", methods=["POST"])(
            self.test_voice_live_call_simulation
        )


        

    async def hello(self):
        """Health check endpoint"""
        self.logger.info("async def hello")
        return "Hello ACS Call Automation Service with Azure AI Voice Live V1.0"

    async def health_check(self):
        """Health check endpoint for Azure App Service"""
        self.logger.info("health_check")
        return Response(
            response="Healthy", status=200, headers={"Content-Type": "text/plain"}
        )
    ## Add incoming_call_handler ##

    async def incoming_call_handler(self):
        """Handle incoming calls"""
        self.logger.info("incoming_call_handler")
        try:
            # Get the raw request data as JSON
            request_data = await request.get_json()
            self.logger.info(
                f"Received incoming call request: {json.dumps(request_data)}"
            )

            # If request_data is not a list, wrap it in a list
            if not isinstance(request_data, list):
                request_data = [request_data]

            for event_dict in request_data:
                self.logger.info(f"Processing event: {json.dumps(event_dict)}")

                # Handle EventGrid subscription validation directly
                event_type = event_dict.get("eventType", "")

                if event_type == "Microsoft.EventGrid.SubscriptionValidationEvent":
                    self.logger.info("Handling EventGrid validation event")
                    validation_code = event_dict.get("data", {}).get("validationCode")
                    if validation_code:
                        self.logger.info(f"Validation code: {validation_code}")
                        return Response(
                            response=json.dumps(
                                {"validationResponse": validation_code}
                            ),
                            status=StatusCodes.OK,
                            headers={"Content-Type": "application/json"},
                        )

                # Handle incoming call events
                elif event_type == "Microsoft.Communication.IncomingCall":
                    self.logger.info("Handling incoming call event")
                    try:
                        # Create EventGridEvent for incoming call processing
                        event = EventGridEvent.from_dict(event_dict)
                        await self._process_incoming_call(event)
                        return Response(status=StatusCodes.OK)
                    except Exception as e:
                        self.logger.error(f"Error processing incoming call: {str(e)}", exc_info=True)
                        return Response(status=StatusCodes.OK)  # Return OK to avoid EventGrid retries

                else:
                    self.logger.info(f"Unhandled event type: {event_type}")
                    return Response(status=StatusCodes.OK)

            return Response(status=StatusCodes.OK)

        except Exception as e:
            self.logger.error(
                f"Error in incoming call handler: {str(e)}", exc_info=True
            )
            return Response(
                response=json.dumps(
                    {"error": "Internal server error", "details": str(e)}
                ),
                status=StatusCodes.SERVER_ERROR,
                headers={"Content-Type": "application/json"},
            )

    ## Add outgoing_call_handler ##
    def _validate_payload(self, payload_dict: dict) -> None:
        """
        Validate the payload dictionary of the POST request.
        """
        pass
    

    async def initiate_outbound_call(self):
        """Initiate an outbound call"""
        self.logger.info("initiate_outbound_call")
        try:
            # extract the payload
            payload_dict = await request.get_json()
            # validate against expected payload
            # self._validate_payload(payload_dict=payload_dict)
            self.logger.info(f"Received payload: {json.dumps(payload_dict)}")
            
            self.config.TARGET_CANDIDATE_PHONE_NUMBER = payload_dict.get("phone_number")

            # Get the target participant and source caller            
            target_participant = PhoneNumberIdentifier(self.config.TARGET_CANDIDATE_PHONE_NUMBER)
            source_caller = PhoneNumberIdentifier(self.config.AGENT_PHONE_NUMBER)
            
            # Generate a callback URI with a unique context ID
            guid = uuid.uuid4()
            query_parameters = urlencode({"calleeId": self.config.TARGET_CANDIDATE_PHONE_NUMBER})
            callback_uri = f"{self.config.CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

            call_connection_properties = self.call_automation_client.create_call(
                target_participant=target_participant,
                source_caller_id_number=source_caller,
                # call_invite=call_invite,
                callback_url=callback_uri,
                cognitive_services_endpoint=self.config.COGNITIVE_SERVICE_ENDPOINT
            )

            # Obtain the call_connection_id
            call_connection_id = call_connection_properties.call_connection_id
            
            self.logger.info(f"Outbound call initiated with connection ID: {call_connection_id}")

            # Store data using call_connection_id as the namespace
            await self.cache_service.set(f"payload_dict:{call_connection_id}", payload_dict)
            await self.cache_service.set(f"participant_id:{call_connection_id}", self.config.TARGET_CANDIDATE_PHONE_NUMBER)
            
            # Simulate an Event Grid event for the outbound call
            #event = EventGridEvent(
            #    subject="OutboundCall",
            #    event_type=EventTypes.CALL_CONNECTED,
            #    data={
            #        "callConnectionId": call_connection_properties.call_connection_id,
            #        "to": {"rawId": self.config.TARGET_CANDIDATE_PHONE_NUMBER},
            #        "outboundCallContext": None,  # Not needed for outbound calls
            #    },
            #    data_version="1.0"
            #)
            await self._process_outbound_call(call_connection_id=call_connection_id)

            return Response(status=StatusCodes.OK)

        except Exception as e:
            self.logger.error(
                f"Error initiating outbound call: {str(e)}", exc_info=True
            )
            return Response(
                response=json.dumps(
                    {"error": "Error initiating outbound call", "details": str(e)}
                ),
                status=StatusCodes.SERVER_ERROR,
                headers={"Content-Type": "application/json"},
            )

    async def _process_outbound_call(self, call_connection_id: str):
        """Process outbound call connected event"""
        try:
            self.logger.info("_process_outbound_call event")

            # Extract call_connection_id from event data
            if not call_connection_id:
                self.logger.error("Error when processing outbound call: Missing callConnectionId")
                return  # Or handle appropriately

            callee_id = self.config.TARGET_CANDIDATE_PHONE_NUMBER

            # Create a new session in CosmosDB
            session_id = self.cosmosdb_service.create_new_session(callee_id, call_connection_id)
            self.logger.info(f"New session created with ID: {session_id} for call_connection_id: {call_connection_id}")

            # Store data in cache namespaced with call_connection_id
            await self.cache_service.set(f"participant_id:{call_connection_id}", callee_id)
            await self.cache_service.set(f"current_session_id:{call_connection_id}", session_id)
            await self.cache_service.set(f"current_call_id:{call_connection_id}", call_connection_id)

            # You might also want to set any other necessary data in the cache here

            # Start the conversation if needed
            # await self.event_handlers.handle_call_connected(event, callee_id)

        except Exception as e:
            self.logger.error(f"Error in _process_outbound_call: {str(e)}", exc_info=True)
            raise

    async def handle_eventgrid_validation(self):
        """Handle EventGrid webhook validation and incoming call events"""
        try:
            self.logger.info("Received EventGrid webhook request")

            # Get JSON data with minimal processing for speed
            events = await request.json

            # Process first event quickly for validation
            if events and len(events) > 0:
                first_event = events[0]
                event_type = first_event.get("eventType", "")

                # Handle EventGrid subscription validation IMMEDIATELY
                if event_type == "Microsoft.EventGrid.SubscriptionValidationEvent":
                    validation_code = first_event.get("data", {}).get("validationCode")
                    if validation_code:
                        self.logger.info(f"EventGrid validation successful: {validation_code}")
                        return Response(
                            response=json.dumps({"validationResponse": validation_code}),
                            status=200,
                            headers={"Content-Type": "application/json"},
                        )

                # Handle incoming call events asynchronously
                elif event_type == "Microsoft.Communication.IncomingCall":
                    self.logger.info("Processing incoming call event from EventGrid")
                    # Process in background without blocking response
                    asyncio.create_task(self._process_incoming_call_async(first_event))
                    return Response(status=200)

            # Default response for other events
            return Response(status=200)

        except Exception as e:
            self.logger.error(f"Error in EventGrid handler: {str(e)}")
            # Return success even on error to avoid EventGrid retries
            return Response(status=200)

    async def handle_callback(self, context_id: str):
        """Handle callbacks from the call automation service"""
        try:
            self.logger.info(f"Received callback for context: {context_id}")
            events = await request.json
            self.logger.info(f"Callback events: {json.dumps(events)}")

            # caller_id = self._normalize_caller_id(request.args.get("callerId", ""))
            # callee_id = await self.cache_service.get("participant_id")
            # self.logger.info(f"Processing callback for caller: {caller_id}")

            for event_dict in events:
                event = CloudEvent.from_dict(event_dict)
                call_connection_id = event.data.get("callConnectionId")
                if not call_connection_id:
                    self.logger.error("Missing callConnectionId in event data")
                    continue  # Skip processing this event if no call_connection_id is found
                
                self.logger.info(f"[Call Connection ID: {call_connection_id}] Received callback for context: {context_id}")
                self.logger.info(f"[Call Connection ID: {call_connection_id}] Event data: {json.dumps(event_dict)}")

                # Retrieve callee_id or any other necessary data using call_connection_id
                callee_id = await self.cache_service.get(f"participant_id:{call_connection_id}")

           
                try:
                    await self._process_event(event, callee_id)
                except Exception as e:
                    self.logger.error(
                        f"Error processing event type {event.type}: {str(e)}",
                        exc_info=True,
                    )

            return Response(status=StatusCodes.OK)

        except Exception as e:
            self.logger.error(f"Error in callback handler: {str(e)}", exc_info=True)
            return Response(
                response={"error": "Internal server error", "details": str(e)},
                status=StatusCodes.SERVER_ERROR,
            )

    async def _process_event(self, event: CloudEvent, caller_id: str):
        """Process different types of events"""
        self.logger.info(f"Processing event type: {event.type}")
        event_handlers = {
            EventTypes.CALL_CONNECTED: self.event_handlers.handle_call_connected,
            EventTypes.RECOGNIZE_COMPLETED: self.event_handlers.handle_recognize_completed,
            EventTypes.PLAY_COMPLETED: self.event_handlers.handle_play_completed,
            EventTypes.RECOGNIZE_FAILED: self.event_handlers.handle_recognize_failed,
            EventTypes.CALL_DISCONNECTED: self.event_handlers.handle_call_disconnected,
            EventTypes.PARTICIPANTS_UPDATED: self.event_handlers.handle_participants_updated,
            EventTypes.MEDIA_STREAMING_STARTED: self.event_handlers.handle_media_streaming_started,
            EventTypes.MEDIA_STREAMING_STOPPED: self.event_handlers.handle_media_streaming_stopped,
        }

        handler = event_handlers.get(event.type)
        if handler:
            try:
                await handler(event, caller_id)
            except Exception as e:
                self.logger.error(
                    f"Error in event handler for {event.type}: {str(e)}", exc_info=True
                )
                raise
        else:
            # Handle MediaStreamingStopped event specifically
            if event.type == "Microsoft.Communication.MediaStreamingStopped":
                self.logger.info(f"Handling MediaStreamingStopped event for call {event.data.get('callConnectionId')}")
                await self.event_handlers.handle_media_streaming_stopped(event, "")
            else:
                self.logger.warning(f"No handler found for event type: {event.type}")

    async def _answer_call_async(self, incoming_call_context, callback_url):
        self.logger.info("_answer_call_async event")

        # Create WebSocket URI for media streaming
        # Convert HTTPS to WSS for WebSocket connection
        callback_host = self.config.CALLBACK_URI_HOST
        if callback_host.startswith("https://"):
            websocket_uri = callback_host.replace("https://", "wss://") + "/ws"
        else:
            websocket_uri = f"wss://{callback_host}/ws"
        self.logger.info(f"Setting up media streaming with WebSocket URI: {websocket_uri}")

        # Configure media streaming options for Voice Live integration
        media_streaming_options = MediaStreamingOptions(
            transport_url=websocket_uri,
            transport_type=MediaStreamingTransportType.WEBSOCKET,
            content_type=MediaStreamingContentType.AUDIO,
            audio_channel_type=MediaStreamingAudioChannelType.MIXED,
            start_media_streaming=True
        )

        # Answer call - run in thread pool to avoid blocking
        if media_streaming_options:
            self.logger.info("Answering call with Voice Live media streaming enabled")
        else:
            self.logger.info("Answering call WITHOUT media streaming - using direct Voice Live integration")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.call_automation_client.answer_call(
                incoming_call_context=incoming_call_context,
                cognitive_services_endpoint=self.config.COGNITIVE_SERVICE_ENDPOINT,
                callback_url=callback_url,
                media_streaming=media_streaming_options
            )
        )

    async def _process_incoming_call_async(self, event_dict: dict):
        """Process incoming call event asynchronously without blocking webhook response"""
        self.logger.info("_process_incoming_call_async event")

        try:
            caller_id = self._extract_caller_id(event_dict.get("data", {}))
            event_data = event_dict.get("data", {})
            server_call_id = event_data.get("serverCallId")

            self.logger.info(f"Processing call from: {caller_id}, Server Call ID: {server_call_id}")

            # Check if we've already processed this call
            if hasattr(self, '_processed_calls'):
                if server_call_id in self._processed_calls:
                    self.logger.info(f"Call {server_call_id} already processed, skipping")
                    return
            else:
                self._processed_calls = set()

            # Mark this call as being processed
            self._processed_calls.add(server_call_id)

            incoming_call_context = event_data.get("incomingCallContext")
            if not incoming_call_context:
                self.logger.error("Missing incomingCallContext in event data")
                return

            callback_uri = self._generate_callback_uri(caller_id)

            # Call _answer_call_async
            answer_call_result = await self._answer_call_async(
                incoming_call_context, callback_uri
            )

            # Log the successful call connection
            self.logger.info(
                f"Answered call for connection id: {answer_call_result.call_connection_id}"
            )

        except Exception as e:
            self.logger.error(
                f"Error in _process_incoming_call_async: {str(e)}", exc_info=True
            )

    async def _process_incoming_call(self, event: EventGridEvent):
        """Process incoming call event (legacy method)"""
        self.logger.info("_process_incoming_call event")

        try:
            caller_id = self._extract_caller_id(event.data)
            #session_id = self.cosmosdb_service.create_new_session(caller_id, event.data["callConnectionId"])

            incoming_call_context = event.data["incomingCallContext"]
            callback_uri = self._generate_callback_uri(caller_id)

            # Call _answer_call_async and remove await
            answer_call_result = await self._answer_call_async(
                incoming_call_context, callback_uri
            )

            # Log the successful call connection
            self.logger.info(
                f"Answered call for connection id: {answer_call_result.call_connection_id}"
            )

        except Exception as e:
            self.logger.error(
                f"Error in _process_incoming_call: {str(e)}", exc_info=True
            )
            raise

    async def _start_direct_voice_live_integration(self, call_connection_id: str):
        """Start direct Voice Live integration without WebSocket media streaming"""
        try:
            self.logger.info(f"🎯 Starting direct Voice Live integration for call {call_connection_id}")

            # Create a Voice Live session
            voice_live_session = await self.voice_live_service.create_voice_live_session(call_connection_id)

            if voice_live_session:
                self.logger.info(f"✅ Voice Live session created for call {call_connection_id}")

                # Send initial greeting using ACS text-to-speech
                await self._send_voice_live_greeting(call_connection_id)

            else:
                self.logger.error(f"❌ Failed to create Voice Live session for call {call_connection_id}")

        except Exception as e:
            self.logger.error(f"Error starting direct Voice Live integration: {str(e)}", exc_info=True)

    async def _send_voice_live_greeting(self, call_connection_id: str):
        """Send initial greeting using ACS text-to-speech"""
        try:
            self.logger.info(f"🎯 Sending Voice Live greeting for call {call_connection_id}")

            # Get the call connection
            call_connection = self.call_automation_client.get_call_connection(call_connection_id)

            # Create greeting message
            greeting_text = """Hello! I'm Emma, your health advisor specializing in lab and imaging services.
            I'm here to help you understand your test results, schedule appointments, and answer any health-related questions you may have.
            How can I help you today?"""

            # Use ACS text-to-speech to play the greeting
            play_source = TextSource(
                text=greeting_text,
                voice_name="en-US-Emma2:DragonHDLatestNeural"
            )

            # Play the greeting
            await call_connection.play_media_to_all(play_source)

            self.logger.info(f"✅ Voice Live greeting sent for call {call_connection_id}")

        except Exception as e:
            self.logger.error(f"Error sending Voice Live greeting: {str(e)}", exc_info=True)

    def _extract_caller_id(self, event_data: dict) -> str:
        """Extract caller ID from event data"""
        if event_data["from"]["kind"] == "phoneNumber":
            return event_data["from"]["phoneNumber"]["value"]
        return event_data["from"]["rawId"]

    def _generate_callback_uri(self, caller_id: str) -> str:
        """Generate callback URI for the call"""
        guid = uuid.uuid4()
        query_parameters = urlencode({"callerId": caller_id})
        return f"{self.config.CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

    def _normalize_caller_id(self, caller_id: str) -> str:
        """Normalize caller ID format"""
        caller_id = caller_id.strip()
        if "+" not in caller_id:
            caller_id = "+" + caller_id
        return caller_id

    async def test_incoming_call_handler(self):
        """Test incoming call handler - Alternative solution"""
        self.logger.info("Test incoming call handler called")
        try:
            request_data = await request.get_json()
            phone_number = request_data.get("phoneNumber", "+1234567890")

            self.logger.info(f"Testing incoming call simulation from: {phone_number}")

            # Create a simulated incoming call event
            simulated_event = {
                "eventType": "Microsoft.Communication.IncomingCall",
                "data": {
                    "incomingCallContext": f"test-context-{phone_number}",
                    "from": {
                        "kind": "phoneNumber",
                        "phoneNumber": {"value": phone_number}
                    },
                    "to": {
                        "kind": "phoneNumber",
                        "phoneNumber": {"value": self.config.AGENT_PHONE_NUMBER}
                    }
                },
                "eventTime": "2025-07-22T16:00:00Z",
                "id": f"test-{phone_number}",
                "dataVersion": "1.0"
            }

            # Process the simulated event through the existing handler
            self.logger.info("Processing simulated incoming call event")

            # Extract caller ID
            caller_id = phone_number

            # Generate callback URI
            callback_uri = self._generate_callback_uri(caller_id)

            # Simulate answering the call
            self.logger.info(f"Simulated call answer for {caller_id} with callback {callback_uri}")

            return Response(
                response=json.dumps({
                    "status": "success",
                    "message": f"Simulated incoming call from {phone_number}",
                    "caller_id": caller_id,
                    "callback_uri": callback_uri,
                    "version": "V0.17-Alternative-Test"
                }),
                status=200,
                headers={"Content-Type": "application/json"}
            )

        except Exception as e:
            self.logger.error(f"Error in test incoming call handler: {str(e)}", exc_info=True)
            return Response(
                response=json.dumps({"error": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )

    async def handle_media_streaming(self, call_connection_id: str):
        """Handle media streaming events for Voice Live integration"""
        try:
            request_data = await request.get_json()
            self.logger.info(f"Received media streaming event for call {call_connection_id}: {json.dumps(request_data)}")

            # Forward to audio streaming service
            await self.audio_streaming_service.handle_media_streaming_event(call_connection_id, request_data)

            return Response(status=StatusCodes.OK)

        except Exception as e:
            self.logger.error(f"Error handling media streaming: {str(e)}", exc_info=True)
            return Response(
                response=json.dumps({"error": str(e)}),
                status=StatusCodes.SERVER_ERROR,
                headers={"Content-Type": "application/json"}
            )

    async def test_voice_live_connection(self):
        """Test Voice Live API connection"""
        try:
            # Test creating a Voice Live session
            test_call_id = "test-connection-" + str(uuid.uuid4())

            self.logger.info(f"Testing Voice Live connection with call ID: {test_call_id}")

            # Try to create a Voice Live session
            voice_live_connection = await self.voice_live_service.create_voice_live_session(test_call_id)

            if voice_live_connection:
                # Close the test session
                await self.voice_live_service.close_voice_live_session(test_call_id)

                return Response(
                    response=json.dumps({
                        "status": "success",
                        "message": "Voice Live API connection successful",
                        "endpoint": self.config.AZURE_VOICE_LIVE_ENDPOINT,
                        "deployment": self.config.AZURE_VOICE_LIVE_DEPLOYMENT,
                        "assistant_id": self.config.VIDA_VOICE_BOT_ASSISTANT_ID
                    }),
                    status=StatusCodes.OK,
                    headers={"Content-Type": "application/json"}
                )
            else:
                return Response(
                    response=json.dumps({
                        "status": "error",
                        "message": "Failed to create Voice Live session"
                    }),
                    status=StatusCodes.SERVER_ERROR,
                    headers={"Content-Type": "application/json"}
                )

        except Exception as e:
            self.logger.error(f"Error testing Voice Live connection: {str(e)}", exc_info=True)
            return Response(
                response=json.dumps({
                    "status": "error",
                    "message": f"Voice Live connection test failed: {str(e)}"
                }),
                status=StatusCodes.SERVER_ERROR,
                headers={"Content-Type": "application/json"}
            )

    async def test_voice_live_call_simulation(self):
        """Simulate a Voice Live call integration test"""
        try:
            request_data = await request.get_json()
            test_phone_number = request_data.get("phone_number", "+1234567890")
            client_name = request_data.get("client_name", "Test User")

            # Simulate a call connection ID
            test_call_id = f"test-call-{uuid.uuid4()}"

            self.logger.info(f"Simulating Voice Live call for {client_name} ({test_phone_number})")

            # Simulate the call connected flow
            await self.cache_service.set(f"call_active:{test_call_id}", True)
            await self.cache_service.set(f"current_session_id:{test_call_id}", test_call_id)
            await self.cache_service.set(f"current_call_id:{test_call_id}", test_call_id)
            await self.cache_service.set(f"participant_id:{test_call_id}", test_phone_number)
            await self.cache_service.set(f"payload_dict:{test_call_id}", {
                "client_name": client_name,
                "phone_number": test_phone_number,
                "test_mode": True
            })

            # Start Voice Live session (simulated)
            websocket_uri = f"wss://test-websocket-endpoint/{test_call_id}"

            streaming_started = await self.audio_streaming_service.start_bidirectional_streaming(
                test_call_id,
                websocket_uri
            )

            if streaming_started:
                # Configure Voice Live session
                await self.audio_streaming_service.configure_voice_live_session(
                    test_call_id,
                    assistant_id=None  # Will use default VIDA_VOICE_BOT_ASSISTANT_ID
                )

                # Simulate some conversation context
                hello_message = f"Hello {client_name}! This is a test of the Voice Live integration. How can I help you today?"

                await self.cache_service.set(f"conversation_context:{test_call_id}", {
                    "payload": {"client_name": client_name, "phone_number": test_phone_number},
                    "initial_greeting": hello_message,
                    "participant_id": test_phone_number,
                    "test_mode": True
                })

                # Clean up after a short delay (simulate call end)
                async def cleanup_test_call():
                    await asyncio.sleep(5)  # Wait 5 seconds
                    await self.audio_streaming_service.stop_bidirectional_streaming(test_call_id)
                    await self.cache_service.delete(f"call_active:{test_call_id}")
                    await self.cache_service.delete(f"current_session_id:{test_call_id}")
                    await self.cache_service.delete(f"current_call_id:{test_call_id}")
                    await self.cache_service.delete(f"conversation_context:{test_call_id}")
                    self.logger.info(f"Test call {test_call_id} cleaned up")

                # Start cleanup task
                asyncio.create_task(cleanup_test_call())

                return Response(
                    response=json.dumps({
                        "status": "success",
                        "message": "Voice Live call simulation successful",
                        "call_id": test_call_id,
                        "client_name": client_name,
                        "phone_number": test_phone_number,
                        "voice_live_session": "active",
                        "greeting": hello_message
                    }),
                    status=StatusCodes.OK,
                    headers={"Content-Type": "application/json"}
                )
            else:
                return Response(
                    response=json.dumps({
                        "status": "error",
                        "message": "Failed to start Voice Live session"
                    }),
                    status=StatusCodes.SERVER_ERROR,
                    headers={"Content-Type": "application/json"}
                )

        except Exception as e:
            self.logger.error(f"Error in Voice Live call simulation: {str(e)}", exc_info=True)
            return Response(
                response=json.dumps({
                    "status": "error",
                    "message": f"Voice Live call simulation failed: {str(e)}"
                }),
                status=StatusCodes.SERVER_ERROR,
                headers={"Content-Type": "application/json"}
            )

    async def handle_websocket_media_streaming(self, websocket):
        """Handle WebSocket media streaming from Azure Communication Services"""
        self.logger.info("🎯 ACS WebSocket connection established for media streaming!")
        self.logger.info(f"🎯 WebSocket connection from: {websocket.remote_address if hasattr(websocket, 'remote_address') else 'Unknown'}")

        # Extract call connection ID from headers
        call_connection_id = None
        correlation_id = None

        try:
            # Get headers from WebSocket connection - ACS sends specific headers
            headers = {}
            if hasattr(websocket, 'headers'):
                headers = dict(websocket.headers)
            elif hasattr(websocket, 'request_headers'):
                headers = dict(websocket.request_headers)

            # ACS sends headers with capital letters, try both cases
            call_connection_id = (headers.get('X-Ms-Call-Connection-Id') or
                                headers.get('x-ms-call-connection-id'))
            correlation_id = (headers.get('X-Ms-Call-Correlation-Id') or
                            headers.get('x-ms-call-correlation-id'))

            self.logger.info(f"ACS WebSocket connection - Call ID: {call_connection_id}, Correlation ID: {correlation_id}")
            self.logger.info(f"WebSocket headers: {headers}")

            # If no call connection ID from headers, use correlation ID or generate one
            if not call_connection_id:
                if correlation_id:
                    call_connection_id = correlation_id
                    self.logger.info(f"Using correlation ID as call connection ID: {call_connection_id}")
                else:
                    call_connection_id = "acs-media-stream"  # Fallback ID
                    self.logger.info(f"No ACS headers found, using fallback ID: {call_connection_id}")

            self.logger.info(f"Using call connection ID: {call_connection_id}")

            # Start Voice Live session for this call with WebSocket connection for bidirectional streaming
            voice_live_started = await self.audio_streaming_service.start_bidirectional_streaming(
                call_connection_id,
                f"{self.config.CALLBACK_URI_HOST}/ws",
                websocket_connection=websocket
            )

            if not voice_live_started:
                self.logger.error(f"Failed to start Voice Live session for call {call_connection_id}")
                await websocket.close(1000, "Failed to start Voice Live session")
                return

            self.logger.info(f"Voice Live session started for ACS call {call_connection_id}")

            # Handle incoming ACS media streaming data
            while True:
                try:
                    message = await websocket.receive()

                    if isinstance(message, str):
                        # Parse ACS audio streaming message
                        data = json.loads(message)
                        kind = data.get("kind")

                        if kind == "AudioMetadata":
                            self.logger.info(f"Received ACS audio metadata: {data}")
                            # Configure audio settings based on metadata
                            await self.audio_streaming_service.configure_audio_settings(
                                call_connection_id, data.get("audioMetadata", {})
                            )
                        elif kind == "AudioData":
                            # Forward audio data to Voice Live
                            audio_data = data.get("audioData", {})
                            await self.audio_streaming_service.process_incoming_audio(
                                call_connection_id, audio_data
                            )
                        else:
                            self.logger.debug(f"Received ACS message kind: {kind}")
                    else:
                        self.logger.warning(f"Received non-string message: {type(message)}")

                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse ACS WebSocket message: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing ACS WebSocket message: {e}")
                    break

        except Exception as e:
            self.logger.error(f"ACS WebSocket error: {e}")
        finally:
            # Clean up when WebSocket closes
            if call_connection_id:
                await self.audio_streaming_service.stop_bidirectional_streaming(call_connection_id)
                self.logger.info(f"Cleaned up Voice Live session for ACS call {call_connection_id}")

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the application using Hypercorn ASGI server"""
        import asyncio
        from hypercorn.config import Config
        from hypercorn.asyncio import serve

        config = Config()
        config.bind = [f"{host}:{port}"]
        config.use_reloader = False
        config.accesslog = "-"  # Log to stdout

        self.logger.info(f"Starting Hypercorn server on {host}:{port}")
        asyncio.run(serve(self.app, config))
