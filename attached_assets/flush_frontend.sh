#!/bin/bash
echo "🔄 Killing stale Python processes..."
killall python3

echo "🔧 Removing cached frontend artifacts..."
rm -rf __pycache__ static/.cache

echo "🛠️ Touching templates to trigger refresh..."
touch templates/*.html

echo "✅ Now re-run: python3 app.py (or main.py)"
