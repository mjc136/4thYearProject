FROM python:3.10-slim

ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
EXPOSE 3978

# Set the command to run the application
CMD ["python", "-m", "backend.main"]
