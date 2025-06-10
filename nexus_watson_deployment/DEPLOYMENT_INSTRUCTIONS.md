# Nexus Watson Deployment Instructions

## Quick Deploy to Google Cloud Run

1. Upload this entire folder to Google Cloud Console
2. In Cloud Run, select "Deploy one revision from source"
3. Upload this folder as ZIP
4. Configure:
   - Port: 8080
   - Memory: 1Gi
   - Environment: SESSION_SECRET=nexus_watson_supreme_production

## Alternative: Command Line Deploy

1. Install Google Cloud SDK
2. Run: gcloud auth login
3. Run: ./deploy-nexus.sh YOUR_PROJECT_ID

## Files Included

- production.py: Main application
- intelligence_export_engine.py: Export functionality
- Dockerfile: Optimized container configuration
- templates/: HTML templates
- static/: CSS, JS, and assets
- requirements.txt: Python dependencies

## Features Available After Deployment

- Watson Command Dashboard
- Intelligence Export Hub (JSON, CSV, XML, Bundle)
- Real-time API endpoints
- Dashboard integration configs for Grafana, Tableau, Power BI

## API Endpoints

- /api/status - System status
- /api/export/json - JSON export
- /api/export/csv - CSV export
- /api/export/dashboard-bundle - Complete bundle
- /api/export/full-intelligence - Real-time intelligence data

Login credentials:
- Username: watson, Password: Btpp@1513
- Username: demo, Password: demo123
