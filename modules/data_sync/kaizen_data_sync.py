# kaizen_data_sync.py
import pandas as pd
import json

def load_parsing_rules():
    with open("meta/kaizen_parse_memory.json") as f:
        return json.load(f)

def validate_csv(path, schema):
    df = pd.read_csv(path)
    return all(col in df.columns for col in schema)

def sync_all():
    rules = load_parsing_rules()
    for file, spec in rules.items():
        try:
            valid = validate_csv(file, spec["fields"])
            if not valid:
                print(f"⚠️ Schema mismatch in {file}")
            else:
                print(f"✅ {file} schema verified")
        except Exception as e:
            print(f"❌ Error reading {file}: {e}")

if __name__ == "__main__":
    sync_all()
