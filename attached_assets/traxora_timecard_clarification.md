# 📝 Clarification on Timecard Data and Ground Works Integration

Thanks for outlining the driver report generation flow — it’s clear and helpful.

However, I wanted to clarify the type of timecard data I’m currently using so we don’t cross any wires during processing or integration.

---

## 🧾 Current Timecard Context

- The timecards I’m referencing **are not the finalized records** from our accounting system.
- For billing and payroll validation, I use **what has actually been paid out** — which is pulled from our accounting backend.
- What I’m using now are **daily Ground Works reports**, generated from our payroll team’s daily email.
- These Ground Works reports show:
  - **Prior-day hours and quantities**
  - **Unapproved time entries**
  - Intended for review and reconciliation — not official yet

---

## 🔗 Integration Intent

Even though the Ground Works data is unofficial:
- I want to tie it directly into the **Daily Driver Report logic**
- This allows us to compare:
  - GPS-verified time-in/time-out vs. reported timecard hours
  - Site attendance vs. what’s been logged for payroll
- It adds valuable operational insight *before* the accounting data becomes available

---

## ✅ Ask

Please make sure TRAXORA:
- Accepts these Ground Works files as a **valid timecard input**
- Flags them internally as `unverified_timecard_source` (or similar)
- Still uses them in daily classification and reporting logic

Let me know if this needs further clarification.
