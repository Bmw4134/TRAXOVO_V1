# Deploy Nexus Watson via GitHub to Cloud Run

## Method 1: Use Individual Files from 'deploy' folder

1. Download these files from the `deploy` folder in Replit:
   - main.py
   - production.py  
   - intelligence_export_engine.py
   - Dockerfile
   - requirements.txt
   - templates/ (entire folder)
   - static/ (entire folder)

2. Create a new GitHub repository

3. Upload all files to your GitHub repository

4. In Google Cloud Run:
   - Select "Continuously deploy from a repository"
   - Connect your GitHub repository
   - Configure build settings:
     - Build Type: Dockerfile
     - Source: / (root)
   - Service settings:
     - Port: 8080
     - Memory: 1Gi
     - Environment: SESSION_SECRET=nexus_watson_supreme_production

## Method 2: Use this Replit directly

If your Replit is connected to GitHub:

1. Commit all files to your GitHub repository from Replit
2. In Cloud Run, connect to that same repository
3. Use the same configuration settings above

## Method 3: Manual file creation

Copy and paste the key files directly:

### main.py
```python
from production import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
```

### requirements.txt
```
flask==2.3.3
gunicorn==21.2.0
```

### Dockerfile
```dockerfile
FROM python:3.11-alpine
ENV PORT=8080
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "main:app"]
```

Then copy the larger files (production.py, intelligence_export_engine.py) from the deploy folder.

## After Deployment

Your application will be available at the Cloud Run URL with:
- Watson dashboard login (watson/Btpp@1513)
- Intelligence export functionality
- Real-time API endpoints

The deployment should complete successfully with these optimized files.