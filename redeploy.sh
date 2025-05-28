#!/bin/bash
# redeploy.sh - Kaizen GPT Auto Redeploy Script

echo "[Kaizen GPT] Triggering TRAXOVO redeploy..."
echo "[Kaizen GPT] Timestamp: $(date)"

# Add all changes
git add .

# Commit with timestamp
git commit -m "KaizenGPT Auto Redeploy - $(date '+%Y-%m-%d %H:%M:%S')"

# Push to trigger redeploy
git push origin main

echo "[Kaizen GPT] Redeploy triggered successfully!"
echo "[Kaizen GPT] Check your Replit dashboard for deployment confirmation."
echo "[Kaizen GPT] TRAXOVO Fleet Management System updating..."