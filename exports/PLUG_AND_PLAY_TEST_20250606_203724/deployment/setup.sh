#!/bin/bash
# NEXUS Dashboard Setup Script

echo "🚀 Setting up NEXUS Dashboard..."

# Install Python dependencies
pip install -r core/requirements.txt

# Create necessary directories
mkdir -p config logs trading/logs instance

# Copy environment template
cp config/environment_template.env .env
echo "📝 Please edit .env file with your API keys"

# Set up database
python core/app_nexus.py &
sleep 5
pkill -f app_nexus.py

echo "✅ NEXUS Dashboard setup complete!"
echo "📖 Edit .env file and run: python core/main.py"
