# ✅ Combined Prompt for Replit: Navigation Fix + Weekly Report Parsing Repair
**Date:** 2025-05-23 18:29:19**


---

## 🧭 PART 1: NAVIGATION CONSISTENCY FIXES (UI ONLY)

Fix the following navigation issues across all TRAXORA modules:

1. **Dashboard Re-Entry**
   - Add a clickable TRAXORA logo or "Home" link on all screens to return to `/dashboard`.

2. **Sidebar**
   - Unify all module views with the same sidebar layout.
   - Highlight the current section (e.g., Enhanced Weekly Report) consistently.

3. **Back Buttons**
   - Add a visible “Back to Overview” or “Return to Dashboard” button on each detailed view.

4. **Missing Link Repair**
   - Ensure working navigation for:
     - Modern File Upload
     - Asset Map
     - Enhanced Weekly Report

5. **Mobile View**
   - Fix sidebar/hamburger menu for mobile to show all routes.

🔒 DO NOT touch any processing or data classification logic for this section.

---

## 🛠️ PART 2: WEEKLY DRIVER REPORT DATA PARSING FIX

📌 CRITICAL ROOT CAUSE:
Field name mismatches are causing every driver to be misclassified as “Not On Job.”

### 🔧 UPDATE FIELD MAPPINGS:

**DrivingHistory.csv:**
- `Contact` → Driver Name
- `EventDateTime` → Timestamp
- `Location` → Jobsite

**ActivityDetail.csv:**
- `Contact` → Driver Name
- `EventDateTimex` → Timestamp
- `Locationx` → Jobsite

### 🧠 REQUIRED CODE UPDATES:
Update in `weekly_driver_processor.py`:
- Line 456, 462, 468: Fix driver name field to `Contact`
- Line 515, 525, 535: Fix job site field to `Locationx` for ActivityDetail
- Implement name cleaner: extract “Ammar Elhamad” from “Ammar Elhamad (210003)”

### 🧪 CONFIRMATION:
Re-run `/enhanced-weekly-report/process-may-data`
- Should now show On Time, Late Start, Early End
- Include a “Matched Jobsite” field in the debug logs

✅ Please respond once both UI fixes and parsing logic updates are complete. This is critical for restoring reporting functionality.
