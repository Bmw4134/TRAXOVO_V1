# GroundWorks Replacement Module
Includes Attendance Workflow, Timekeeping Upload, Quantity Tracker, Approval Engine.

## Setup Instructions

1. Place files:
   - `attendance_workflow.py` → project root
   - HTML files → templates/...
   - Snippets → admin.html via include or copy

2. Register attendance route in `app.py`:
```python
from attendance_workflow import attendance_bp
app.register_blueprint(attendance_bp, url_prefix="/attendance-workflow")
```

3. Ensure your user model supports `is_admin`.

4. Confirm visibility of admin UI.

## Modules
- Attendance Workflow UI
- Timekeeping Upload
- Quantity Entry
- Approval Routing (Foreman → PM → VP)

Use the included Replit Agent prompt to install.