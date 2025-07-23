#!/usr/bin/env python3
"""
Comprehensive Azure App Service startup script for ACS Voice Integration
Handles Azure deployment environment and provides detailed diagnostics
"""
import os
import sys
import subprocess
import json
import traceback

def print_diagnostic_info():
    """Print comprehensive diagnostic information"""
    print("=" * 60)
    print("🔍 AZURE APP SERVICE DIAGNOSTIC INFORMATION")
    print("=" * 60)
    print(f"🐍 Python version: {sys.version}")
    print(f"📍 Current working directory: {os.getcwd()}")
    print(f"🏠 Home directory: {os.path.expanduser('~')}")
    print(f"👤 User: {os.getenv('USER', 'unknown')}")
    print(f"🌐 PORT environment variable: {os.getenv('PORT', 'not set')}")

    # Check common Azure App Service paths
    azure_paths = [
        "/home/site/wwwroot",
        "/opt/python",
        "/usr/local/bin",
        os.getcwd()
    ]

    for path in azure_paths:
        if os.path.exists(path):
            print(f"📁 {path} contents: {os.listdir(path)[:10]}")  # First 10 items
        else:
            print(f"❌ {path} does not exist")

    print(f"🛤️ Python path (first 5): {sys.path[:5]}")
    print(f"🔧 Environment variables (selected):")
    for key in ['PYTHONPATH', 'PATH', 'WEBSITE_SITE_NAME', 'WEBSITE_RESOURCE_GROUP']:
        print(f"   {key}: {os.getenv(key, 'not set')}")
    print("=" * 60)

def install_requirements():
    """Install requirements with comprehensive error handling"""
    requirements_files = ['requirements.txt', 'api/requirements.txt']

    for req_file in requirements_files:
        if os.path.exists(req_file):
            print(f"📦 Found requirements file: {req_file}")
            try:
                print(f"📋 Installing from {req_file}...")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '--user', '--no-cache-dir', '-r', req_file
                ], capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    print("✅ Requirements installed successfully")
                    return True
                else:
                    print(f"⚠️ Pip install failed with return code {result.returncode}")
                    print(f"📤 STDOUT: {result.stdout}")
                    print(f"📤 STDERR: {result.stderr}")

            except subprocess.TimeoutExpired:
                print("⏰ Pip install timed out after 5 minutes")
            except Exception as e:
                print(f"❌ Exception during pip install: {e}")

    print("⚠️ No requirements.txt found or installation failed")
    return False

def find_main_module():
    """Find the main application module"""
    possible_locations = [
        'main.py',
        'api/main.py',
        'src/main.py',
        'app.py',
        'api/app.py'
    ]

    for location in possible_locations:
        if os.path.exists(location):
            print(f"✅ Found main module at: {location}")
            return location

    print("❌ No main module found!")
    return None

def start_main_application(main_location):
    """Start the main application"""
    try:
        # Add the directory containing main.py to Python path
        main_dir = os.path.dirname(os.path.abspath(main_location))
        if main_dir not in sys.path:
            sys.path.insert(0, main_dir)

        # Change to the directory containing main.py
        original_cwd = os.getcwd()
        os.chdir(main_dir)

        print(f"📂 Changed to directory: {os.getcwd()}")
        print(f"🚀 Importing main module from: {main_location}")

        # Import the main module
        if main_location.endswith('main.py'):
            import main
        elif main_location.endswith('app.py'):
            import app
        else:
            print(f"❌ Unknown main module type: {main_location}")
            return False

        print("✅ Main application started successfully")
        return True

    except Exception as e:
        print(f"❌ Error starting main application: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def create_fallback_server():
    """Create a minimal fallback server for diagnostics"""
    try:
        print("🏥 Creating fallback diagnostic server...")

        # Try to import Quart
        try:
            from quart import Quart, Response, jsonify
        except ImportError:
            print("❌ Quart not available, trying Flask...")
            try:
                from flask import Flask as Quart, Response, jsonify
            except ImportError:
                print("❌ Neither Quart nor Flask available")
                return False

        app = Quart(__name__)

        @app.route("/")
        async def hello():
            return "🏥 ACS Voice Integration - Diagnostic Mode"

        @app.route("/health")
        async def health():
            return Response("Healthy - Diagnostic Mode", status=200)

        @app.route("/diagnostic")
        async def diagnostic():
            return jsonify({
                "status": "diagnostic_mode",
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "files_in_directory": os.listdir('.'),
                "python_path": sys.path[:10],
                "environment_variables": {
                    "PORT": os.getenv('PORT'),
                    "PYTHONPATH": os.getenv('PYTHONPATH'),
                    "WEBSITE_SITE_NAME": os.getenv('WEBSITE_SITE_NAME'),
                    "WEBSITE_RESOURCE_GROUP": os.getenv('WEBSITE_RESOURCE_GROUP')
                }
            })

        port = int(os.getenv('PORT', '8000'))
        print(f"🌐 Starting diagnostic server on port {port}...")

        # Run the app
        if hasattr(app, 'run'):
            app.run(host="0.0.0.0", port=port, debug=False)
        else:
            # For Flask
            app.run(host="0.0.0.0", port=port, debug=False)

        return True

    except Exception as e:
        print(f"❌ Fallback server failed: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting ACS Voice Integration Application...")

    # Print diagnostic information
    print_diagnostic_info()

    # Set up environment
    port = os.getenv('PORT', '8000')
    os.environ['PORT'] = port

    # Install requirements
    install_requirements()

    # Find and start main application
    main_location = find_main_module()
    if main_location and start_main_application(main_location):
        print("✅ Application startup completed successfully")
        return

    # If main application failed, start fallback server
    print("🔄 Main application failed, starting fallback diagnostic server...")
    if create_fallback_server():
        print("✅ Fallback server started")
    else:
        print("❌ All startup methods failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
