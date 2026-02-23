# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 8001 (preview service, separate from main app on 8000)
EXPOSE 8001

CMD ["gunicorn", "preview_service.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "2"]
