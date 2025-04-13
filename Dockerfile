FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 3978
EXPOSE 5000

ENV PORT=3978
ENV FLASK_PORT=5000

CMD ["python", "-m", "backend.main"]
