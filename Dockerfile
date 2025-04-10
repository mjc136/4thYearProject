# Use the official Python image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install supervisor to manage multiple processes
RUN pip install supervisor

# Create directories for deployment files
RUN mkdir -p /etc/supervisor/conf.d/ /app/deployment

# Copy the entire project into the container
COPY . .

# Create supervisord configuration if not exists
RUN if [ ! -f "/etc/supervisor/conf.d/supervisord.conf" ] && [ -f "/app/deployment/supervisord.conf" ]; then \
    cp /app/deployment/supervisord.conf /etc/supervisor/conf.d/supervisord.conf; \
fi

# Generate default supervisord.conf if not exists
RUN if [ ! -f "/etc/supervisor/conf.d/supervisord.conf" ]; then \
    echo "[supervisord]\n\
nodaemon=true\n\
loglevel=info\n\
\n\
[program:flask]\n\
command=python backend/flask_app/flask_app.py\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0\n\
\n\
[program:bot]\n\
command=python bot_app.py\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0\n\
\n\
[program:healthcheck]\n\
command=python healthcheck.py\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0" > /etc/supervisor/conf.d/supervisord.conf; \
fi

# Set environment variables
ENV PYTHONPATH="/app"
ENV FLASK_APP="backend/flask_app/flask_app.py"
ENV PORT=8000

# Create healthcheck endpoint script if it doesn't exist
RUN if [ ! -f "/app/healthcheck.py" ] && [ -f "/app/deployment/healthcheck.py" ]; then \
    cp /app/deployment/healthcheck.py /app/healthcheck.py; \
    chmod +x /app/healthcheck.py; \
fi

# Create a simple healthcheck if neither exists
RUN if [ ! -f "/app/healthcheck.py" ]; then \
    echo '#!/usr/bin/env python\nimport http.server\nimport socketserver\n\nclass HealthCheckHandler(http.server.SimpleHTTPRequestHandler):\n    def do_GET(self):\n        if self.path == "/health":\n            self.send_response(200)\n            self.send_header("Content-type", "text/plain")\n            self.end_headers()\n            self.wfile.write(b"Service is healthy")\n        else:\n            self.send_response(404)\n            self.end_headers()\n\nif __name__ == "__main__":\n    with socketserver.TCPServer(("", 8080), HealthCheckHandler) as httpd:\n        print("Health check service started at port 8080")\n        httpd.serve_forever()' > /app/healthcheck.py; \
    chmod +x /app/healthcheck.py; \
fi

# Expose Flask (5000) and Bot (8000 or 3978) ports and health check port
EXPOSE 5000
EXPOSE 8000
EXPOSE 3978
EXPOSE 8080

# Use supervisord to manage processes
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
