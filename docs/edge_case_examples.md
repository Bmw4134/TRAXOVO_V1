# Edge Case Testing Examples

This document provides examples of the different edge cases the test data generator can create, along with sample data and how to handle them in your code.

## 1. Duplicate Employee IDs Across Assets

**What it tests:** How the system handles the same driver appearing on multiple assets during the same day.

**Example data:**
```
Date: 2025-05-18
Asset: ET-32 James T. Wilson (EMP2345) [DFW]
Time Start: 07:05 AM
Time Stop: 03:25 PM

Date: 2025-05-18
Asset: PT-14 James T. Wilson (EMP2345) [DFW]
Time Start: 11:15 AM
Time Stop: 02:45 PM
```

**Handling strategy:**
```python
# Group by employee ID when present
employee_id_pattern = r'\(([A-Za-z0-9-]+)\)'
employee_ids = []

for asset_label in df['Asset']:
    match = re.search(employee_id_pattern, asset_label)
    if match:
        employee_ids.append(match.group(1))
    else:
        employee_ids.append(None)
        
df['EmployeeID'] = employee_ids
grouped_data = df.groupby('EmployeeID', dropna=True)
```

## 2. Missing Division/Region Data

**What it tests:** System resilience when hierarchical organization data is missing.

**Example data:**
```
Date: 2025-05-18
Asset: ET-32 James T. Wilson (EMP2345)  # No division marker
Time Start: 07:05 AM
Time Stop: 03:25 PM

Date: 2025-05-18
Asset: PT-14 Mary Johnson (EMP8765) [DFW]  # Has division marker
Time Start: 11:15 AM
Time Stop: 02:45 PM
```

**Handling strategy:**
```python
# Extract division with fallback to 'Unknown'
division_pattern = r'\[([A-Z]+)\]'
divisions = []

for asset_label in df['Asset']:
    match = re.search(division_pattern, asset_label)
    if match:
        divisions.append(match.group(1))
    else:
        divisions.append('Unknown')
        
df['Division'] = divisions
```

## 3. Overnight Shifts

**What it tests:** Time calculations for shifts spanning midnight.

**Example data:**
```
Date: 2025-05-18
Asset: ET-32 James T. Wilson (EMP2345) [DFW]
Time Start: 10:15 PM
Time Stop: 06:30 AM (+1)  # Next day marker

Date: 2025-05-18
Asset: PT-14 Mary Johnson (EMP8765) [DFW]
Time Start: 22:45
Time Stop: 06:20 (+1)  # Next day marker with 24-hour format
```

**Handling strategy:**
```python
# Parse time with next-day awareness
def parse_time_with_day_crossing(time_str):
    next_day = False
    
    # Check for next day markers
    if any(marker in time_str for marker in ['(+1)', '(Next Day)']):
        next_day = True
        time_str = re.sub(r'\s*[\(\[](?:\+1|Next Day)[\)\]]', '', time_str)
    
    # Parse the time
    try:
        time_obj = datetime.strptime(time_str.strip(), '%I:%M %p').time()
    except ValueError:
        try:
            time_obj = datetime.strptime(time_str.strip(), '%H:%M').time()
        except ValueError:
            return None, False
    
    return time_obj, next_day
```

## 4. Missing or Malformed Asset Labels

**What it tests:** System robustness against null parsing and unexpected asset data.

**Example data:**
```
Date: 2025-05-18
Asset: ???  # Malformed asset
Time Start: 07:05 AM
Time Stop: 03:25 PM

Date: 2025-05-18
Asset:   # Completely empty asset
Time Start: 11:15 AM
Time Stop: 02:45 PM
```

**Handling strategy:**
```python
# Safe asset and driver extraction
def extract_asset_info(asset_label):
    if not asset_label or asset_label in ['???', 'UNKNOWN', 'UNASSIGNED']:
        return {
            'asset_id': 'UNKNOWN',
            'driver_name': 'UNKNOWN',
            'employee_id': None,
            'division': None
        }
        
    # Regular extraction logic...
```

## Testing All Edge Cases Together

To generate a test file with all edge cases:

```bash
python test_data_generator.py -d 2025-05-18 -c 50 \
    --include-duplicates \
    --include-null-divisions \
    --include-overnight-shifts \
    --include-null-assets
```

This will create a robust test file that exercises all edge cases in a single test run.