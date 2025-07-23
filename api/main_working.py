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
        ('requests', 'requests'),
        ('websockets', 'websockets')
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
    """Answer an incoming call with enhanced error handling"""
    try:
        print("📞 Attempting to answer incoming call...")
        print(f"📞 Call data received: {call_data}")

        # Get connection string
        connection_string = os.getenv("ACS_CONNECTION_STRING")
        if not connection_string:
            print("❌ ACS_CONNECTION_STRING not found in environment")
            return None

        # Extract call information
        incoming_call_context = call_data.get("incomingCallContext")
        callback_uri = f"{os.getenv('CALLBACK_URI_HOST', 'https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net')}/api/callbacks"

        print(f"📞 Callback URI: {callback_uri}")
        print(f"📞 Incoming call context: {incoming_call_context}")

        if not incoming_call_context:
            print("❌ No incoming call context found in call data")
            print(f"📞 Available keys in call_data: {list(call_data.keys())}")
            return None

        try:
            # Import ACS client
            from azure.communication.callautomation import CallAutomationClient

            # Create client
            client = CallAutomationClient.from_connection_string(connection_string)
            print("✅ ACS client created successfully")

            # Answer the call
            print(f"📞 Answering call with context: {incoming_call_context[:50]}...")
            answer_call_result = client.answer_call(
                incoming_call_context=incoming_call_context,
                callback_url=callback_uri
            )

            print(f"✅ Call answered successfully: {answer_call_result.call_connection_id}")
            return answer_call_result

        except ImportError as import_error:
            print(f"❌ Failed to import ACS client: {import_error}")
            return None
        except Exception as acs_error:
            print(f"❌ ACS client error: {acs_error}")
            print(f"📋 ACS Traceback: {traceback.format_exc()}")
            return None

    except Exception as e:
        print(f"❌ Error answering call: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return None

async def handle_call_connected(call_connection_id, call_data):
    """Handle a connected call - try Voice Live first, fallback to TTS"""
    try:
        print(f"📞 Handling connected call: {call_connection_id}")

        # First, always try simple TTS to ensure something works
        await fallback_to_simple_tts(call_connection_id)

        # Then try to start Voice Live in the background (optional)
        try:
            print("🎤 Attempting to start Voice Live conversation...")
            from voice_live_integration import start_voice_live_for_call
            success = await start_voice_live_for_call(call_connection_id)

            if success:
                print("✅ Voice Live conversation started successfully")
            else:
                print("⚠️ Voice Live failed to start, but TTS already played")

        except ImportError:
            print("⚠️ Voice Live integration not available, using TTS only")
        except Exception as voice_error:
            print(f"⚠️ Voice Live error (TTS already played): {voice_error}")

    except Exception as e:
        print(f"❌ Error handling connected call: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        # Last resort fallback
        try:
            await fallback_to_simple_tts(call_connection_id)
        except Exception as fallback_error:
            print(f"❌ Even fallback TTS failed: {fallback_error}")

async def fallback_to_simple_tts(call_connection_id):
    """Fallback to simple TTS if Voice Live fails"""
    try:
        print(f"🔄 Using fallback TTS for call: {call_connection_id}")

        # Import ACS client
        from azure.communication.callautomation import CallAutomationClient, TextSource

        # Get connection string
        connection_string = os.getenv("ACS_CONNECTION_STRING")
        if not connection_string:
            print("❌ ACS_CONNECTION_STRING not found")
            return

        # Create client
        client = CallAutomationClient.from_connection_string(connection_string)
        call_connection = client.get_call_connection(call_connection_id)

        # Simple welcome message
        welcome_message = "Hello! Welcome to the ACS Voice Integration. Please hold while we connect you to our voice assistant."

        # Create TTS source
        text_source = TextSource(
            text=welcome_message,
            voice_name="en-US-JennyNeural"
        )

        # Play the message
        play_result = call_connection.play_media_to_all(
            play_source=text_source,
            operation_context="fallback_welcome"
        )

        print(f"✅ Fallback TTS message initiated: {play_result}")

    except Exception as e:
        print(f"❌ Fallback TTS also failed: {e}")
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
                                result = await answer_incoming_call(event.get("data", {}))
                                if result:
                                    print(f"✅ Call answered successfully: {result.call_connection_id}")
                                else:
                                    print("❌ Failed to answer call - no result returned")
                            except Exception as e:
                                print(f"❌ Failed to answer call: {e}")
                                print(f"📋 Answer call traceback: {traceback.format_exc()}")

                        elif event_type == "Microsoft.Communication.CallConnected":
                            print("📞 Call connected - starting conversation...")
                            try:
                                # Start the voice conversation
                                await handle_call_connected(call_connection_id, event.get("data", {}))
                            except Exception as e:
                                print(f"❌ Failed to handle connected call: {e}")
                                print(f"📋 Traceback: {traceback.format_exc()}")
                                # Continue processing other events even if this fails

                        elif event_type == "Microsoft.Communication.CallDisconnected":
                            print("📞 Call disconnected - ending Voice Live conversation")
                            try:
                                from voice_live_integration import end_voice_live_for_call
                                await end_voice_live_for_call()
                            except Exception as e:
                                print(f"❌ Error ending Voice Live conversation: {e}")

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

        @app.route("/test-voice-live")
        async def test_voice_live():
            """Test Voice Live configuration"""
            try:
                voice_live_config = {
                    "endpoint": os.getenv("AZURE_VOICE_LIVE_ENDPOINT"),
                    "deployment": os.getenv("AZURE_VOICE_LIVE_DEPLOYMENT", "vida-voice-bot"),
                    "api_key_configured": "✅" if os.getenv("AZURE_VOICE_LIVE_API_KEY") else "❌",
                }

                # Test if we can import the Voice Live integration
                try:
                    from voice_live_integration import VoiceLiveCallHandler
                    handler = VoiceLiveCallHandler()
                    voice_live_config["integration_status"] = "✅ Voice Live integration available"
                except Exception as e:
                    voice_live_config["integration_status"] = f"❌ Integration error: {str(e)}"

                return jsonify({
                    "status": "success",
                    "voice_live_config": voice_live_config,
                    "message": "Voice Live configuration check completed"
                })

            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "message": "Voice Live configuration test failed"
                })

        @app.route("/install-websockets")
        async def install_websockets():
            """Install websockets dependency for Voice Live"""
            try:
                import subprocess

                # Install websockets
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '--user', '--no-cache-dir', 'websockets==12.0'
                ], capture_output=True, text=True, timeout=120)

                if result.returncode == 0:
                    # Try to import to verify
                    try:
                        import websockets
                        return jsonify({
                            "status": "success",
                            "message": "Websockets installed and imported successfully",
                            "websockets_version": websockets.__version__ if hasattr(websockets, '__version__') else "unknown"
                        })
                    except ImportError:
                        return jsonify({
                            "status": "partial_success",
                            "message": "Websockets installed but import failed - may need app restart"
                        })
                else:
                    return jsonify({
                        "status": "error",
                        "message": f"Installation failed: {result.stderr}"
                    })

            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to install websockets"
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
