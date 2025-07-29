"""
ACS Voice Integration Application with Azure AI Voice Live
Main entry point for the application
"""
import os
import sys

print("🚀 Starting ACS Voice Integration Application...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Set up the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Check if we're in health check only mode
if os.getenv("HEALTH_CHECK_ONLY", "false").lower() == "true":
    print("🏥 Running in health check only mode")
    from health import app
else:
    print("🔧 Starting Voice Live integration...")
    try:
        print("📦 Importing Voice Live integration...")
        from voice_live_complete import app
        print("✅ Voice Live integration imported successfully")
        print("🎉 Voice Live integration ready!")
    except Exception as e:
        print(f"❌ Failed to import Voice Live integration: {e}")
        print("🔄 Falling back to health check mode...")
        from health import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"🌐 Starting server on port {port}...")
    app.run(host="0.0.0.0", port=port)
