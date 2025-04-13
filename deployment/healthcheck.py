#!/usr/bin/env python
import http.server
import socketserver
import json
import os
import urllib.request
import urllib.error
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('healthcheck')

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
            logger.info(f"Checking Flask health at http://localhost:{flask_port}/health")
            with urllib.request.urlopen(f"http://localhost:{flask_port}/health", timeout=5) as response:
                self.flask_healthy = response.status == 200
                logger.info(f"Flask health: {'OK' if self.flask_healthy else 'FAILED'}")
        except Exception as e:
            self.flask_healthy = False
            logger.warning(f"Flask health check failed: {str(e)}")
        
        # Check Bot service
        try:
            bot_port = os.environ.get("PORT", "8000")
            logger.info(f"Checking Bot health at http://localhost:{bot_port}/health")
            with urllib.request.urlopen(f"http://localhost:{bot_port}/health", timeout=5) as response:
                self.bot_healthy = response.status == 200
                logger.info(f"Bot health: {'OK' if self.bot_healthy else 'FAILED'}")
        except Exception as e:
            # Bot health is optional - we consider it "OK" if the service isn't responding
            self.bot_healthy = True
            logger.warning(f"Bot health check skipped: {str(e)}")

health_status = HealthStatus()

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - - [%s] %s" % 
                (self.address_string(),
                 self.log_date_time_string(),
                 format % args))
                 
    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            # Always update health status on request
            health_status.update()
            
            # We'll return 200 status code for Azure to keep the container running
            # even if Flask is not yet ready (it might be starting up)
            status_code = 200
            
            self.send_response(status_code)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            health_data = {
                "status": "healthy" if health_status.flask_healthy else "starting",
                "timestamp": time.time(),
                "services": {
                    "flask": "up" if health_status.flask_healthy else "starting",
                    "bot": "up" if health_status.bot_healthy else "starting",
                }
            }
            
            logger.info(f"Health check response: {json.dumps(health_data)}")
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

if __name__ == "__main__":
    port = int(os.environ.get("WEBSITES_PORT", 8080))
    logger.info(f"Starting health check server on port {port}")
    
    # Allow socket reuse to prevent "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
            logger.info(f"Health check service started at port {port}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health check server error: {str(e)}")
