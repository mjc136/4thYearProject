# Use the official Python image from Docker Hub
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app/

# Set environment variables (ensure these are configured in Azure)
ENV PYTHONPATH="/app/bot"
ENV PORT=8000

# Expose the port (Make sure this matches Azure settings)
EXPOSE 8000

# Run the application
CMD ["python", "-m", "bot.app"]
