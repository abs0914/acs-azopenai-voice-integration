from typing import List, Dict, Any, Optional
from openai import AsyncAzureOpenAI
import json
import asyncio
from ..config.settings import Config
from ..config.constants import OpenAIPrompts
from ..utils.helpers import AgentPersonaType
from ..services.cache_service import CacheService

class OpenAIService:
    """Service for handling OpenAI API interactions"""
    def __init__(self, config: Config, cache_service: CacheService):
        self.config = config
        self.cache_service = cache_service
        self.client = AsyncAzureOpenAI(
            api_key=config.AZURE_OPENAI_SERVICE_KEY,
            api_version="2024-08-01-preview",
            azure_endpoint=config.AZURE_OPENAI_SERVICE_ENDPOINT
        )
        # self.chat_history: List[Dict[str, Any]] = []
        self.system_message_dict = OpenAIPrompts.system_message_dict
        # self._initialize_chat_history()
        

    async def _initialize_chat_history(
        self, 
        call_connection_id: str,
        system_prompt_str: str = "You are a helpful AI assistant.",
    ) -> None:
        """Initialize chat history with system message defined by the agent persona of choice"""
        chat_history = [{
            "role": "system",
            "content": system_prompt_str
        }]
        await self.cache_service.set(f"chat_history:{call_connection_id}", chat_history)

    async def update_agent_persona(
        self, 
        call_connection_id: str,
        agent_persona: AgentPersonaType = "DEFAULT",
        assistant_message_to_include: Optional[str] = None,
        user_message_to_include: Optional[str] = None
    ) -> None:
        """Update the agent persona for the conversation
        Args:
            assistant_message_to_include: Optional assistant message to include in the chat history
            user_message_to_include: Optional user message to include in the chat history
        """
        # self.chat_history.clear()
        agent = agent_persona.value
        await self._initialize_chat_history(call_connection_id, self.system_message_dict[agent])
        
        # Retrieve chat history
        chat_history = await self.cache_service.get(f"chat_history:{call_connection_id}")

        if chat_history is None:
            chat_history = []
        
        if user_message_to_include:
            chat_history.append({
                "role": "user",
                "content": user_message_to_include
            })

        if assistant_message_to_include:
            chat_history.append({
                "role": "assistant",
                "content": assistant_message_to_include
            })
            
         # Save the updated chat history back to the cache
        await self.cache_service.set(f"chat_history:{call_connection_id}", chat_history)
    
    async def get_chat_completion(
        self,
        call_connection_id: str,
        user_prompt: str,
        max_length: int = 200
    ) -> str:
        """
        Get chat completion from Azure OpenAI Assistant
        Args:
            user_prompt: User's input text
            max_length: Maximum length of the response
        """
        try:
            # Use Assistant API if OPENAI_ASSISTANT_ID is configured
            if self.config.OPENAI_ASSISTANT_ID:
                return await self._get_assistant_response(call_connection_id, user_prompt, max_length)
            else:
                # Fallback to Chat Completions API
                return await self._get_chat_completion_fallback(call_connection_id, user_prompt, max_length)

        except Exception as ex:
            print(f"Error in OpenAI API call: {ex}")
            return ""

    async def _get_assistant_response(
        self,
        call_connection_id: str,
        user_prompt: str,
        max_length: int = 200
    ) -> str:
        """Get response using OpenAI Assistant API"""
        try:
            # Get or create thread for this call
            thread_id = await self.cache_service.get(f"thread_id:{call_connection_id}")

            if not thread_id:
                # Create new thread
                thread = await self.client.beta.threads.create()
                thread_id = thread.id
                await self.cache_service.set(f"thread_id:{call_connection_id}", thread_id)

            # Add user message to thread
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=f"In less than {max_length} characters and being succinct: {user_prompt}"
            )

            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.config.OPENAI_ASSISTANT_ID
            )

            # Wait for completion
            while run.status in ['queued', 'in_progress']:
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

            if run.status == 'completed':
                # Get the latest message
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread_id,
                    limit=1
                )

                if messages.data:
                    response_content = messages.data[0].content[0].text.value
                    return response_content

            return "I apologize, but I'm having trouble processing your request right now."

        except Exception as ex:
            print(f"Error in Assistant API call: {ex}")
            return "I apologize, but I'm having trouble processing your request right now."

    async def _get_chat_completion_fallback(
        self,
        call_connection_id: str,
        user_prompt: str,
        max_length: int = 200
    ) -> str:
        """Fallback to Chat Completions API"""
        try:
            # Retrieve chat history
            chat_history = await self.cache_service.get(f"chat_history:{call_connection_id}")

            if chat_history is None:
                # Initialize chat history if it doesn't exist
                await self._initialize_chat_history(call_connection_id)
                chat_history = await self.cache_service.get(f"chat_history:{call_connection_id}")

            # Add user message to history
            chat_history.append({
                "role": "user",
                "content": f"In less than {max_length} characters and being succint: {user_prompt}"
            })

            response = await self.client.chat.completions.create(
                model=self.config.AZURE_OPENAI_DEPLOYMENT_MODEL_NAME,
                messages=chat_history,
                max_tokens=1000
            )

            response_content = response.choices[0].message.content

            # Add assistant's response to history
            chat_history.append({
                "role": "assistant",
                "content": response_content
            })

            # Save updated chat history
            await self.cache_service.set(f"chat_history:{call_connection_id}", chat_history)

            return response_content

        except Exception as ex:
            print(f"Error in Chat Completions API call: {ex}")
            return ""


    