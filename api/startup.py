"""
Startup utilities for the ACS Voice Integration application
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_required_env_vars():
    """Check if all required environment variables are set"""
    
    # Critical environment variables for basic functionality
    required_vars = [
        "ACS_CONNECTION_STRING",
        "CALLBACK_URI_HOST",
    ]
    
    # Important but not critical (will use defaults or fallback)
    important_vars = [
        "AZURE_VOICE_LIVE_API_KEY",
        "AZURE_VOICE_LIVE_ENDPOINT",
        "REDIS_URL",
        "COSMOS_DB_URL",
        "AZURE_OPENAI_SERVICE_KEY"
    ]
    
    missing_critical = []
    missing_important = []
    
    print("🔍 Checking environment variables...")
    
    # Check critical variables
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_critical.append(var)
        else:
            print(f"✅ {var}: {'*' * min(len(value), 20)}...")
    
    # Check important variables
    for var in important_vars:
        value = os.getenv(var)
        if not value:
            missing_important.append(var)
        else:
            print(f"✅ {var}: {'*' * min(len(value), 20)}...")
    
    # Report missing variables
    if missing_critical:
        print(f"❌ Missing CRITICAL environment variables: {', '.join(missing_critical)}")
        print("💡 These are required for the application to function.")
        print("📝 Create a .env file in the api directory with these variables.")
        raise EnvironmentError(f"Missing critical environment variables: {missing_critical}")
    
    if missing_important:
        print(f"⚠️  Missing IMPORTANT environment variables: {', '.join(missing_important)}")
        print("💡 The application will run but some features may not work properly.")
    
    print("✅ Environment variable check completed")

def setup_logging():
    """Setup basic logging configuration"""
    import logging
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, 'app.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    print("✅ Logging configured")

def validate_azure_services():
    """Validate that Azure services are accessible (optional check)"""
    try:
        from azure.communication.callautomation import CallAutomationClient
        
        acs_connection_string = os.getenv("ACS_CONNECTION_STRING")
        if acs_connection_string:
            # Try to create client (doesn't make network call)
            client = CallAutomationClient.from_connection_string(acs_connection_string)
            print("✅ Azure Communication Services client initialized")
        else:
            print("⚠️  ACS_CONNECTION_STRING not set - skipping ACS validation")
            
    except Exception as e:
        print(f"⚠️  Azure services validation warning: {e}")
        # Don't fail startup for this

if __name__ == "__main__":
    """Run startup checks independently"""
    print("🚀 Running startup checks...")
    try:
        check_required_env_vars()
        setup_logging()
        validate_azure_services()
        print("✅ All startup checks passed!")
    except Exception as e:
        print(f"❌ Startup check failed: {e}")
        sys.exit(1)
