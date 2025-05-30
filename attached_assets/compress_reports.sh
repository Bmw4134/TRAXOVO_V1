#!/bin/bash
echo "[Kaizen] Compressing report files..."
zip -r reports_data.zip GroundWorks DrivingHistory AssetsTimeOnSite ActivityDetail
echo "[Kaizen] Reports compressed to reports_data.zip"
