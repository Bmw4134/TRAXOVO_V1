#!/bin/bash
# Cloud Run deployment script

set -e

PROJECT_ID=${1:-"your-project-id"}
SERVICE_NAME="traxovo-watson"
REGION="us-central1"

echo "Deploying to Cloud Run..."
echo "Project ID: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"

# Build and deploy in one command
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300s \
  --set-env-vars "SESSION_SECRET=nexus_watson_supreme_production" \
  --project $PROJECT_ID

echo "Deployment complete!"
echo "Service URL: https://$SERVICE_NAME-$REGION.run.app"