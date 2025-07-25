import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration management class"""
    # Azure Communication Services
    ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
    COGNITIVE_SERVICE_ENDPOINT = os.getenv("COGNITIVE_SERVICE_ENDPOINT")
    AGENT_PHONE_NUMBER = os.getenv("AGENT_PHONE_NUMBER")
    VOICE_NAME = os.getenv("VOICE_NAME")
    
    # Azure OpenAI
    AZURE_OPENAI_SERVICE_KEY = os.getenv("AZURE_OPENAI_SERVICE_KEY")
    AZURE_OPENAI_SERVICE_ENDPOINT = os.getenv("AZURE_OPENAI_SERVICE_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_MODEL_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_MODEL_NAME")
    AZURE_OPENAI_DEPLOYMENT_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_MODEL")
    OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

    # Azure AI Voice Live API
    AZURE_VOICE_LIVE_ENDPOINT = os.getenv("AZURE_VOICE_LIVE_ENDPOINT", "https://vida-voice-live.cognitiveservices.azure.com/")
    AZURE_VOICE_LIVE_API_KEY = os.getenv("AZURE_VOICE_LIVE_API_KEY")
    AZURE_VOICE_LIVE_DEPLOYMENT = os.getenv("AZURE_VOICE_LIVE_DEPLOYMENT", "gpt-4o-realtime-preview")
    AZURE_VOICE_LIVE_REGION = os.getenv("AZURE_VOICE_LIVE_REGION", "eastus2")
    VIDA_VOICE_BOT_ASSISTANT_ID = os.getenv("VIDA_VOICE_BOT_ASSISTANT_ID", "asst_dEODj1Hu6Z68Ebggl13DAHPv")
    
    # Application Settings
    CALLBACK_URI_HOST = os.getenv("CALLBACK_URI_HOST")
    CALLBACK_EVENTS_URI = f"{CALLBACK_URI_HOST}/api/callbacks"
    END_SILENCE_TIMEOUT = float(os.getenv("END_SILENCE_TIMEOUT", "0.5"))

    # CosmosDB
    COSMOS_DB_DATABASE_NAME= os.getenv("COSMOS_DB_DATABASE_NAME")
    COSMOS_DB_CONTAINER_NAME= os.getenv("COSMOS_DB_CONTAINER_NAME")
    COSMOS_DB_URL= os.getenv("COSMOS_DB_URL")
    COSMOS_DB_KEY= os.getenv("COSMOS_DB_KEY")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


    TARGET_CANDIDATE_PHONE_NUMBER = os.getenv("TARGET_PHONE_NUMBER") 
    AGENT_PHONE_NUMBER = os.getenv("AGENT_PHONE_NUMBER")           
    
