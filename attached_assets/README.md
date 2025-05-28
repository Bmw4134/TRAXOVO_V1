
# TRAXOVO Enhancement Patch: KPIs, Maps, Roles

## Includes:
- ✅ KPI Export (Excel .xlsx of driver metrics)
- ✅ Role-based dashboards (Admin vs PM vs Driver)
- ✅ GPS map zone refresh JavaScript stub (for future Mapbox/Leaflet integration)

To install:
1. Merge /routes and /static into your current workspace
2. Hook `kpi_export.py` to your daily scheduler
3. Attach `get_dashboard_view()` to your login role handler
