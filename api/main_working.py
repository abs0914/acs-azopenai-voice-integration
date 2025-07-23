#!/usr/bin/env python3
"""
Working main application - simplified and robust
"""
import os
import sys
import traceback

print("🚀 Starting ACS Voice Integration - Working Version")
print(f"🐍 Python version: {sys.version}")
print(f"📍 Working directory: {os.getcwd()}")

# Set up the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def check_and_install_dependencies():
    """Check and install missing dependencies"""
    required_packages = [
        'python-dotenv',
        'quart', 
        'azure-communication-callautomation',
        'azure-core',
        'azure-identity',
        'openai'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} missing")
    
    if missing_packages:
        print(f"🔧 Installing {len(missing_packages)} missing packages...")
        import subprocess
        for package in missing_packages:
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '--user', '--no-cache-dir', package
                ], check=True, capture_output=True)
                print(f"✅ Installed {package}")
            except Exception as e:
                print(f"❌ Failed to install {package}: {e}")
    
    return len(missing_packages) == 0

def start_application():
    """Start the main application"""
    try:
        print("🔍 Checking dependencies...")
        if not check_and_install_dependencies():
            print("⚠️ Some dependencies missing, but continuing...")
        
        print("📦 Importing required modules...")
        
        # Import environment loading
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Environment variables loaded")
        except ImportError:
            print("⚠️ python-dotenv not available, using system environment")
        
        # Import Quart
        from quart import Quart, Response, jsonify, request
        print("✅ Quart imported successfully")
        
        # Create Quart app
        app = Quart(__name__)
        print("✅ Quart app created")
        
        # Basic routes
        @app.route("/")
        async def hello():
            return "🚀 ACS Voice Integration - Working Version!"
        
        @app.route("/health")
        async def health():
            return Response("Healthy - Working Main Application", status=200)
        
        @app.route("/status")
        async def status():
            return jsonify({
                "status": "running",
                "mode": "working_main_application",
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "environment_check": {
                    "ACS_CONNECTION_STRING": "✅" if os.getenv("ACS_CONNECTION_STRING") else "❌",
                    "AZURE_OPENAI_SERVICE_KEY": "✅" if os.getenv("AZURE_OPENAI_SERVICE_KEY") else "❌",
                    "CALLBACK_URI_HOST": "✅" if os.getenv("CALLBACK_URI_HOST") else "❌"
                }
            })
        
        @app.route("/env-check")
        async def env_check():
            return jsonify({
                "environment_variables": {
                    "ACS_CONNECTION_STRING": "✅ Set" if os.getenv("ACS_CONNECTION_STRING") else "❌ Missing",
                    "AZURE_OPENAI_SERVICE_ENDPOINT": "✅ Set" if os.getenv("AZURE_OPENAI_SERVICE_ENDPOINT") else "❌ Missing",
                    "AZURE_OPENAI_SERVICE_KEY": "✅ Set" if os.getenv("AZURE_OPENAI_SERVICE_KEY") else "❌ Missing",
                    "CALLBACK_URI_HOST": "✅ Set" if os.getenv("CALLBACK_URI_HOST") else "❌ Missing",
                    "COSMOS_DB_DATABASE_NAME": "✅ Set" if os.getenv("COSMOS_DB_DATABASE_NAME") else "❌ Missing"
                },
                "working_directory": os.getcwd(),
                "python_version": sys.version
            })
        
        @app.route("/test-azure-imports")
        async def test_azure_imports():
            """Test Azure SDK imports"""
            import_results = {}
            
            try:
                from azure.communication.callautomation import CallAutomationClient
                import_results["CallAutomationClient"] = "✅ Available"
            except Exception as e:
                import_results["CallAutomationClient"] = f"❌ Failed: {str(e)}"
            
            try:
                from azure.identity import DefaultAzureCredential
                import_results["DefaultAzureCredential"] = "✅ Available"
            except Exception as e:
                import_results["DefaultAzureCredential"] = f"❌ Failed: {str(e)}"
            
            try:
                import openai
                import_results["openai"] = "✅ Available"
            except Exception as e:
                import_results["openai"] = f"❌ Failed: {str(e)}"
            
            return jsonify({"azure_imports": import_results})
        
        # Start the server
        port = int(os.getenv("PORT", "8000"))
        print(f"🌐 Starting working application on port {port}")
        
        app.run(host="0.0.0.0", port=port)
        
    except Exception as e:
        print(f"❌ Application failed to start: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        
        # Fallback to basic HTTP server
        print("🔧 Starting fallback HTTP server...")
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class FallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                error_msg = f"Main app failed: {str(e)}\nCheck logs for details."
                self.wfile.write(error_msg.encode())
        
        port = int(os.getenv("PORT", "8000"))
        server = HTTPServer(('0.0.0.0', port), FallbackHandler)
        print(f"🌐 Fallback server running on port {port}")
        server.serve_forever()

if __name__ == "__main__":
    start_application()
