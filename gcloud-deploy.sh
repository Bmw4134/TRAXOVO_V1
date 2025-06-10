#!/bin/bash
# Ultra-Fast Cloud Run Deployment Script

set -euo pipefail

# Configuration
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
SERVICE_NAME="nexus-watson"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 NEXUS DEPLOYMENT SWEEP INITIATED"
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"

# Enable required APIs
echo "📡 Enabling Cloud Run API..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project=$PROJECT_ID

# Build with Cloud Build for speed
echo "🔨 Building container image..."
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID

# Deploy to Cloud Run
echo "🚁 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars "SESSION_SECRET=nexus_watson_supreme_production,PORT=8080" \
  --execution-environment gen2 \
  --cpu-throttling \
  --project=$PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)

echo "✅ DEPLOYMENT COMPLETE"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔍 Health Check: $SERVICE_URL/api/status"

# Test deployment
echo "🧪 Testing deployment..."
sleep 5
curl -f "$SERVICE_URL/api/status" && echo "✅ Health check passed" || echo "❌ Health check failed"