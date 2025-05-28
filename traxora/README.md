# TRAXORA (GENIUS CORE)

This project runs under Kaizen GPT with dual-mode architecture:
- `runtime_mode.py`: toggles dev/prod logic via REPLIT_PROFILE
- `init_db.py`: initializes with fallbacks
- `mtd_data_processor.py`: filters data for robust ingestion
- Async chunking, logging, and error resilience
- PM Checklist + dev config for field testing

Agents expected:
- DriverClassifier
- GeoValidator
- ReportGenerator
- OutputFormatter

Log everything, fail gracefully, and evolve modularly.
