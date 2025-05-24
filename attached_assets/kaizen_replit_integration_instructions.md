
# 🔧 Kaizen Sync Agent: Replit File Integration Instructions

This document provides standardized instructions for Replit agents when receiving Kaizen system files.

## 📂 File Placement

Please move the following files to their correct directories:

- `kaizen_watchdog.py` → `utils/`
- `kaizen_theme.css` → `static/css/`

## ⚙️ Configuration Tasks

1. Ensure `start_watchdog()` from `kaizen_watchdog.py` is invoked on application startup.
2. In your main layout file (likely `templates/base.html`), add this line inside the `<head>` tag:
```html
<link rel="stylesheet" href="/static/css/kaizen_theme.css">
```

## ✅ Post-Integration Checks

- Verify that `/admin` renders with the dark Kaizen theme
- Confirm that editing any file in `routes/` or `templates/` triggers auto sync testing via the watchdog

## 🛑 Conflict Handling

If any file already exists:
- Backup the old version to `*_backup.py` or `*_old.css`
- Notify the developer if overwrites were skipped or failed

Thank you.
