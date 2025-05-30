#!/bin/bash
echo "[Kaizen] Compressing non-essential AI modules for deploy..."
zip -r ai_modules_backup.zip diff_watcher.py llm_test.py goal_tracker.json session_audit.json prompt_fingerprint.json
echo "[Kaizen] AI modules compressed to ai_modules_backup.zip"
