
# 🧪 KAIZEN REPORT TRACE LOGGER

## USAGE
Import and run this tool in your Replit to verify the driver report pipeline:

```python
from kaizen_trace_logger import trace_driver_report_flow

file_paths = {
    "DrivingHistory": "data/DrivingHistory.csv",
    "AssetsTimeOnSite": "data/AssetsTimeOnSite.csv",
    "ActivityDetail": "data/ActivityDetail.csv"
}

print(trace_driver_report_flow(file_paths))
```

## OUTPUT
Will confirm:
- Each file loads
- Required columns exist
- Weekly processor is connected
- Classification engine is reachable

Use this to detect if recent schema patches broke data linkage.
