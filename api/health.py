"""
Simple health check application that doesn't require full service initialization
"""
import os
from quart import Quart, Response
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a simple Quart app for health checks
app = Quart(__name__)

@app.route("/")
async def hello():
    """Basic hello endpoint"""
    return "Hello ACS Call Automation Service with Azure AI Voice Live V1.0"

@app.route("/health")
async def health_check():
    """Health check endpoint for Azure App Service"""
    return Response(
        response="Healthy", 
        status=200, 
        headers={"Content-Type": "text/plain"}
    )

@app.route("/robots933456.txt")
async def robots():
    """Alternative health check endpoint"""
    return Response(
        response="Healthy", 
        status=200, 
        headers={"Content-Type": "text/plain"}
    )

@app.route("/env-check")
async def env_check():
    """Check environment variables status"""
    required_vars = [
        "ACS_CONNECTION_STRING",
        "COGNITIVE_SERVICE_ENDPOINT", 
        "AGENT_PHONE_NUMBER",
        "AZURE_OPENAI_SERVICE_KEY",
        "AZURE_OPENAI_SERVICE_ENDPOINT",
        "AZURE_VOICE_LIVE_API_KEY",
        "CALLBACK_URI_HOST",
        "COSMOS_DB_DATABASE_NAME",
        "REDIS_URL"
    ]
    
    env_status = {}
    for var in required_vars:
        value = os.getenv(var)
        env_status[var] = "✅ Set" if value else "❌ Missing"
    
    return {
        "status": "Environment Variable Check",
        "variables": env_status,
        "all_set": all(os.getenv(var) for var in required_vars)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
