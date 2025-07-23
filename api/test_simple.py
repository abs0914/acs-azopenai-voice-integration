#!/usr/bin/env python3
"""
Ultra simple test script
"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Simple test server working!')

port = int(os.getenv('PORT', '8000'))
server = HTTPServer(('0.0.0.0', port), SimpleHandler)
print(f"Simple server on port {port}")
server.serve_forever()
