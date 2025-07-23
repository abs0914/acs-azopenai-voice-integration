#!/usr/bin/env python3
"""
Fixed main.py with proper error handling and startup logic
"""
import os
import sys
import traceback

print("🚀 Starting ACS Voice Integration Application (Fixed Version)...")
print(f"🐍 Python version: {sys.version}")
print(f"📍 Working directory: {os.getcwd()}")

# Set up the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"🛤️ Python path updated: {sys.path[:3]}")

def start_full_application():
    """Try to start the full application"""
    try:
        print("🔧 Attempting to start full application...")
        
        # Import required modules
        print("📦 Importing startup module...")
        from startup import check_required_env_vars
        
        print("📦 Importing CallAutomationApp...")
        from src.core.app import CallAutomationApp
        
        print("✅ All modules imported successfully")
        
        # Check required environment variables
        print("🔍 Checking environment variables...")
        check_required_env_vars()
        print("✅ Environment variables validated")
        
        # Create application instance
        print("🏗️ Creating application instance...")
        app_instance = CallAutomationApp()
        print("✅ Application instance created successfully")
        
        # Get the Quart app instance
        app = app_instance.app
        print("✅ Quart app instance obtained")
        
        # Start the server
        port = int(os.getenv("PORT", "8000"))
        print(f"🌐 Starting full application server on port {port}...")
        
        app_instance.run(host="0.0.0.0", port=port)
        return True
        
    except Exception as e:
        print(f"❌ Full application failed: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def start_health_fallback():
    """Start health check fallback"""
    try:
        print("🏥 Starting health check fallback...")
        from health import app
        
        port = int(os.getenv("PORT", "8000"))
        print(f"🌐 Starting health check server on port {port}...")
        
        app.run(host="0.0.0.0", port=port)
        return True
        
    except Exception as e:
        print(f"❌ Health check fallback failed: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def start_minimal_fallback():
    """Start minimal fallback server"""
    try:
        print("🔧 Starting minimal fallback server...")
        from quart import Quart, Response
        
        app = Quart(__name__)
        
        @app.route("/")
        async def hello():
            return "🔧 ACS Voice Integration - Minimal Fallback Mode"
        
        @app.route("/health")
        async def health():
            return Response("Healthy - Minimal Fallback", status=200)
        
        @app.route("/status")
        async def status():
            return {
                "status": "minimal_fallback",
                "message": "Full application failed to start",
                "python_version": sys.version,
                "working_directory": os.getcwd()
            }
        
        port = int(os.getenv("PORT", "8000"))
        print(f"🌐 Starting minimal fallback server on port {port}...")
        
        app.run(host="0.0.0.0", port=port)
        return True
        
    except Exception as e:
        print(f"❌ Even minimal fallback failed: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main startup function with progressive fallback"""
    print("🎯 Starting application with progressive fallback strategy...")
    
    # Try full application first
    if start_full_application():
        print("✅ Full application started successfully")
        return
    
    print("⚠️ Full application failed, trying health check fallback...")
    
    # Try health check fallback
    if start_health_fallback():
        print("✅ Health check fallback started successfully")
        return
    
    print("⚠️ Health check failed, trying minimal fallback...")
    
    # Try minimal fallback
    if start_minimal_fallback():
        print("✅ Minimal fallback started successfully")
        return
    
    # If everything fails, exit with error
    print("❌ All startup methods failed!")
    sys.exit(1)

if __name__ == "__main__":
    main()
