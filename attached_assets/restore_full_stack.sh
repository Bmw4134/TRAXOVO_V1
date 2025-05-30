#!/bin/bash
echo "[Kaizen] Restoring entire Kaizen stack..."
bash restore_core_ai.sh
bash restore_reports.sh
bash restore_meta.sh
echo "[Kaizen] Full restoration complete"
