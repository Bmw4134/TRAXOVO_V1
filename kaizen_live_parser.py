# kaizen_live_parser.py
import pandas as pd
import json
import os

def load_memory():
    with open("meta/kaizen_parse_memory.json") as f:
        return json.load(f)

def parse_file(file, schema):
    try:
        df = pd.read_csv(file)
        if all(field in df.columns for field in schema):
            print(f"✅ Parsed {file} successfully")
            return df
        else:
            print(f"⚠️ Schema mismatch in {file}")
            return None
    except Exception as e:
        print(f"❌ Failed to parse {file}: {e}")
        return None

def run_live_parsing():
    memory = load_memory()
    results = {}
    for file, config in memory.items():
        df = parse_file(file, config["fields"])
        if df is not None:
            results[file] = df.head().to_dict()  # Only preview for now
    with open("dashboard_summary.json", "w") as f:
        json.dump(results, f, indent=2)
    print("🧠 Summary saved to dashboard_summary.json")

if __name__ == "__main__":
    run_live_parsing()
