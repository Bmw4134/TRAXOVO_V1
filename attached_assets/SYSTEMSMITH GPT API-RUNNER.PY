# SYSTEMSMITH GPT API RUNNER (Fleet Version)
# This script ingests JSON/CSV Activity Data and returns GPT-4 analysis via OpenAI API

import openai
import pandas as pd
import json
from datetime import datetime

# 🔑 STEP 1: Insert your API key here
openai.api_key = "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"

# 📂 STEP 2: Load your local file (CSV or JSON)
INPUT_FILE = "GAUGE API PULL 1045AM_05.15.2025.json"  # or .csv or .xlsx

def load_file(filepath):
    if filepath.endswith(".json"):
        with open(filepath, 'r') as f:
            return json.load(f)
    elif filepath.endswith(".csv"):
        return pd.read_csv(filepath).to_dict(orient='records')
    elif filepath.endswith(".xlsx"):
        return pd.read_excel(filepath).to_dict(orient='records')
    else:
        raise ValueError("Unsupported file type")

# 🧠 STEP 3: System prompt logic (same as GPT Builder personality)
system_message = {
    "role": "system",
    "content": (
        "You are SYSTEMSMITH-FLEET, a GPT optimized for GPS-based employee attendance, asset tracking, and jobsite intelligence.\n"
        "You accept data from Activity Detail or API exports including fields like 'AssetIdentifier', 'EventDateTimeString', 'Reason', 'Latitude', and 'Location'.\n"
        "You match assets to employees using known mappings and detect behavior patterns like Late Start, Left Early, or Not On Job.\n"
        "You also construct implicit geofences by grouping repeated coordinates and matching by label (e.g., 'DFW Yard', 'TEXDIST').\n"
        "Return a clean daily summary report of driver or asset activity. Flag exceptions clearly.\n"
    )
}

# 📨 STEP 4: Build messages and send to GPT
activity_data = load_file(INPUT_FILE)

user_message = {
    "role": "user",
    "content": (
        f"Analyze the following {len(activity_data)} activity events.\n"
        "Return a daily driver/asset report with late starts, early ends, or missing presence.\n"
        f"\n```json\n{json.dumps(activity_data[:20], indent=2)}\n```\n\n(Note: only showing first 20 records for performance.)"
    )
}

response = openai.ChatCompletion.create(
    model="gpt-4-1106-preview",
    messages=[system_message, user_message],
    temperature=0.2
)

# 📤 STEP 5: Output the response
print("\n----- SYSTEMSMITH DAILY REPORT -----\n")
print(response['choices'][0]['message']['content'])
