import os
import sys
from dotenv import load_dotenv

def check_required_env_vars():
    """Check if all required environment variables are set"""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Define required environment variables by category
    required_vars = {
        "Azure Communication Services": [
            "ACS_CONNECTION_STRING",
            "COGNITIVE_SERVICE_ENDPOINT",
            "AGENT_PHONE_NUMBER"
        ],
        "Azure OpenAI": [
            "AZURE_OPENAI_SERVICE_KEY",
            "AZURE_OPENAI_SERVICE_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT_MODEL_NAME",
            "AZURE_OPENAI_DEPLOYMENT_MODEL"
        ],
        "Azure AI Voice Live API": [
            "AZURE_VOICE_LIVE_API_KEY"
        ],
        "Application Settings": [
            "CALLBACK_URI_HOST"
        ],
        "CosmosDB": [
            "COSMOS_DB_DATABASE_NAME",
            "COSMOS_DB_CONTAINER_NAME",
            "COSMOS_DB_URL",
            "COSMOS_DB_KEY"
        ],
        "Redis": [
            "REDIS_URL",
            "REDIS_PASSWORD"
        ]
    }
    
    # Check each required variable
    missing_vars = {}
    for category, vars_list in required_vars.items():
        missing_in_category = []
        for var in vars_list:
            if not os.getenv(var):
                missing_in_category.append(var)
        
        if missing_in_category:
            missing_vars[category] = missing_in_category
    
    # If any variables are missing, print error message and exit
    if missing_vars:
        print("\n❌ ERROR: Missing required environment variables")
        print("==================================================")
        
        for category, vars_list in missing_vars.items():
            print(f"\n📋 {category}:")
            for var in vars_list:
                print(f"   - {var}")
        
        print("\n📝 Please set these environment variables in your Azure App Service Configuration")
        print("   or provide a .env file with these values.")
        print("\n🔗 For more information, see the README.md file.")
        
        # Exit with error code
        sys.exit(1)
    
    print("✅ All required environment variables are set")
    return True

if __name__ == "__main__":
    # Check required environment variables
    check_required_env_vars()
    
    # If all required variables are set, import and run the application
    try:
        from src.core.app import CallAutomationApp
        
        # Create application instance
        app_instance = CallAutomationApp()
        # Get the Quart app instance
        app = app_instance.app
        
        print("✅ Application initialized successfully")
        print("🚀 Starting server...")
        
        # Run the application
        app_instance.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
    except Exception as e:
        print(f"❌ Error starting application: {str(e)}")
        sys.exit(1)
