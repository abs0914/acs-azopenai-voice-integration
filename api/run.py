#!/usr/bin/env python3
"""
Simple Python-based startup script for Azure App Service
This avoids bash/shell issues and uses Python directly
"""
import os
import sys
import subprocess

def main():
    print("🚀 Starting ACS Voice Integration Application...")
    print(f"🐍 Python version: {sys.version}")
    print(f"📍 Current directory: {os.getcwd()}")
    print(f"📁 Directory contents: {os.listdir('.')}")
    
    # Set up Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Check if main.py exists
    if not os.path.exists('main.py'):
        print("❌ main.py not found!")
        print(f"📁 Contents: {os.listdir('.')}")
        sys.exit(1)
    
    # Install requirements if they exist
    if os.path.exists('requirements.txt'):
        print("📦 Installing requirements...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--user', '-r', 'requirements.txt'
            ])
            print("✅ Requirements installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Failed to install requirements: {e}")
            print("🔄 Continuing anyway...")
    
    # Set port
    port = os.getenv('PORT', '8000')
    os.environ['PORT'] = port
    
    print(f"🌐 Starting application on port {port}...")
    
    # Import and run the application
    try:
        import main
        print("✅ Application started successfully")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("🏥 Trying minimal fallback...")
        
        # Create minimal fallback server
        try:
            from quart import Quart, Response
            
            app = Quart(__name__)
            
            @app.route("/")
            async def hello():
                return "ACS Voice Integration - Minimal Mode (Python Startup)"
            
            @app.route("/health")
            async def health():
                return Response("Healthy", status=200)
            
            @app.route("/error-info")
            async def error_info():
                return {
                    "error": str(e),
                    "python_version": sys.version,
                    "directory": os.getcwd(),
                    "files": os.listdir('.'),
                    "python_path": sys.path[:5]  # First 5 entries
                }
            
            print(f"🌐 Starting minimal server on port {port}...")
            app.run(host="0.0.0.0", port=int(port))
            
        except Exception as fallback_error:
            print(f"❌ Even fallback failed: {fallback_error}")
            sys.exit(1)

if __name__ == "__main__":
    main()
