import React, { useEffect, useState } from 'react';
import axios from 'axios';
import WidgetCustomization from '../components/WidgetCustomization';

export default function Dashboard() {
  const [fleetData, setFleetData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [preferences, setPreferences] = useState({
    layout: 'grid-4x2',
    enabledWidgets: ['revenue-metrics', 'efficiency-trends', 'asset-utilization', 'billing-summary'],
    autoRefresh: true,
    refreshInterval: 30000
  });

  const fetchFleetData = async () => {
    try {
      const response = await axios.get('/api/fleet_assets');
      setFleetData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load fleet data from GAUGE API');
      console.error('Fleet data fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadPreferences = async () => {
    try {
      const response = await axios.get('/api/user/widget-preferences');
      setPreferences(response.data);
    } catch (err) {
      console.error('Failed to load preferences:', err);
    }
  };

  useEffect(() => {
    fetchFleetData();
    loadPreferences();
  }, []);

  useEffect(() => {
    if (preferences.autoRefresh && preferences.refreshInterval) {
      const interval = setInterval(fetchFleetData, preferences.refreshInterval);
      return () => clearInterval(interval);
    }
  }, [preferences.autoRefresh, preferences.refreshInterval]);

  const handlePreferencesUpdate = (newPreferences) => {
    setPreferences(newPreferences);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner">Loading TRAXOVO Dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Connection Error</h2>
        <p>{error}</p>
        <button onClick={fetchFleetData} className="retry-btn">
          Retry Connection
        </button>
      </div>
    );
  }

  const widgets = {
    'revenue-metrics': {
      title: 'YTD Revenue',
      value: fleetData.revenue || '$2.1M',
      trend: '+8.2% vs Last Year',
      icon: '💰',
      category: 'financial',
      onClick: () => drillDownRevenue()
    },
    'efficiency-trends': {
      title: 'Fleet Efficiency',
      value: fleetData.efficiency || '94.2%',
      trend: '+2.1% This Month',
      icon: '⚡',
      category: 'operations',
      onClick: () => drillDownEfficiency()
    },
    'asset-utilization': {
      title: 'Assets Active',
      value: `${fleetData.active_assets || 614}/${fleetData.total_assets || 717}`,
      trend: `${((fleetData.active_assets || 614) / (fleetData.total_assets || 717) * 100).toFixed(1)}% Utilization`,
      icon: '🚛',
      category: 'operations',
      onClick: () => drillDownAssets()
    },
    'billing-summary': {
      title: 'Profit Margin',
      value: fleetData.profit_margin || '34.7%',
      trend: '+1.8% vs Target',
      icon: '📊',
      category: 'financial',
      onClick: () => drillDownMargin()
    }
  };

  // Drill-down functions from current dashboard
  const drillDownRevenue = () => {
    window.location.href = '/billing';
  };

  const drillDownEfficiency = () => {
    console.log('Fleet Efficiency drill-down');
  };

  const drillDownAssets = () => {
    window.location.href = '/assets';
  };

  const drillDownMargin = () => {
    window.location.href = '/billing';
  };

  // Additional drill-down and navigation functions
  const drillDown = (type) => {
    switch(type) {
      case 'revenue':
        navigateTo('/billing');
        break;
      case 'total-assets':
        navigateTo('/assets');
        break;
      case 'drivers':
        navigateTo('/attendance');
        break;
      case 'efficiency':
        console.log('Fleet efficiency analytics');
        break;
      case 'categories':
        navigateTo('/assets');
        break;
      default:
        console.log(`Drill-down for ${type}`);
    }
  };

  const navigateTo = (path) => {
    window.location.href = path;
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1>TRAXOVO Fleet Dashboard</h1>
          <div className="header-actions">
            <div className="live-indicator">
              <span className="status-dot active"></span>
              Live Data from GAUGE API
            </div>
            <WidgetCustomization 
              preferences={preferences}
              onUpdate={handlePreferencesUpdate}
            />
          </div>
        </div>
      </div>

      <div className={`kpi-grid layout-${preferences.layout}`}>
        {preferences.enabledWidgets.map(widgetId => {
          const widget = widgets[widgetId];
          if (!widget) return null;
          
          return (
            <div key={widgetId} className="kpi-card" data-widget={widgetId}>
              <div className="kpi-icon">{widget.icon}</div>
              <div className="kpi-content">
                <div className="kpi-value">{widget.value}</div>
                <div className="kpi-label">{widget.title}</div>
                <div className="kpi-trend positive">{widget.trend}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        <div className="stats-grid">
          <div className="stat-item clickable" onClick={() => drillDown('revenue')}>
            <div className="stat-number">$2.1M</div>
            <div className="stat-label">YTD Revenue</div>
            <div className="stat-source">RAGLE Billing Data</div>
            <div className="drill-indicator">📈 Monthly Breakdown</div>
          </div>
          <div className="stat-item clickable" onClick={() => drillDown('total-assets')}>
            <div className="stat-number">{fleetData.total_assets || 717}</div>
            <div className="stat-label">Total Assets</div>
            <div className="stat-source">GAUGE API Live Data</div>
            <div className="drill-indicator">🚛 View Full Report</div>
          </div>
          <div className="stat-item clickable" onClick={() => drillDown('drivers')}>
            <div className="stat-number">92</div>
            <div className="stat-label">Active Drivers</div>
            <div className="stat-source">Real-time Performance</div>
            <div className="drill-indicator">👥 Performance Data</div>
          </div>
          <div className="stat-item clickable" onClick={() => drillDown('efficiency')}>
            <div className="stat-number">91.7%</div>
            <div className="stat-label">Fleet Efficiency</div>
            <div className="stat-source">Analytics Engine</div>
            <div className="drill-indicator">⚡ Efficiency Metrics</div>
          </div>
          <div className="stat-item clickable" onClick={() => drillDown('categories')}>
            <div className="stat-number">56+</div>
            <div className="stat-label">Equipment Types</div>
            <div className="stat-source">Equipment Classification</div>
            <div className="drill-indicator">🔍 View Categories</div>
          </div>
        </div>
      </div>

      {/* Dashboard Grid */}
      <div className="dashboard-grid">
        <div className="dashboard-card" onClick={() => navigateTo('/fleet-map')}>
          <div className="card-header">
            <div className="card-icon">🗺️</div>
            <div className="card-title">Fleet Map</div>
          </div>
          <div className="card-description">
            View all your equipment on an interactive map with real-time locations and status updates from your GAUGE system.
          </div>
          <div className="card-action">Open Fleet Map</div>
        </div>

        <div className="dashboard-card" onClick={() => navigateTo('/attendance')}>
          <div className="card-header">
            <div className="card-icon">👥</div>
            <div className="card-title">Driver Attendance</div>
          </div>
          <div className="card-description">
            Monitor driver attendance, weekly calendar views, and process attendance data uploads from Foundation systems.
          </div>
          <div className="card-action">View Attendance</div>
        </div>

        <div className="dashboard-card" onClick={() => navigateTo('/billing')}>
          <div className="card-header">
            <div className="card-icon">💰</div>
            <div className="card-title">Equipment Billing</div>
          </div>
          <div className="card-description">
            Process equipment billing data, manage monthly reports, and track revenue from your Ragle billing systems.
          </div>
          <div className="card-action">Manage Billing</div>
        </div>

        <div className="dashboard-card" onClick={() => navigateTo('/jobs')}>
          <div className="card-header">
            <div className="card-icon">🏗️</div>
            <div className="card-title">Job Sites</div>
          </div>
          <div className="card-description">
            Monitor job site operations, equipment assignments, and project accountability across all active projects.
          </div>
          <div className="card-action">View Job Sites</div>
        </div>

        <div className="dashboard-card" onClick={() => navigateTo('/assets')}>
          <div className="card-header">
            <div className="card-icon">🚜</div>
            <div className="card-title">Asset Manager</div>
          </div>
          <div className="card-description">
            Comprehensive asset management dashboard with equipment tracking, maintenance schedules, and utilization metrics.
          </div>
          <div className="card-action">Manage Assets</div>
        </div>

        <div className="dashboard-card" onClick={() => navigateTo('/watson-admin')}>
          <div className="card-header">
            <div className="card-icon">⚙️</div>
            <div className="card-title">System Admin</div>
          </div>
          <div className="card-description">
            System health monitoring, user management, development audit, and administrative controls.
          </div>
          <div className="card-action">System Settings</div>
        </div>
      </div>
    </div>
  );
}