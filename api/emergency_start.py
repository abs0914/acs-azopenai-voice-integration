#!/usr/bin/env python3
"""
Emergency startup script that works even with missing dependencies
"""
import os
import sys

print("🚨 Emergency startup - handling deployment issues...")

def test_imports():
    """Test which imports are available"""
    available = {}
    
    # Test core imports
    try:
        import quart
        available['quart'] = True
    except ImportError:
        available['quart'] = False
    
    try:
        from azure.communication.callautomation import CallAutomationClient
        available['azure_call_automation'] = True
    except ImportError:
        available['azure_call_automation'] = False
    
    try:
        import openai
        available['openai'] = True
    except ImportError:
        available['openai'] = False
    
    return available

def start_with_available_imports():
    """Start server with whatever imports are available"""
    available = test_imports()
    print(f"📦 Available imports: {available}")
    
    if available.get('quart'):
        print("✅ Quart available - starting Quart server")
        from quart import Quart, Response, jsonify
        
        app = Quart(__name__)
        
        @app.route("/")
        async def hello():
            return "🚨 ACS Voice Integration - Emergency Mode (Post-Deployment)"
        
        @app.route("/health")
        async def health():
            return Response("Healthy - Emergency Mode", status=200)
        
        @app.route("/imports")
        async def imports_status():
            return jsonify({
                "available_imports": test_imports(),
                "status": "emergency_mode",
                "message": "Some dependencies may be missing from deployment"
            })
        
        @app.route("/env-check")
        async def env_check():
            return jsonify({
                "environment_variables": {
                    "ACS_CONNECTION_STRING": "✅" if os.getenv("ACS_CONNECTION_STRING") else "❌",
                    "AZURE_OPENAI_SERVICE_KEY": "✅" if os.getenv("AZURE_OPENAI_SERVICE_KEY") else "❌",
                    "CALLBACK_URI_HOST": "✅" if os.getenv("CALLBACK_URI_HOST") else "❌",
                },
                "working_directory": os.getcwd(),
                "python_version": sys.version
            })
        
        port = int(os.getenv("PORT", "8000"))
        print(f"🌐 Starting Quart server on port {port}")
        app.run(host="0.0.0.0", port=port)
        
    else:
        print("❌ Quart not available - starting basic HTTP server")
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json
        
        class EmergencyHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Healthy - Basic HTTP Mode')
                elif self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    html = b"""
                    <html><body>
                    <h1>ACS Voice Integration - Basic HTTP Mode</h1>
                    <p>Deployment had issues - running in basic mode</p>
                    <p><a href="/health">Health Check</a></p>
                    </body></html>
                    """
                    self.wfile.write(html)
                else:
                    self.send_response(404)
                    self.end_headers()
        
        port = int(os.getenv("PORT", "8000"))
        server = HTTPServer(('0.0.0.0', port), EmergencyHandler)
        print(f"🌐 Starting basic HTTP server on port {port}")
        server.serve_forever()

if __name__ == "__main__":
    start_with_available_imports()
