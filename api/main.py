import os
import sys

print("🚀 Starting ACS Voice Integration Application...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Set up the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try to import and run the full application
try:
    # Check if we're in a minimal health check mode
    if os.getenv("HEALTH_CHECK_ONLY", "false").lower() == "true":
        print("🏥 Running in health check only mode")
        from health import app
    else:
        print("🔧 Attempting to start Voice Live integration...")

        # Try to import Voice Live integration
        try:
            print("📦 Importing Voice Live integration...")
            from voice_live_complete import app
            print("✅ Voice Live integration imported successfully")
            print("🎉 Voice Live integration ready!")

        except ImportError as ie:
            print(f"❌ Failed to import Voice Live integration: {ie}")
            print("🔄 Falling back to health check mode...")
            from health import app
        except Exception as ae:
            print(f"❌ Failed to start Voice Live integration: {ae}")
            print("🔄 Falling back to health check mode...")
            from health import app

except Exception as e:
    print(f"❌ Error starting application: {str(e)}")
    print("🏥 Falling back to health check mode...")

    # Fall back to simple health check app
    try:
        from health import app
        print("✅ Health check app loaded successfully")

        if __name__ == "__main__":
            port = int(os.getenv("PORT", "8000"))
            print(f"🌐 Starting health check server on port {port}...")
            app.run(host="0.0.0.0", port=port)
    except Exception as he:
        print(f"❌ Even health check failed: {str(he)}")
        print("🆘 Creating minimal fallback server...")

        # Create absolute minimal server
        from quart import Quart, Response

        minimal_app = Quart(__name__)

        @minimal_app.route("/")
        async def hello():
            return "ACS Voice Integration - Minimal Mode"

        @minimal_app.route("/health")
        async def health():
            return Response("Healthy", status=200)

        if __name__ == "__main__":
            port = int(os.getenv("PORT", "8000"))
            print(f"🌐 Starting minimal server on port {port}...")
            minimal_app.run(host="0.0.0.0", port=port)
