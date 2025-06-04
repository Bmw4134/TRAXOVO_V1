# qq_recursive_diagnosis_engine.py
import os
import json
import time
from pathlib import Path
from hashlib import sha256

class RecursiveDiagnosisEngine:
    def __init__(self, root_dir="./", legacy_signals=None):
        self.root = Path(root_dir)
        self.legacy_signals = legacy_signals or ["dailyDriver", "assetMap", "jobZone"]
        self.drift_log = []
        self.scan_time = time.time()
        self.output_file = "qq_drift_map.json"

    def hash_file(self, path):
        with open(path, 'rb') as f:
            return sha256(f.read()).hexdigest()

    def match_legacy(self, content):
        return any(signal in content for signal in self.legacy_signals)

    def scan(self):
        for filepath in self.root.rglob("*.js"):
            if "node_modules" in str(filepath):
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    code = file.read()
                    if self.match_legacy(code):
                        self.log_drift(filepath, code)
            except Exception as e:
                continue

    def log_drift(self, path, content):
        signal_hits = [s for s in self.legacy_signals if s in content]
        self.drift_log.append({
            "file": str(path),
            "hits": signal_hits,
            "hash": self.hash_file(path),
            "timestamp": time.time()
        })

    def save(self):
        with open(self.output_file, 'w') as f:
            json.dump({"scanned": self.scan_time, "results": self.drift_log}, f, indent=2)

if __name__ == "__main__":
    engine = RecursiveDiagnosisEngine()
    engine.scan()
    engine.save()
    print(f"🧠 Drift mapping complete. Output written to {engine.output_file}")