#!/bin/bash
echo "[Kaizen] Creating lightweight production bundle..."
zip -r traxovo-deployable-core.zip main.py app.py templates static requirements.txt .replit replit.nix -x "*.csv" "*.zip" "*.json" "*.log" "data/*" "logs/*" "__pycache__/*"
echo "[Kaizen] Bundle ready: traxovo-deployable-core.zip"
