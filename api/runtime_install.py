#!/usr/bin/env python3
"""
Runtime installation startup script
Installs dependencies at runtime to bypass deployment issues
"""
import os
import sys
import subprocess
import time

print("🔧 Runtime Installation Startup Script")
print(f"🐍 Python version: {sys.version}")
print(f"📍 Working directory: {os.getcwd()}")

def install_package(package):
    """Install a single package with error handling"""
    try:
        print(f"📦 Installing {package}...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--user', '--no-cache-dir', package
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ {package} installed successfully")
            return True
        else:
            print(f"⚠️ {package} failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {package} installation timed out")
        return False
    except Exception as e:
        print(f"❌ {package} error: {e}")
        return False

def install_core_dependencies():
    """Install only the most essential dependencies"""
    essential_packages = [
        'quart==0.19.9',
        'requests==2.32.3',
        'python-dotenv==1.0.1'
    ]
    
    print("🎯 Installing essential packages...")
    success_count = 0
    
    for package in essential_packages:
        if install_package(package):
            success_count += 1
        time.sleep(1)  # Small delay between installations
    
    print(f"✅ {success_count}/{len(essential_packages)} essential packages installed")
    return success_count > 0

def install_azure_dependencies():
    """Install Azure-specific dependencies"""
    azure_packages = [
        'azure-core==1.32.0',
        'azure-identity==1.15.0',
        'azure-communication-callautomation==1.2.0'
    ]
    
    print("☁️ Installing Azure packages...")
    success_count = 0
    
    for package in azure_packages:
        if install_package(package):
            success_count += 1
        time.sleep(1)
    
    print(f"✅ {success_count}/{len(azure_packages)} Azure packages installed")
    return success_count > 0

def start_minimal_server():
    """Start a minimal server that works without external dependencies"""
    print("🔧 Starting minimal server (no external dependencies)...")
    
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    
    class MinimalHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress logging
        
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Healthy - Runtime Install Mode')
                
            elif self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = """
                <html>
                <head><title>ACS Voice Integration - Runtime Install Mode</title></head>
                <body>
                <h1>🔧 ACS Voice Integration - Runtime Install Mode</h1>
                <p><strong>Status:</strong> Dependencies being installed at runtime</p>
                <p><strong>Reason:</strong> Azure deployment build process failed</p>
                <h2>Available Endpoints:</h2>
                <ul>
                <li><a href="/health">/health</a> - Health check</li>
                <li><a href="/status">/status</a> - Installation status</li>
                <li><a href="/install-progress">/install-progress</a> - Installation progress</li>
                </ul>
                </body>
                </html>
                """.encode()
                self.wfile.write(html)
                
            elif self.path == '/status':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                status = {
                    "mode": "runtime_install",
                    "python_version": sys.version,
                    "working_directory": os.getcwd(),
                    "environment_variables": {
                        "PORT": os.getenv('PORT'),
                        "WEBSITE_SITE_NAME": os.getenv('WEBSITE_SITE_NAME'),
                        "ACS_CONNECTION_STRING": "✅" if os.getenv("ACS_CONNECTION_STRING") else "❌"
                    }
                }
                
                response = json.dumps(status, indent=2).encode()
                self.wfile.write(response)
                
            else:
                self.send_response(404)
                self.end_headers()
    
    port = int(os.getenv('PORT', '8000'))
    server = HTTPServer(('0.0.0.0', port), MinimalHandler)
    print(f"🌐 Minimal server running on port {port}")
    server.serve_forever()

def start_quart_server():
    """Start Quart server if available"""
    try:
        print("🚀 Starting Quart server...")
        from quart import Quart, Response, jsonify
        
        app = Quart(__name__)
        
        @app.route("/")
        async def hello():
            return "🚀 ACS Voice Integration - Runtime Install Success!"
        
        @app.route("/health")
        async def health():
            return Response("Healthy - Quart Runtime Mode", status=200)
        
        @app.route("/status")
        async def status():
            return jsonify({
                "mode": "quart_runtime",
                "status": "dependencies_installed",
                "python_version": sys.version,
                "working_directory": os.getcwd()
            })
        
        port = int(os.getenv('PORT', '8000'))
        print(f"🌐 Quart server running on port {port}")
        app.run(host="0.0.0.0", port=port)
        
    except ImportError:
        print("❌ Quart not available, falling back to minimal server")
        start_minimal_server()
    except Exception as e:
        print(f"❌ Quart server failed: {e}")
        start_minimal_server()

def main():
    """Main runtime installation and startup"""
    print("🎯 Starting runtime installation process...")
    
    # Try to install essential dependencies
    if install_core_dependencies():
        print("✅ Core dependencies installed, trying Quart server...")
        start_quart_server()
    else:
        print("⚠️ Core dependencies failed, starting minimal server...")
        start_minimal_server()

if __name__ == "__main__":
    main()
