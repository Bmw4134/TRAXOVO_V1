# Ultra-minimal Cloud Run Dockerfile
FROM python:3.11-alpine

# Production environment
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# Install only essential dependencies
RUN pip install --no-cache-dir flask==2.3.3 gunicorn==21.2.0

# Working directory
WORKDIR /app

# Copy production application and intelligence engine
COPY production.py main.py
COPY intelligence_export_engine.py .
COPY templates templates
COPY static static

# Create minimal models file
RUN echo "# Production models placeholder" > models.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/api/status')" || exit 1

# Expose port
EXPOSE 8080

# Production command
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "main:app"]