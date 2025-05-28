
# TRAXOVO Fleet Analytics: YTD Utilization Module

Includes:
- Asset-level usage parsing from Excel
- Monthly KPI extraction: Usage hrs, Distance, Idle %
- UI stub for rendering asset rows + map pins
- Ready to ingest data from accounting system for cost overlays

Deploy:
1. Add `fleet_analytics_utilization.py` to routes
2. Point file upload handler to Excel source
3. Render `fleet_utilization.html` at /fleet/utilization
