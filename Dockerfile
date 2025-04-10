# Use the official Python image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Set environment variables
ENV PYTHONPATH="/app"
ENV FLASK_APP="backend/flask_app/flask_app.py"
ENV PORT=8000

# Expose Flask (5000) and Bot (8000 or 3978) ports
EXPOSE 5000
EXPOSE 8000
EXPOSE 3978

# Run both Flask and bot apps in parallel
CMD ["sh", "-c", "python backend/flask_app/flask_app.py & python bot_app.py"]
