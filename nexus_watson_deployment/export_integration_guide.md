# Intelligence Export Integration Guide

## Available Export Formats

### 1. JSON Export (`/api/export/json`)
Complete intelligence data in JSON format for programmatic integration.

### 2. CSV Export (`/api/export/csv`)
Flattened metrics in CSV format for spreadsheet analysis.

### 3. XML Export (`/api/export/xml`)
Structured XML format for enterprise systems integration.

### 4. Widget Configuration (`/api/export/widget-config`)
Pre-configured widget settings for dashboard platforms.

### 5. Dashboard Bundle (`/api/export/dashboard-bundle`)
Complete ZIP package with data, configurations, and integration guides.

## Real-time API Endpoints

```
GET /api/status                    - System status
GET /api/fleet-data                - Fleet operational data  
GET /api/export/full-intelligence  - Complete intelligence export
```

## Dashboard Platform Integration

### Grafana
1. Add data source: Web API
2. URL: `https://your-app.run.app/api/export/full-intelligence`
3. Import provided dashboard configuration

### Tableau
1. Connect to Web Data Connector
2. Use API endpoint URL
3. Configure refresh interval: 5 minutes

### Power BI
1. Get Data > Web
2. Enter API endpoint URL
3. Set up automatic refresh

## Data Structure

```json
{
  "metadata": {
    "export_timestamp": "2025-06-10T22:30:00",
    "data_version": "2.1.0",
    "accuracy_score": 99.2
  },
  "operational_data": {
    "fleet_status": {
      "total_assets": 47,
      "operational": 43,
      "efficiency_percentage": 97.3
    },
    "financial_metrics": {
      "daily_revenue": 52340.00,
      "cost_savings_ytd": 347320.00,
      "roi_percentage": 24.8
    }
  }
}
```

## Integration Examples

### JavaScript Fetch
```javascript
fetch('/api/export/full-intelligence')
  .then(response => response.json())
  .then(data => {
    // Use intelligence data
    console.log('Fleet Efficiency:', data.operational_data.fleet_status.efficiency_percentage);
  });
```

### Python Integration
```python
import requests

response = requests.get('https://your-app.run.app/api/export/full-intelligence')
data = response.json()
fleet_efficiency = data['operational_data']['fleet_status']['efficiency_percentage']
```

## Refresh Rates
- Real-time data: 2-minute maximum lag
- Recommended refresh: 5 minutes
- API rate limit: 1000 requests/hour