# Optimized production Dockerfile for Cloud Run
FROM python:3.11-slim

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=5000

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy and install minimal Python dependencies first (for better caching)
COPY production_requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r production_requirements.txt

# Copy only essential application files
COPY main.py .
COPY start_production.sh .
COPY templates/ templates/
COPY static/ static/

# Make startup script executable
RUN chmod +x start_production.sh

# Change ownership to app user
RUN chown -R app:app /app
USER app

# Single port exposure for Cloud Run
EXPOSE $PORT

# Production-ready startup
CMD ["./start_production.sh"]