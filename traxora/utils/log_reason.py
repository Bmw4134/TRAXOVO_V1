import json
from datetime import datetime
import os

LOG_PATH = "logs/skipped_rows.jsonl"

def log_skip(reason, row=None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "reason": reason,
        "row_preview": str(row)[:200] if row else "N/A"
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
