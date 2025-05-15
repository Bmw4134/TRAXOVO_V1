"""
Reports Package

This package contains modules for generating various reports:
- Attendance reports (late start, early end, not on job)
- Billing reports
- Work zone GPS efficiency reports
"""

# Import report generators for easier access
from reports.attendance import generate_same_day_report, generate_prior_day_report