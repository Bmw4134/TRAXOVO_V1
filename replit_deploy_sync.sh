
#!/bin/bash

echo "🔍 Starting TRAXOVO V11 Integrity Audit..."

# Step 1: Confirm directory structure
if [ ! -d "core" ] || [ ! -d "modules" ] || [ ! -f "main.py" ]; then
  echo "❌ Core structure missing. Expected directories: core/, modules/, and file: main.py"
  exit 1
else
  echo "✅ Directory structure looks good."
fi

# Step 2: Check Python routes registration
echo "🔄 Checking route registration in app..."
if grep -q "register_routes()" main.py; then
  echo "✅ Routes are registered."
else
  echo "❌ Route registration call missing in main.py"
fi

# Step 3: Run dependency check
echo "🔍 Verifying required packages from requirements.txt..."
pip install -r requirements.txt

# Step 4: List all modules and sync
echo "📦 Syncing TRAXOVO modules:"
for file in modules/*.py; do
  echo "→ Module: $(basename "$file")"
done

# Step 5: Touch UI auto-refresh trigger
touch static/ui/reload.flag
echo "♻️ UI refresh trigger placed."

# Step 6: Start/Rebind server
echo "🚀 Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:5000 --reload app:app
