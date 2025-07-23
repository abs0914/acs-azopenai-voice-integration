#!/usr/bin/env python3
"""
Test startup script that bypasses environment variable checks
For testing purposes only
"""
import os
import sys

print("🧪 Starting TEST mode - bypassing environment checks...")

# Set up the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set some minimal environment variables to prevent crashes
os.environ.setdefault("ACS_CONNECTION_STRING", "test")
os.environ.setdefault("COGNITIVE_SERVICE_ENDPOINT", "test")
os.environ.setdefault("AGENT_PHONE_NUMBER", "test")
os.environ.setdefault("AZURE_OPENAI_SERVICE_KEY", "test")
os.environ.setdefault("AZURE_OPENAI_SERVICE_ENDPOINT", "test")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT_MODEL_NAME", "test")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT_MODEL", "test")
os.environ.setdefault("AZURE_VOICE_LIVE_API_KEY", "test")
os.environ.setdefault("CALLBACK_URI_HOST", "test")
os.environ.setdefault("COSMOS_DB_DATABASE_NAME", "test")
os.environ.setdefault("COSMOS_DB_CONTAINER_NAME", "test")
os.environ.setdefault("COSMOS_DB_URL", "test")
os.environ.setdefault("COSMOS_DB_KEY", "test")
os.environ.setdefault("REDIS_URL", "test")
os.environ.setdefault("REDIS_PASSWORD", "test")

try:
    print("🔧 Attempting to start application with test environment...")
    
    # Try to import the application
    from src.core.app import CallAutomationApp
    
    print("✅ Application imported successfully")
    
    # Create application instance
    print("🏗️ Creating application instance...")
    app_instance = CallAutomationApp()
    
    print("✅ Application instance created successfully")
    
    # Get the Quart app instance
    app = app_instance.app
    
    print("✅ Quart app instance obtained")
    
    # Start the server
    port = int(os.getenv("PORT", "8000"))
    print(f"🌐 Starting server on port {port}...")
    
    app_instance.run(host="0.0.0.0", port=port)
    
except Exception as e:
    print(f"❌ Error in test startup: {str(e)}")
    import traceback
    print(f"📋 Traceback: {traceback.format_exc()}")
    
    print("🏥 Falling back to health check...")
    
    try:
        from health import app
        port = int(os.getenv("PORT", "8000"))
        print(f"🌐 Starting health check server on port {port}...")
        app.run(host="0.0.0.0", port=port)
    except Exception as he:
        print(f"❌ Health check also failed: {str(he)}")
        
        # Last resort - minimal server
        from quart import Quart, Response
        
        minimal_app = Quart(__name__)
        
        @minimal_app.route("/")
        async def hello():
            return "ACS Voice Integration - Test Mode with Errors"
        
        @minimal_app.route("/health")
        async def health():
            return Response("Healthy - Test Mode", status=200)
        
        @minimal_app.route("/error")
        async def error_info():
            return {
                "main_error": str(e),
                "health_error": str(he),
                "status": "test_mode_with_errors"
            }
        
        port = int(os.getenv("PORT", "8000"))
        print(f"🌐 Starting minimal test server on port {port}...")
        minimal_app.run(host="0.0.0.0", port=port)
