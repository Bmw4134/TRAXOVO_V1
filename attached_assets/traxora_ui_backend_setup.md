# 🚀 TRAXORA File Upload Integration (UI + Backend)

This guide completes the connection between your React file upload UI and the backend processing logic in Flask.

---

## ✅ Step-by-Step Setup (All-in-One)

### 📁 1. Create a new file: `routes/file_upload.py`

```python
from flask import Blueprint, request, jsonify
import pandas as pd
from enhanced_data_ingestion import load_data
from agents import driver_classifier_agent

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = uploaded_file.filename
    ext = filename.split(".")[-1].lower()
    file_type = "excel" if ext in ["xlsx", "xls"] else "csv"

    try:
        # Save temporarily
        temp_path = f"/tmp/{filename}"
        uploaded_file.save(temp_path)

        # Load and classify
        df = load_data(temp_path, file_type=file_type, skip_fluff_rows=5)
        if df is None:
            return jsonify({"error": "Could not parse file"}), 422

        result = driver_classifier_agent.handle(df.to_dict(orient="records"))

        return jsonify({
            "classified_count": result.get("count", 0),
            "skipped_count": len(result.get("skipped", [])),
            "skipped": result.get("skipped", [])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

### 🧠 2. Register the Upload Route in `main.py` or `app.py`

Add this to the bottom or your app initialization code:

```python
from routes.file_upload import upload_bp
app.register_blueprint(upload_bp)
```

---

## ✅ Now You Can:

1. Run Replit
2. Use your browser UI to drag in `.csv` or `.xlsx` reports
3. See the classification result instantly (success, skipped, reasons)

This is your live ingestion + classifier pipeline in action.
