#!/usr/bin/env python3
"""
Simple startup script for Azure App Service
Tries main app first, falls back to health check
"""
import os
import sys

def main():
    print("🚀 Simple startup for ACS Voice Integration")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"📁 Files: {os.listdir('.')}")
    
    # Set port
    port = os.getenv('PORT', '8000')
    os.environ['PORT'] = port
    
    # Try to start main application
    try:
        print("🎯 Attempting to start main application...")
        import main
        print("✅ Main application started")
        return
    except Exception as e:
        print(f"❌ Main app failed: {e}")
    
    # Fallback to health check
    try:
        print("🏥 Starting health check fallback...")
        import health
        print("✅ Health check started")
        return
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Last resort - minimal server
    print("🔧 Starting minimal server...")
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ['/health', '/']:
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'ACS Voice Integration - Minimal Mode')
            else:
                self.send_response(404)
                self.end_headers()
    
    server = HTTPServer(('0.0.0.0', int(port)), SimpleHandler)
    print(f"🌐 Minimal server on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    main()
