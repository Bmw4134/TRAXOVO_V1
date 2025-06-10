#!/bin/bash
# Nexus Watson Cloud Run Deployment

PROJECT_ID=${1:-""}
if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./deploy-nexus.sh PROJECT_ID"
    exit 1
fi

echo "Deploying Nexus Watson Intelligence Platform to Cloud Run..."

# Single command deployment with intelligence export functionality
gcloud run deploy nexus-watson \
    --source . \
    --platform managed \
    --region us-central1 \
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
echo "Intelligence Export endpoints available:"
echo "  - JSON: /api/export/json"
echo "  - CSV: /api/export/csv" 
echo "  - Widget Config: /api/export/widget-config"
echo "  - Dashboard Bundle: /api/export/dashboard-bundle"
echo "  - Real-time API: /api/export/full-intelligence"