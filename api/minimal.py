#!/usr/bin/env python3
"""
Ultra-minimal startup script that WILL work
No external dependencies, pure Python only
"""
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import traceback

class MinimalHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging to avoid issues
        pass
    
    def do_GET(self):
        try:
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Healthy - Minimal Mode')
                
            elif self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = """
                <html>
                <head><title>ACS Voice Integration - Emergency Mode</title></head>
                <body>
                <h1>🚨 ACS Voice Integration - Emergency Diagnostic Mode</h1>
                <p><strong>Status:</strong> Container is running successfully!</p>
                <p><strong>Issue:</strong> Main application failed to start</p>
                <h2>Available Endpoints:</h2>
                <ul>
                <li><a href="/health">/health</a> - Health check</li>
                <li><a href="/diagnostic">/diagnostic</a> - System diagnostics</li>
                <li><a href="/files">/files</a> - File listing</li>
                <li><a href="/test-imports">/test-imports</a> - Test Python imports</li>
                <li><a href="/test-main-execution">/test-main-execution</a> - Test main.py execution steps</li>
                </ul>
                </body>
                </html>
                """.encode()
                self.wfile.write(html)
                
            elif self.path == '/diagnostic':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                diagnostic_info = {
                    "status": "emergency_mode",
                    "python_version": sys.version,
                    "working_directory": os.getcwd(),
                    "python_executable": sys.executable,
                    "python_path": sys.path[:10],
                    "environment_variables": {
                        "PORT": os.getenv('PORT'),
                        "PYTHONPATH": os.getenv('PYTHONPATH'),
                        "WEBSITE_SITE_NAME": os.getenv('WEBSITE_SITE_NAME'),
                        "WEBSITE_HOSTNAME": os.getenv('WEBSITE_HOSTNAME'),
                        "WEBSITE_RESOURCE_GROUP": os.getenv('WEBSITE_RESOURCE_GROUP')
                    }
                }
                
                response = json.dumps(diagnostic_info, indent=2).encode()
                self.wfile.write(response)
                
            elif self.path == '/files':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                try:
                    files_info = {
                        "current_directory": os.getcwd(),
                        "files_in_current_dir": os.listdir('.'),
                        "main_py_exists": os.path.exists('main.py'),
                        "requirements_txt_exists": os.path.exists('requirements.txt'),
                        "health_py_exists": os.path.exists('health.py')
                    }
                    
                    # Try to read main.py first few lines
                    if os.path.exists('main.py'):
                        try:
                            with open('main.py', 'r') as f:
                                files_info["main_py_first_10_lines"] = f.readlines()[:10]
                        except Exception as e:
                            files_info["main_py_read_error"] = str(e)
                    
                except Exception as e:
                    files_info = {"error": str(e)}
                
                response = json.dumps(files_info, indent=2).encode()
                self.wfile.write(response)
                
            elif self.path == '/test-imports':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()

                import_tests = {}

                # Test basic imports
                test_modules = ['quart', 'flask', 'azure', 'openai', 'dotenv']

                for module in test_modules:
                    try:
                        __import__(module)
                        import_tests[module] = "✅ Available"
                    except ImportError as e:
                        import_tests[module] = f"❌ Missing: {str(e)}"
                    except Exception as e:
                        import_tests[module] = f"⚠️ Error: {str(e)}"

                # Test main.py import
                try:
                    import main
                    import_tests["main_module"] = "✅ Imports successfully"
                except Exception as e:
                    import_tests["main_module"] = f"❌ Import failed: {str(e)}"
                    import_tests["main_module_traceback"] = traceback.format_exc()

                response = json.dumps(import_tests, indent=2).encode()
                self.wfile.write(response)

            elif self.path == '/test-main-execution':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()

                execution_test = {}

                try:
                    # Test specific imports from main.py
                    from startup import check_required_env_vars
                    execution_test["startup_import"] = "✅ Success"
                except Exception as e:
                    execution_test["startup_import"] = f"❌ Failed: {str(e)}"
                    execution_test["startup_import_traceback"] = traceback.format_exc()

                try:
                    from src.core.app import CallAutomationApp
                    execution_test["app_import"] = "✅ Success"
                except Exception as e:
                    execution_test["app_import"] = f"❌ Failed: {str(e)}"
                    execution_test["app_import_traceback"] = traceback.format_exc()

                try:
                    # Test environment check
                    from startup import check_required_env_vars
                    check_required_env_vars()
                    execution_test["env_check"] = "✅ Success"
                except Exception as e:
                    execution_test["env_check"] = f"❌ Failed: {str(e)}"
                    execution_test["env_check_traceback"] = traceback.format_exc()

                response = json.dumps(execution_test, indent=2).encode()
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
            error_msg = f"Server Error: {str(e)}\n{traceback.format_exc()}"
            self.wfile.write(error_msg.encode())

def main():
    print("🚨 Starting EMERGENCY minimal server...")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Files in directory: {os.listdir('.')}")
    
    port = int(os.getenv('PORT', '8000'))
    
    try:
        server = HTTPServer(('0.0.0.0', port), MinimalHandler)
        print(f"🌐 Emergency server starting on port {port}")
        print("✅ Server should be accessible now!")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Even minimal server failed: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
