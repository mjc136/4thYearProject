FROM python:3.10-slim

WORKDIR /app

# Install build dependencies for certain packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install dependencies with verbose output
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -v -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for the SQLite database
RUN mkdir -p /app/data && \
    touch /app/lingolizard.db && \
    chmod 666 /app/lingolizard.db

# Expose ports for Flask and Bot
EXPOSE 3978 5000 8080

# Set environment variables
ENV PORT=3978
ENV FLASK_PORT=5000
ENV WEBSITES_PORT=8080
ENV PYTHONPATH=/app

# Set the command to run the application
CMD ["python", "-m", "backend.main"]
