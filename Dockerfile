FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code
COPY . /app

# Ensure cv file and db are accessible
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

# Run FastAPI backend with 24/7 background scheduler
CMD ["sh", "-c", "python -m uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port ${PORT:-8000}"]
