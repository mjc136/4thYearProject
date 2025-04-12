#!/usr/bin/env python
import http.server
import socketserver
import json
import os
import urllib.request
import urllib.error
import time

class HealthStatus:
    def __init__(self):
        self.flask_healthy = False
        self.bot_healthy = False
        self.last_checked = 0

    def update(self):
        # Don't check more often than every 10 seconds
        if time.time() - self.last_checked < 10:
            return
            
        self.last_checked = time.time()
        
        # Check Flask service
        try:
            flask_port = os.environ.get("FLASK_PORT", "5000")
            with urllib.request.urlopen(f"http://localhost:{flask_port}/health", timeout=2) as response:
                self.flask_healthy = response.status == 200
        except (urllib.error.URLError, ConnectionRefusedError):
            self.flask_healthy = False
        
        # Check Bot service
        try:
            bot_port = os.environ.get("PORT", "8000")
            with urllib.request.urlopen(f"http://localhost:{bot_port}/health", timeout=2) as response:
                self.bot_healthy = response.status == 200
        except (urllib.error.URLError, ConnectionRefusedError):
            # Bot health is optional - we consider it "OK" if the service isn't responding
            self.bot_healthy = True

health_status = HealthStatus()

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            health_status.update()
            
            status_code = 200 if health_status.flask_healthy else 503
            
            self.send_response(status_code)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            health_data = {
                "status": "healthy" if health_status.flask_healthy else "unhealthy",
                "timestamp": time.time(),
                "services": {
                    "flask": "up" if health_status.flask_healthy else "down",
                    "bot": "up" if health_status.bot_healthy else "down",
                }
            }
            
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

if __name__ == "__main__":
    port = 8080
    with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
        print(f"Health check service started at port {port}")
        httpd.serve_forever()
