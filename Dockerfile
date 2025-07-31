FROM python:3.11-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create cookies file and temp directories
RUN touch /tmp/cookies.txt && \
    chmod 666 /tmp/cookies.txt && \
    mkdir -p /tmp/videos /tmp/frames /tmp/audio

# Copy application code
COPY . .

EXPOSE 8000

# Increased timeout and added worker class
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "300", "--worker-class", "gthread", "--threads", "4", "app:app"]
