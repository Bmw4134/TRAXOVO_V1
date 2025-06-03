
# kaizen_trace_logger.py
import pandas as pd
import traceback

def trace_driver_report_flow(file_paths):
    try:
        logs = []

        logs.append("🔍 Starting Driver Report Trace Logger")

        for label, path in file_paths.items():
            logs.append(f"📁 Loading {label} from: {path}")
            df = pd.read_csv(path)

            logs.append(f"✅ {label}: {len(df)} rows loaded. Columns: {list(df.columns)}")

            if label == "DrivingHistory":
                assert "Contact" in df.columns, "Missing 'Contact'"
                assert "EventDateTime" in df.columns, "Missing 'EventDateTime'"
            if label == "AssetsTimeOnSite":
                assert "Locationx" in df.columns, "Missing 'Locationx'"

        logs.append("📊 Validating classification engine references...")
        from utils import weekly_driver_processor
        if not hasattr(weekly_driver_processor, "classify_driver_activity"):
            logs.append("❌ No 'classify_driver_activity' method found in weekly_driver_processor.")
        else:
            logs.append("✅ Classification function exists.")

        logs.append("🎯 Report processor is wired and ready.")
        return "\n".join(logs)

    except Exception as e:
        return "💥 ERROR during trace:\n" + traceback.format_exc()
