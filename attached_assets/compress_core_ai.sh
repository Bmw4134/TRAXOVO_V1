#!/bin/bash
echo "[Kaizen] Compressing core AI modules..."
zip -r kaizen_core.zip diff_watcher.py llm_test.py goal_tracker.json session_audit.json prompt_fingerprint.json
echo "[Kaizen] Core AI modules zipped to kaizen_core.zip"
