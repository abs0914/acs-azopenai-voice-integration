import os
import sys

# Try to import and run the full application
try:
    # Check if we're in a minimal health check mode
    if os.getenv("HEALTH_CHECK_ONLY", "false").lower() == "true":
        from health import app
        print("Running in health check only mode")
    else:
        # Run the full application with environment variable checks
        from startup import check_required_env_vars
        from src.core.app import CallAutomationApp

        # Check required environment variables first
        check_required_env_vars()

        # Create application instance
        app_instance = CallAutomationApp()
        # Get the Quart app instance
        app = app_instance.app

        if __name__ == "__main__":
            app_instance.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

except Exception as e:
    print(f"Error starting application: {str(e)}")
    print("Falling back to health check mode...")

    # Fall back to simple health check app
    from health import app

    if __name__ == "__main__":
        port = int(os.getenv("PORT", "8000"))
        app.run(host="0.0.0.0", port=port)
