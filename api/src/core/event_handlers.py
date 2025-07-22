# src/core/event_handlers.py
from azure.core.messaging import CloudEvent
from typing import Dict, Any, Callable, Optional
import json
from ..config.constants import EventTypes, ConversationPrompts
from ..services.call_handler import CallHandler
from ..services.cache_service import CacheService
from ..services.openai_service import OpenAIService
from ..services.cosmosdb_service import CosmosDBService
from ..services.voice_live_service import VoiceLiveService
from ..services.audio_streaming_service import AudioStreamingService
from ..utils.helpers import AgentPersonaType
from ..utils.logger import setup_logger


class EventHandlers:
    """Handles different types of call automation events with Voice Live integration"""
    def __init__(self,
                 call_handler: CallHandler,
                 cache_service: CacheService,
                 openai_service: OpenAIService,
                 cosmosdb_service: CosmosDBService,
                 voice_live_service: VoiceLiveService,
                 audio_streaming_service: AudioStreamingService):
        self.call_handler = call_handler
        self.cache_service = cache_service
        self.openai_service = openai_service
        self.cosmosdb_service = cosmosdb_service
        self.voice_live_service = voice_live_service
        self.audio_streaming_service = audio_streaming_service
        self.max_retry = 2
        self._setup_context_handlers()
        # Initialize logger
        self.logger = setup_logger(__name__)

    def _setup_context_handlers(self) -> None:
        """Initialize context handlers mapping"""
        self.context_handlers = {
            "doGreetingCall": self._handle_intro_call,
            "continueCall": self._handle_continue_call,
            "endCall": self._handle_goodbye_play_completed,
            
            
            #"doRecruitingCall": self._handle_recruiting_call,
            #"doInterviewCall": self._handle_recruiting_call,
            #"doClosureCall": self._handle_closure_call,
            #"InitialGreeting": self._handle_initial_greeting,
            #"ConsentRequest": self._handle_consent_request,
            #"LocationRequest": self._handle_location_request,
            #"CommuteQuestion": self._handle_commute_question,
            #"JobInterest": self._handle_job_interest,
            #"CompetencyResponse": self._handle_competency_response,
            #"NextStepsRequest": self._handle_next_steps_request
        }
        
        self.play_completed_handlers = {
            "endCall": self._handle_goodbye_play_completed,
            "GOODBYE_CONTEXT": self._handle_goodbye_play_completed,
            
            
            #"goalAchieved1": self._handle_goals_achieved_play_completed,
            #"goalAchieved2": self._handle_goals_achieved_play_completed,
            #"ConsentRequest": self._handle_consent_play_completed,
            #"LocationRequest": self._handle_location_play_completed,
            #"JobDetails": self._handle_job_details_play_completed
        }

    # async def handle_call_connected(self, event: CloudEvent, caller_id: str) -> None:
    #     """Handle call connected event"""
    #     await self.call_handler.handle_recognize(
    #         ConversationPrompts.HELLO,
    #         caller_id,
    #         event.data["callConnectionId"],
    #         context="InitialGreeting"
    #     )
    

    def json_parse_message(self, message: str, context: str) -> Dict[str, Any]:
        """Parse the message as JSON from OpenAI Chat Completion API to avoid non-json formating issues
        
        Args:
            message: Message to be parsed from openai
            context: Context of the message
        Returns:
            Dictionary containing the 'msg' and 'context' keys
         """
        try:
            # Try to load the message as JSON
            return json.loads(message)
        except json.JSONDecodeError:
            # If it fails, reformat the message into a JSON object
            return json.loads(json.dumps({"msg": message, "context": context}))



    async def handle_call_connected(self, event: CloudEvent, phone_number: str) -> None:
        """
        Handle call connected event with Voice Live integration
        Args:
            event: CloudEvent containing call data
            phone_number: Caller or Target's phone number depending on whether it's an incoming or outgoing call
        """
        try:
            call_connection_id = event.data.get("callConnectionId")
            if not call_connection_id:
                self.logger.error("Missing callConnectionId in CallConnected event")
                return

            # Initialize the conversation state
            await self.cache_service.set(f"call_active:{call_connection_id}", True)
            await self.cache_service.set(f"current_session_id:{call_connection_id}", call_connection_id)
            await self.cache_service.set(f"current_call_id:{call_connection_id}", call_connection_id)

            participant_id = await self.cache_service.get(f"participant_id:{call_connection_id}")
            payload_dict = await self.cache_service.get(f"payload_dict:{call_connection_id}")

            if participant_id:
                # Start bidirectional audio streaming with Voice Live API
                websocket_uri = f"wss://your-websocket-endpoint/{call_connection_id}"  # This should be your WebSocket endpoint

                streaming_started = await self.audio_streaming_service.start_bidirectional_streaming(
                    call_connection_id,
                    websocket_uri
                )

                if streaming_started:
                    # Configure Voice Live session with vida-voice-bot agent
                    await self.audio_streaming_service.configure_voice_live_session(
                        call_connection_id,
                        assistant_id=None  # Will use default VIDA_VOICE_BOT_ASSISTANT_ID from config
                    )

                    # Send initial greeting through Voice Live API
                    hello_message = f"Hello {payload_dict.get('client_name', '')}! {ConversationPrompts.HELLO}. Is this a good time to speak?"

                    # Store conversation context
                    await self.cache_service.set(f"conversation_context:{call_connection_id}", {
                        "payload": payload_dict,
                        "initial_greeting": hello_message,
                        "participant_id": participant_id
                    })

                    self.logger.info(f"Voice Live session started for call {call_connection_id}")
                else:
                    self.logger.error(f"Failed to start Voice Live streaming for call {call_connection_id}")
                    # Fallback to traditional approach if Voice Live fails
                    await self._fallback_to_traditional_approach(call_connection_id, participant_id, payload_dict)
            else:
                self.logger.info("Participant ID not available yet. Waiting for ParticipantsUpdated event.")

        except Exception as e:
            self.logger.error(f"Error in handle_call_connected: {str(e)}", exc_info=True)
            if call_connection_id:
                await self.call_handler.hangup(call_connection_id)

    async def _fallback_to_traditional_approach(self, call_connection_id: str, participant_id: str, payload_dict: dict):
        """Fallback to traditional STT/TTS approach if Voice Live fails"""
        try:
            hello_message = f"Hello {payload_dict.get('client_name', '')}! {ConversationPrompts.HELLO}. Is this a good time to speak?"
            await self.call_handler.handle_recognize(
                hello_message,
                participant_id,
                call_connection_id,
                context="doGreetingCall"
            )
            await self.openai_service.update_agent_persona(
                agent_persona=AgentPersonaType.DEFAULT,
                call_connection_id=call_connection_id,
                user_message_to_include=f"This is information about my request for you to use during our call: {payload_dict}\nNow start the conversation based on this.",
                assistant_message_to_include=json.dumps({
                    "msg": hello_message,
                    "context": "doGreetingCall"
                })
            )
            self.logger.info(f"Fallback to traditional approach for call {call_connection_id}")
        except Exception as e:
            self.logger.error(f"Error in fallback approach: {e}")

    async def handle_participants_updated(self, event: CloudEvent, caller_id: str) -> None:
        """Handle participants updated event"""
        try:
            call_connection_id = event.data.get("callConnectionId")
            if not call_connection_id:
                self.logger.error("Missing callConnectionId in event data")
                return  # Handle the missing call_connection_id appropriately

            participants = event.data.get("participants", [])
            participant_id_found = False

            for participant in participants:
                identifier = participant.get('identifier', {})
                kind = identifier.get('kind', 'unknown')

                self.logger.debug(f"Processing participant identifier: {identifier}")

                if kind == 'phoneNumber':
                    phone_number = identifier.get('phoneNumber')
                    self.logger.debug(f"Participant phone number: {phone_number}")
                    if phone_number == caller_id:
                        participant_id = phone_number
                        await self.cache_service.set(f"participant_id:{call_connection_id}", participant_id)
                        participant_id_found = True
                        self.logger.info(f"Set participant_id for call {call_connection_id}: {participant_id}")
                        break  # Exit loop if participant is found
                elif kind == 'communicationUser':
                    communication_user_id = identifier.get('communicationUserId')
                    # Handle communication user if needed
                    self.logger.debug(f"Participant communicationUserId: {communication_user_id}")
                else:
                    self.logger.warning(f"Unknown participant kind: {kind}")

            if not participant_id_found:
                self.logger.warning(f"Participant matching caller_id {caller_id} not found in participants")

            # Log participants update
            self.logger.info(f"Participants updated for call {call_connection_id}")
            self.logger.info(f"Current participants: {participants}")

            # Store participants in cache (ensure serialization if necessary)
            await self.cache_service.set(f"current_participants:{call_connection_id}", participants)

        except Exception as e:
            self.logger.error(f"Error in handle_participants_updated: {str(e)}", exc_info=True)

    async def handle_media_streaming_event(self, event: CloudEvent, caller_id: str) -> None:
        """Handle media streaming events for Voice Live integration"""
        try:
            call_connection_id = event.data.get("callConnectionId")
            if not call_connection_id:
                self.logger.error("Missing callConnectionId in media streaming event")
                return

            # Forward the event to the audio streaming service
            await self.audio_streaming_service.handle_media_streaming_event(call_connection_id, event.data)

        except Exception as e:
            self.logger.error(f"Error handling media streaming event: {e}")

    async def handle_call_disconnected(self, event: CloudEvent, caller_id: str) -> None:
        """Handle call disconnected event and cleanup Voice Live resources"""
        try:
            call_connection_id = event.data.get("callConnectionId")
            if not call_connection_id:
                self.logger.error("Missing callConnectionId in call disconnected event")
                return

            # Stop Voice Live streaming
            if self.audio_streaming_service.is_streaming_active(call_connection_id):
                await self.audio_streaming_service.stop_bidirectional_streaming(call_connection_id)

            # Clean up cache
            await self.cache_service.delete(f"call_active:{call_connection_id}")
            await self.cache_service.delete(f"current_session_id:{call_connection_id}")
            await self.cache_service.delete(f"current_call_id:{call_connection_id}")
            await self.cache_service.delete(f"conversation_context:{call_connection_id}")

            self.logger.info(f"Cleaned up resources for disconnected call {call_connection_id}")

        except Exception as e:
            self.logger.error(f"Error handling call disconnected: {e}")

    async def handle_recognize_completed(self, event: CloudEvent, caller_id: str) -> None:
        """Handle recognize completed event"""
        call_connection_id = event.data.get("callConnectionId")
        if not call_connection_id:
            self.logger.error("Missing callConnectionId in event data")
            return  # Or handle appropriately
        if event.data["recognitionType"] == "speech":
            # Log user message to CosmosDB
            speech_result = event.data.get("speechResult", {})
            speech_text = speech_result.get("speech")
            session_id = await self.cache_service.get(f"current_session_id:{call_connection_id}")
            if session_id and speech_text:
                self.cosmosdb_service.append_message_to_session(
                    session_id, caller_id, "user", speech_text
                )
            await self._handle_speech_recognition(event, caller_id)
        elif event.data["recognitionType"] == "dxtmf":
            await self._handle_dtmf_recognition(event, caller_id)

    async def _handle_speech_recognition(self, event: CloudEvent, caller_id: str) -> None:
        """Handle speech recognition completion"""
        speech_text = event.data["speechResult"]["speech"]
        context = event.data["operationContext"]
        call_connection_id = event.data["callConnectionId"]

        handler = self.context_handlers.get(context)
        if handler:
            await handler(
                speech_text=speech_text, 
                caller_id=caller_id, 
                call_connection_id=call_connection_id
            )
        else:
            print(f"No handler found for context: {context}")

    # Handles the call with the intro persona until the goals are achieved
    async def _handle_intro_call(
        self,
        speech_text: str,
        caller_id: str,
        call_connection_id: str
    ) -> None:
        """Handle the interview with INTRO agent persona"""
        # asummes that intro persona is used already active
        # first generates openai message
        try:
            message = await self.openai_service.get_chat_completion(
                call_connection_id=call_connection_id,
                user_prompt=speech_text
            )
            
            self.logger.info(f"OpenAI message: {message}")
            
            message = self.json_parse_message(message, "continueCall")
        except Exception as e:
            self.logger.error(f"Error in get_chat_completion: {str(e)}", exc_info=True)
            message = {
                "msg": "I'm sorry but I'm having some trouble with my system... Could you repeat that?",
                "context": "continueCall"
            }
        intro_message="""Hello! My name is Kira, an AI travel agent at Contoso Travel. I'm calling because you requested more information about a trip on our website. Is this a good time to speak?"""
        
        # second it sends the message to ACS to be played (and wait for an answer if message['intent] is not goalAchieved1)
        try:
            await self.call_handler.handle_communicate(
                reply_text=message.get("msg", intro_message),
                caller_id=caller_id,
                call_connection_id=call_connection_id,
                context=message.get("intent", "continueCall")
            )
        except Exception as e:
            self.logger.error(f"Error in handle_communicate: {str(e)}", exc_info=True)
            
            
    # Handles the call after  greeting until the goals are achieved
    async def _handle_continue_call(
        self,
        speech_text: str,
        caller_id: str,
        call_connection_id: str
    ) -> None:
        """Handle the call conversation after greeting and till goals are achieved"""
        # asummes that intro persona is used already active
        # first generates openai message
        try:
            message = await self.openai_service.get_chat_completion(
                call_connection_id=call_connection_id,
                user_prompt=speech_text
            )
            
            self.logger.info(f"OpenAI message: {message}")
            
            message = self.json_parse_message(message, "doGreetingCall")
        except Exception as e:
            self.logger.error(f"Error in get_chat_completion: {str(e)}", exc_info=True)
            message = {
                "msg": "I'm sorry but I'm having some trouble with my system... Could you repeat that?",
                "context": "doGreetingCall"
            }
        # second it sends the message to ACS to be played (and wait for an answer if message['intent] is not goalAchieved1)
        try:
            await self.call_handler.handle_communicate(
                reply_text=message.get("msg", "Sorry I had some trouble processing my answer, could you please repeat?"),
                caller_id=caller_id,
                call_connection_id=call_connection_id,
                context=message.get("intent", "continueCall")
            )
        except Exception as e:
            self.logger.error(f"Error in handle_communicate: {str(e)}", exc_info=True)
            

    
    # Handles the call with the recruiting persona until the goals are achieved
    async def _handle_recruiting_call(
        self,
        speech_text: str,
        caller_id: str,
        call_connection_id: str
    ) -> None:
        # first generates openai message
        try:
            message = await self.openai_service.get_chat_completion(
                call_connection_id=call_connection_id,
                user_prompt=speech_text
            )
            
            message = self.json_parse_message(message, "doRecruitingCall")
        except Exception as e:
            self.logger.error(f"Error in get_chat_completion: {str(e)}", exc_info=True)
            message = {
                "msg": "I'm sorry but I'm having some trouble with my system... Could you repeat that?",
                "context": "doRecruitingCall"
            }
        # second it sends the message to ACS to be played (and wait for an answer if message['intent] is not goalAchieved1)
        try:
            await self.call_handler.handle_communicate(
                reply_text=message.get("msg", "The format of the response is incorrect"),
                caller_id=caller_id,
                call_connection_id=call_connection_id,
                context=message.get("intent", "doRecruitingCall")
            )
        except Exception as e:
            self.logger.error(f"Error in handle_communicate: {str(e)}", exc_info=True)
            
    # Handles the call with the closure persona until the goals are achieved
    async def _handle_closure_call(
        self,
        speech_text: str,
        caller_id: str,
        call_connection_id: str
    ) -> None:
        # first generates openai message
        try:
            message = await self.openai_service.get_chat_completion(
                call_connection_id=call_connection_id,
                user_prompt=speech_text
            )
            
            message = self.json_parse_message(message, "doClosureCall")
        except Exception as e:
            self.logger.error(f"Error in get_chat_completion: {str(e)}", exc_info=True)
            message = {
                "msg": "I'm sorry but I'm having some trouble with my system... Could you repeat that?",
                "context": "doClosureCall"
            }
        # second it sends the message to ACS to be played (and wait for an answer if message['intent] is not goalAchieved1)
        try:
            await self.call_handler.handle_communicate(
                reply_text=message.get("msg", "The format of the response is incorrect"),
                caller_id=caller_id,
                call_connection_id=call_connection_id,
                context=message.get("intent", "doClosureCall")
            )
        except Exception as e:
            self.logger.error(f"Error in handle_communicate: {str(e)}", exc_info=True)

    
    async def _handle_initial_greeting(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle initial greeting response"""
        if any(keyword in speech_text.lower() for keyword in ["no", "not interested", "busy"]):
            await self.call_handler.handle_play(
                call_connection_id,
                "No problem, I understand. Have a good day!",
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)
        else:
            consent_message = await self.cache_service.get("consent_message")
            await self.call_handler.handle_recognize(
                consent_message,
                caller_id,
                call_connection_id,
                context="ConsentRequest"
            )

    async def _handle_consent_request(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle consent request response"""
        if "no" in speech_text.lower():
            await self.call_handler.handle_play(
                call_connection_id,
                "I understand. Thank you for your time. Have a great day!",
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)
        else:
            location_question = await self.cache_service.get("location_question")
            await self.call_handler.handle_recognize(
                location_question,
                caller_id,
                call_connection_id,
                context="LocationRequest"
            )

    async def _handle_location_request(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle location request response"""
        # Store the location in cache
        await self.cache_service.set("candidate_location", speech_text)
        
        # Get job location and details
        job_location = await self.cache_service.get("job_location")
        job_details = await self.cache_service.get("job_details")
        
        # In a real implementation, you would validate the location here
        # For now, just proceed with job details
        await self.call_handler.handle_play(
            call_connection_id,
            f"The role is based in {job_location}. {job_details}",
            context="JobDetails"
        )

    async def _handle_commute_question(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle commute question response"""
        if any(keyword in speech_text.lower() for keyword in ["yes", "okay", "fine", "sure"]):
            job_details = await self.cache_service.get("job_details")
            await self.call_handler.handle_play(
                call_connection_id,
                f"Great! {job_details}",
                context="JobDetails"
            )
        else:
            await self.call_handler.handle_play(
                call_connection_id,
                "I understand. Thank you for your time. Have a great day!",
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)

    async def _handle_job_interest(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle job interest response"""
        if any(keyword in speech_text.lower() for keyword in ["no", "not interested"]):
            await self.call_handler.handle_play(
                call_connection_id,
                "I understand. Thank you for your time. Have a great day!",
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)
        else:
            # Get competency question from cache or generate one
            competency_question = await self.openai_service.get_chat_completion(
                "Generate a relevant competency question for an AI Vice President role"
            )
            await self.call_handler.handle_recognize(
                competency_question,
                caller_id,
                call_connection_id,
                context="CompetencyResponse"
            )

    async def _handle_competency_response(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle competency question response"""
        # Generate acknowledgment using OpenAI
        acknowledgment = await self.openai_service.get_chat_completion(
            f"Generate a positive acknowledgment for this experience: {speech_text}"
        )
        
        await self.call_handler.handle_play(
            call_connection_id,
            acknowledgment,
            context="Acknowledgement"
        )
        
        # Ask about next steps
        next_steps = "Based on your experience, I think you would be a great fit for this role. Would it be okay if I forwarded your CV to our client?"
        await self.call_handler.handle_recognize(
            next_steps,
            caller_id,
            call_connection_id,
            context="NextStepsRequest"
        )

    async def _handle_next_steps_request(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle next steps request response"""
        if any(keyword in speech_text.lower() for keyword in ["yes", "okay", "sure"]):
            await self.call_handler.handle_play(
                call_connection_id,
                ConversationPrompts.THANK_YOU,
                "GOODBYE_CONTEXT"
            )
        else:
            await self.call_handler.handle_play(
                call_connection_id,
                ConversationPrompts.GOODBYE,
                "GOODBYE_CONTEXT"
            )
        await self.call_handler.hangup(call_connection_id)

    async def handle_play_completed(self, event: CloudEvent, caller_id: str) -> None:
        """Handle play completed event"""
        context = event.data["operationContext"]
        call_connection_id = event.data["callConnectionId"]

        # Log the playback completion or message played
        session_id = await self.cache_service.get("current_session_id")
        if session_id:
            # You might store the message that was played in cache or retrieve it from the context
            # For this example, we'll log a generic message
            self.cosmosdb_service.append_message_to_session(
                session_id, caller_id, "application", f"Playback completed for context: {context}"
            )

        handler = self.play_completed_handlers.get(context)
        if handler:
            await handler(event, caller_id)
        elif context == "GOODBYE_CONTEXT":
            await self.call_handler.hangup(call_connection_id)

    async def _handle_consent_play_completed(
        self, 
        event: CloudEvent, 
        caller_id: str
    ) -> None:
        """Handle consent play completed"""
        location_question = await self.cache_service.get("location_question")
        await self.call_handler.handle_recognize(
            location_question,
            caller_id,
            event.data["callConnectionId"],
            context="LocationRequest"
        )

    async def _handle_location_play_completed(
        self, 
        event: CloudEvent, 
        caller_id: str
    ) -> None:
        """Handle location play completed"""
        job_details = await self.cache_service.get("job_details")
        await self.call_handler.handle_play(
            event.data["callConnectionId"],
            job_details,
            context="JobDetails"
        )

    async def _handle_job_details_play_completed(
        self, 
        event: CloudEvent, 
        caller_id: str
    ) -> None:
        """Handle job details play completed"""
        interest_question = await self.cache_service.get("user_interested")
        await self.call_handler.handle_recognize(
            interest_question,
            caller_id,
            event.data["callConnectionId"],
            context="JobInterest"
        )
    
    async def _handle_goals_achieved_play_completed(
        self,
        event: CloudEvent,
        caller_id: str
    ) -> None:
        """Handle goals achieved play completed"""
        # For goalAchieved1, initiate the interview persona
        
        # Extract call_connection_id from event data
        call_connection_id = event.data.get("callConnectionId")
        if not call_connection_id:
            self.logger.error("Missing callConnectionId in event data")
            return  # Or handle appropriately
        
        if event.data["operationContext"] == "goalAchieved1":
            message = {
                "msg": "Alright! Let's move on to the interview. Are you ready?",
                "intent": "doRecruitingCall"
            }
            
            # Retrieve job and candidate data from cache, namespaced with call_connection_id
            job_data_dict = await self.cache_service.get(f"job_data_dict:{call_connection_id}")
            candidate_data_dict = await self.cache_service.get(f"candidate_data_dict:{call_connection_id}")

            
            # initiate interview persona
            await self.openai_service.update_agent_persona(
                agent_persona=AgentPersonaType.INTERVIEW,
                call_connection_id=call_connection_id, 
                assistant_message_to_include=(
                    f"Are you ready for the interview? "
                    f"Job role details: {job_data_dict}\n"
                    f"Candidate details: {candidate_data_dict}"
                )
            )
            
            await self.call_handler.handle_communicate(
                reply_text=message.get("msg"),
                call_connection_id=call_connection_id,
                context=message.get("intent"),
                caller_id=caller_id
            )
            
        # For goalAchieved2, initiate the closure persona
        elif event.data["operationContext"] == "goalAchieved2":
            # generate interview summary
            try:
                # Retrieve candidate data from cache
                candidate_data_dict = await self.cache_service.get(f"candidate_data_dict:{call_connection_id}")
                if not candidate_data_dict:
                    self.logger.error(f"[Call Connection ID: {call_connection_id}] Missing candidate_data_dict in cache")
                    candidate_name = "Candidate"
                else:
                    candidate_name = candidate_data_dict.get('candidate_name', 'Candidate')

                # Prepare the user prompt
                user_prompt = f"""
                Give me a summary of the most important information I provided about my experience and fit for the role in 3 numbered bullet points. 
                Please structure your answer as:
                {{
                    "msg": "Okay {candidate_name}, let me share my notes. <the bullet points you generated>. Does that sound good?",
                    "intent": "doClosureCall"
                }}
                """
                
                # Get chat completion from OpenAI
                interview_summary = await self.openai_service.get_chat_completion(
                    call_connection_id=call_connection_id,
                    user_prompt=user_prompt.strip()
                )
                
                
                
                interview_summary_dict = json.loads(interview_summary)
                
                # initiate closure persona
                await self.openai_service.update_agent_persona(
                    agent_persona=AgentPersonaType.CLOSURE,
                    call_connection_id=call_connection_id,
                    assistant_message_to_include=interview_summary
                )
                
                await self.call_handler.handle_communicate(
                    reply_text=interview_summary_dict.get("msg", "The format of the response is incorrect"),
                    call_connection_id=call_connection_id,
                    context="doClosureCall",
                    caller_id=caller_id
                )     
            except Exception as e:
                self.logger.error(f"Error in get_chat_completion: {str(e)}", exc_info=True)
                   

    async def _handle_goodbye_play_completed(
        self,
        speech_text: Optional[str] = None,
        call_connection_id: Optional[str] = None, 
        event: Optional[CloudEvent] = None, 
        caller_id: Optional[str] = None,
        *args,
        **kwargs
    ) -> None:
        """Handle goodbye play completed"""
        if event is not None:
            await self.call_handler.hangup(event.data["callConnectionId"])
        elif call_connection_id is not None:
            await self.call_handler.hangup(call_connection_id)
        else:
            self.logger.error("No call connection ID provided")

    async def _handle_dtmf_recognition(
        self, 
        event: CloudEvent, 
        caller_id: str
    ) -> None:
        """Handle DTMF recognition"""
        # Implement DTMF handling if needed
        pass

    async def handle_recognize_failed(self, event: CloudEvent, caller_id: str) -> None:
        """Handle recognize failed event"""
        result_information = event.data["resultInformation"]
        reason_code = result_information["subCode"]
        context = event.data["operationContext"]
        call_connection_id = event.data["callConnectionId"]

        if reason_code == 8510 and self.max_retry > 0:
            await self.call_handler.handle_recognize(
                ConversationPrompts.TIMEOUT_SILENCE,
                caller_id,
                call_connection_id,
                context=context
            )
            self.max_retry -= 1
        else:
            await self.call_handler.handle_play(
                call_connection_id,
                ConversationPrompts.GOODBYE,
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)

    # async def handle_call_disconnected(self, event: CloudEvent, caller_id: str) -> None:
    #     """Handle call disconnected event"""
    #     print(f"Call disconnected for call connection id: {event.data['callConnectionId']}")
    #     await self.cache_service.clear()  # Clean up the cache for this session
    
    async def handle_call_disconnected(self, event: CloudEvent, caller_id: str) -> None:
        """Handle call disconnected event"""
        try:
            call_connection_id = event.data.get('callConnectionId')
            if not call_connection_id:
                self.logger.error("Missing callConnectionId in event data")
                return  # Handle appropriately or raise an exception

            print(f"Call disconnected for call connection id: {call_connection_id}")

            # Delete all cache entries for this call_connection_id
            pattern = f"*:{call_connection_id}"
            await self.cache_service.delete_by_pattern(pattern)

            self.logger.info(f"Cleared cache for call connection id: {call_connection_id}")

        except Exception as e:
            self.logger.error(f"Error in handle_call_disconnected: {str(e)}", exc_info=True)