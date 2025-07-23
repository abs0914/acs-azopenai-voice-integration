#!/usr/bin/env python3
"""
Zero dependencies startup script
Uses only Python standard library - guaranteed to work
"""
import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

print("🔧 Zero Dependencies Startup Script")
print(f"🐍 Python version: {sys.version}")
print(f"📍 Working directory: {os.getcwd()}")
print(f"📁 Files: {os.listdir('.')}")

class ZeroDepsHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def do_GET(self):
        try:
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Healthy - Zero Dependencies Mode')
                
            elif self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>ACS Voice Integration - Zero Dependencies Mode</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; }
                        .status { background: #e8f5e8; padding: 20px; border-radius: 5px; }
                        .error { background: #ffe8e8; padding: 20px; border-radius: 5px; }
                        ul { list-style-type: none; padding: 0; }
                        li { margin: 10px 0; }
                        a { color: #0066cc; text-decoration: none; }
                        a:hover { text-decoration: underline; }
                    </style>
                </head>
                <body>
                    <h1>🔧 ACS Voice Integration - Zero Dependencies Mode</h1>
                    
                    <div class="status">
                        <h2>✅ Status: Running Successfully</h2>
                        <p><strong>Mode:</strong> Zero Dependencies (Python Standard Library Only)</p>
                        <p><strong>Reason:</strong> Azure deployment build process failed during pip install</p>
                        <p><strong>Solution:</strong> Running with minimal functionality to diagnose issues</p>
                    </div>
                    
                    <h2>🔍 Available Diagnostic Endpoints:</h2>
                    <ul>
                        <li>🏥 <a href="/health">/health</a> - Basic health check</li>
                        <li>📊 <a href="/status">/status</a> - System status (JSON)</li>
                        <li>📁 <a href="/files">/files</a> - File system info</li>
                        <li>🌐 <a href="/env">/env</a> - Environment variables</li>
                        <li>🧪 <a href="/test-imports">/test-imports</a> - Test package imports</li>
                        <li>🔧 <a href="/install-deps">/install-deps</a> - Try installing dependencies</li>
                    </ul>
                    
                    <h2>📋 Next Steps:</h2>
                    <ol>
                        <li>Check <a href="/test-imports">/test-imports</a> to see which packages are available</li>
                        <li>Try <a href="/install-deps">/install-deps</a> to install missing dependencies</li>
                        <li>Use Azure Portal to change startup command if needed</li>
                    </ol>
                </body>
                </html>
                """.encode()
                self.wfile.write(html)
                
            elif self.path == '/status':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                status = {
                    "mode": "zero_dependencies",
                    "status": "running",
                    "python_version": sys.version,
                    "python_executable": sys.executable,
                    "working_directory": os.getcwd(),
                    "python_path": sys.path[:5],
                    "environment": {
                        "PORT": os.getenv('PORT'),
                        "WEBSITE_SITE_NAME": os.getenv('WEBSITE_SITE_NAME'),
                        "WEBSITE_HOSTNAME": os.getenv('WEBSITE_HOSTNAME'),
                        "PYTHONPATH": os.getenv('PYTHONPATH')
                    }
                }
                
                response = json.dumps(status, indent=2).encode()
                self.wfile.write(response)
                
            elif self.path == '/files':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                try:
                    files_info = {
                        "current_directory": os.getcwd(),
                        "files": os.listdir('.'),
                        "main_py_exists": os.path.exists('main.py'),
                        "requirements_txt_exists": os.path.exists('requirements.txt'),
                        "startup_scripts": [f for f in os.listdir('.') if f.endswith('.py') and 'start' in f.lower()]
                    }
                except Exception as e:
                    files_info = {"error": str(e)}
                
                response = json.dumps(files_info, indent=2).encode()
                self.wfile.write(response)
                
            elif self.path == '/env':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Show key environment variables (mask sensitive ones)
                env_vars = {}
                key_vars = [
                    'PORT', 'WEBSITE_SITE_NAME', 'WEBSITE_HOSTNAME', 'PYTHONPATH',
                    'ACS_CONNECTION_STRING', 'AZURE_OPENAI_SERVICE_ENDPOINT',
                    'CALLBACK_URI_HOST', 'COSMOS_DB_DATABASE_NAME'
                ]
                
                for var in key_vars:
                    value = os.getenv(var)
                    if value:
                        # Mask sensitive values
                        if 'key' in var.lower() or 'connection' in var.lower():
                            env_vars[var] = f"***{value[-4:]}" if len(value) > 4 else "***"
                        else:
                            env_vars[var] = value
                    else:
                        env_vars[var] = None
                
                response = json.dumps({"environment_variables": env_vars}, indent=2).encode()
                self.wfile.write(response)
                
            elif self.path == '/test-imports':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                import_tests = {}
                test_modules = ['quart', 'requests', 'azure', 'openai', 'redis', 'dotenv']
                
                for module in test_modules:
                    try:
                        __import__(module)
                        import_tests[module] = "✅ Available"
                    except ImportError:
                        import_tests[module] = "❌ Not available"
                    except Exception as e:
                        import_tests[module] = f"⚠️ Error: {str(e)}"
                
                response = json.dumps({"import_tests": import_tests}, indent=2).encode()
                self.wfile.write(response)
                
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Not Found')
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            error_msg = f"Server Error: {str(e)}"
            self.wfile.write(error_msg.encode())

def main():
    """Start the zero dependencies server"""
    port = int(os.getenv('PORT', '8000'))
    
    try:
        server = HTTPServer(('0.0.0.0', port), ZeroDepsHandler)
        print(f"🌐 Zero Dependencies server starting on port {port}")
        print("✅ Server guaranteed to work - uses only Python standard library!")
        print(f"🔗 Access at: http://localhost:{port}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Even zero dependencies server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
