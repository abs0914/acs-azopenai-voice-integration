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
    """Check and install missing dependencies with enhanced error handling"""
    required_packages = [
        ('python-dotenv', 'dotenv'),
        ('quart', 'quart'),
        ('azure-communication-callautomation', 'azure.communication.callautomation'),
        ('azure-core', 'azure.core'),
        ('azure-identity', 'azure.identity'),
        ('openai', 'openai'),
        ('requests', 'requests')
    ]

    missing_packages = []
    for pip_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {pip_name} available")
        except ImportError:
            missing_packages.append(pip_name)
            print(f"❌ {pip_name} missing")

    if missing_packages:
        print(f"🔧 Installing {len(missing_packages)} missing packages...")
        import subprocess

        # Try different installation methods
        install_methods = [
            ['--user', '--no-cache-dir'],
            ['--user', '--no-cache-dir', '--force-reinstall'],
            ['--no-cache-dir'],
            ['--user']
        ]

        for package in missing_packages:
            installed = False
            for method in install_methods:
                try:
                    cmd = [sys.executable, '-m', 'pip', 'install'] + method + [package]
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
                    print(f"✅ Installed {package} with method {method}")
                    installed = True
                    break
                except Exception as e:
                    print(f"⚠️ Method {method} failed for {package}: {e}")
                    continue

            if not installed:
                print(f"❌ All installation methods failed for {package}")

    # Refresh Python path
    try:
        import site
        site.main()
        print("✅ Python path refreshed")
    except Exception as e:
        print(f"⚠️ Failed to refresh Python path: {e}")

    return len(missing_packages) == 0

async def answer_incoming_call(call_data):
    """Answer an incoming call"""
    try:
        print("📞 Attempting to answer incoming call...")

        # Import ACS client
        from azure.communication.callautomation import CallAutomationClient
        from azure.identity import DefaultAzureCredential

        # Get connection string
        connection_string = os.getenv("ACS_CONNECTION_STRING")
        if not connection_string:
            print("❌ ACS_CONNECTION_STRING not found")
            return

        # Create client
        client = CallAutomationClient.from_connection_string(connection_string)

        # Extract call information
        incoming_call_context = call_data.get("incomingCallContext")
        callback_uri = f"{os.getenv('CALLBACK_URI_HOST')}/api/callbacks"

        if incoming_call_context:
            print(f"📞 Answering call with context: {incoming_call_context}")

            # Answer the call
            answer_call_result = client.answer_call(
                incoming_call_context=incoming_call_context,
                callback_url=callback_uri
            )

            print(f"✅ Call answered successfully: {answer_call_result.call_connection_id}")
            return answer_call_result
        else:
            print("❌ No incoming call context found")

    except Exception as e:
        print(f"❌ Error answering call: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")

async def handle_call_connected(call_connection_id, call_data):
    """Handle a connected call"""
    try:
        print(f"📞 Handling connected call: {call_connection_id}")

        # Import ACS client
        from azure.communication.callautomation import CallAutomationClient

        # Get connection string
        connection_string = os.getenv("ACS_CONNECTION_STRING")
        if not connection_string:
            print("❌ ACS_CONNECTION_STRING not found")
            return

        # Create client
        client = CallAutomationClient.from_connection_string(connection_string)
        call_connection = client.get_call_connection(call_connection_id)

        # Play a welcome message using TTS
        welcome_message = "Hello! Welcome to the ACS Voice Integration. How can I help you today?"

        print(f"📞 Playing welcome message: {welcome_message}")

        try:
            # Import TTS source
            from azure.communication.callautomation import TextSource

            # Create TTS source
            text_source = TextSource(
                text=welcome_message,
                voice_name="en-US-JennyNeural"  # Use a clear female voice
            )

            # Play the message using TTS
            play_result = call_connection.play_media_to_all(
                play_source=text_source,
                operation_context="welcome_message"
            )

            print(f"✅ Welcome message initiated with TTS: {play_result}")

        except Exception as tts_error:
            print(f"❌ TTS failed, trying simple text: {tts_error}")

            # Fallback: try without TTS
            try:
                play_result = call_connection.play_media_to_all(
                    play_source=welcome_message,
                    operation_context="welcome_message_fallback"
                )
                print(f"✅ Fallback message initiated: {play_result}")
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")

                # Last resort: just log that call is connected
                print("📞 Call connected but unable to play welcome message")

    except Exception as e:
        print(f"❌ Error handling connected call: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")

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

        # Event Grid webhook endpoints
        @app.route("/api/callbacks", methods=["POST"])
        async def handle_event_grid_webhook():
            """Handle Event Grid webhook for ACS call automation events"""
            try:
                data = await request.get_json()
                print(f"📞 Received Event Grid webhook: {data}")

                # Handle Event Grid validation
                if isinstance(data, list) and len(data) > 0:
                    event = data[0]

                    # Event Grid subscription validation
                    if event.get("eventType") == "Microsoft.EventGrid.SubscriptionValidationEvent":
                        validation_code = event["data"]["validationCode"]
                        print(f"✅ Event Grid validation code: {validation_code}")
                        return jsonify({"validationResponse": validation_code})

                    # Handle ACS call automation events
                    elif event.get("eventType", "").startswith("Microsoft.Communication."):
                        event_type = event.get("eventType")
                        call_connection_id = event.get("data", {}).get("callConnectionId")

                        print(f"📞 ACS Event: {event_type}")
                        print(f"📞 Call Connection ID: {call_connection_id}")

                        # Log the full event for debugging
                        print(f"📞 Full event data: {event}")

                        # Handle specific call events
                        if event_type == "Microsoft.Communication.IncomingCall":
                            print("📞 Incoming call detected - attempting to answer...")
                            try:
                                # Answer the incoming call
                                await answer_incoming_call(event.get("data", {}))
                            except Exception as e:
                                print(f"❌ Failed to answer call: {e}")

                        elif event_type == "Microsoft.Communication.CallConnected":
                            print("📞 Call connected - starting conversation...")
                            try:
                                # Start the voice conversation
                                await handle_call_connected(call_connection_id, event.get("data", {}))
                            except Exception as e:
                                print(f"❌ Failed to handle connected call: {e}")

                        elif event_type == "Microsoft.Communication.CallDisconnected":
                            print("📞 Call disconnected")

                        elif event_type == "Microsoft.Communication.PlayCompleted":
                            print("🎵 Welcome message completed")
                            # Here you could start listening for user input

                        elif event_type == "Microsoft.Communication.PlayFailed":
                            print("❌ Welcome message failed to play")
                            print(f"📋 Play failure details: {event.get('data', {})}")

                        else:
                            print(f"📞 Unhandled event type: {event_type}")

                        return jsonify({"status": "received", "eventType": event_type})

                return jsonify({"status": "received"})

            except Exception as e:
                print(f"❌ Error handling webhook: {str(e)}")
                print(f"📋 Traceback: {traceback.format_exc()}")
                return jsonify({"error": str(e)}), 500

        @app.route("/api/callbacks", methods=["GET"])
        async def webhook_info():
            """Provide information about the webhook endpoint"""
            return jsonify({
                "webhook_url": f"{os.getenv('CALLBACK_URI_HOST', 'https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net')}/api/callbacks",
                "methods": ["POST"],
                "description": "Event Grid webhook for ACS call automation events",
                "supported_events": [
                    "Microsoft.EventGrid.SubscriptionValidationEvent",
                    "Microsoft.Communication.CallConnected",
                    "Microsoft.Communication.CallDisconnected",
                    "Microsoft.Communication.RecognizeCompleted",
                    "Microsoft.Communication.PlayCompleted"
                ]
            })

        @app.route("/webhook-test")
        async def webhook_test():
            """Test webhook configuration"""
            webhook_url = f"{os.getenv('CALLBACK_URI_HOST', 'https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net')}/api/callbacks"

            return jsonify({
                "webhook_endpoint": webhook_url,
                "callback_uri_host": os.getenv('CALLBACK_URI_HOST'),
                "environment_check": {
                    "ACS_CONNECTION_STRING": "✅ Set" if os.getenv("ACS_CONNECTION_STRING") else "❌ Missing",
                    "CALLBACK_URI_HOST": "✅ Set" if os.getenv("CALLBACK_URI_HOST") else "❌ Missing"
                },
                "instructions": {
                    "event_grid_subscription": f"Use this URL for Event Grid subscription: {webhook_url}",
                    "test_webhook": f"Send POST request to: {webhook_url}"
                }
            })

        @app.route("/test-tts")
        async def test_tts():
            """Test TTS functionality"""
            try:
                from azure.communication.callautomation import TextSource

                # Test creating a TTS source
                text_source = TextSource(
                    text="This is a test message",
                    voice_name="en-US-JennyNeural"
                )

                return jsonify({
                    "status": "success",
                    "message": "TTS TextSource created successfully",
                    "voice_name": "en-US-JennyNeural",
                    "test_text": "This is a test message"
                })

            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "message": "TTS TextSource creation failed"
                })
        
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
