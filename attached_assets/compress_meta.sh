#!/bin/bash
echo "[Kaizen] Compressing meta-config and evolution state..."
zip -r meta_config.zip intent_matrix.json meta_audit.json prompt_dna.json experiments_queue.json
echo "[Kaizen] Meta config compressed to meta_config.zip"
