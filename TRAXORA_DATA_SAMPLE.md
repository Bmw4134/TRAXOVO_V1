# TRAXORA Data Sample

## Sample CSV Data Format

### DrivingHistory.csv
This file contains GPS tracking data for drivers including their locations and timestamps.

```csv
Contact,EventDateTime,Locationx,Speed,Heading,Ignition
"Ammar Elhamad (210003)","2025-05-18 07:15:23","Job Site 342 - Plano Center",12.5,180,"On"
"James Ramirez (210044)","2025-05-18 07:45:12","Job Site 342 - Plano Center",0,0,"Off"
"Sarah Johnson (210089)","2025-05-18 08:10:56","Transit - Dallas Highway",65.3,90,"On"
"David Chen (210076)","2025-05-18 07:22:45","Job Site 105 - North Complex",8.2,270,"On"
"Maria Garcia (210027)","2025-05-18 07:05:33","Job Site 243 - Eastern Heights",0,0,"On"
```

### ActivityDetail.csv
This file tracks specific driver activities and job site assignments.

```csv
Contact,EventDateTime,Locationx,ActivityType,Duration,JobNumber
"Ammar Elhamad (210003)","2025-05-18 07:15:00","Job Site 342 - Plano Center","Start Shift",480,"PLANO-2025-003"
"James Ramirez (210044)","2025-05-18 07:45:00","Job Site 342 - Plano Center","Start Shift",435,"PLANO-2025-003"
"Sarah Johnson (210089)","2025-05-18 08:15:00","Job Site 108 - South Tower","Start Shift",390,"SOUTH-2025-108"
"David Chen (210076)","2025-05-18 07:25:00","Job Site 105 - North Complex","Start Shift",480,"NORTH-2025-105"
"Maria Garcia (210027)","2025-05-18 07:05:00","Job Site 243 - Eastern Heights","Start Shift",510,"EAST-2025-243"
```

### AssetsTimeOnSite.csv
This file tracks how long assets (which may be associated with drivers) spend at job sites.

```csv
Contact,AssetID,JobSite,EventDateTime,Duration,Status
"Ammar Elhamad (210003)","TRUCK-45678","Job Site 342 - Plano Center","2025-05-18 07:15:00",480,"On Site"
"James Ramirez (210044)","TRUCK-32145","Job Site 342 - Plano Center","2025-05-18 07:45:00",435,"On Site"
"Sarah Johnson (210089)","TRUCK-78901","Job Site 108 - South Tower","2025-05-18 08:15:00",390,"On Site"
"David Chen (210076)","TRUCK-56789","Job Site 105 - North Complex","2025-05-18 07:25:00",480,"On Site"
"Maria Garcia (210027)","TRUCK-67890","Job Site 243 - Eastern Heights","2025-05-18 07:05:00",510,"On Site"
```

## Attendance Classification Rules

Based on the data, the system classifies drivers as follows:

1. **On Time**: 
   - Arrives before 7:30 AM
   - Stays until at least 4:00 PM
   - Total on-site time of 7+ hours

2. **Late Start**:
   - Arrives after 7:30 AM

3. **Early End**:
   - Leaves before 4:00 PM
   - Total on-site time less than 7 hours

4. **Not On Job**:
   - No valid job site detected
   - Missing tracking data

## Example Classification Results

| Driver | Date | First Seen | Last Seen | Hours | Status |
|--------|------|------------|-----------|-------|--------|
| Ammar Elhamad | 2025-05-18 | 07:15:23 | 15:15:23 | 8.0 | On Time |
| James Ramirez | 2025-05-18 | 07:45:12 | 15:00:12 | 7.25 | Late Start |
| Sarah Johnson | 2025-05-18 | 08:10:56 | 14:40:56 | 6.5 | Late Start + Early End |
| David Chen | 2025-05-18 | 07:22:45 | 15:22:45 | 8.0 | On Time |
| Maria Garcia | 2025-05-18 | 07:05:33 | 15:35:33 | 8.5 | On Time |

This sample data demonstrates how TRAXORA processes and classifies driver attendance based on real-world GPS and activity data.