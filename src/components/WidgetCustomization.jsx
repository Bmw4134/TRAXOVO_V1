import React, { useState } from 'react';
import axios from 'axios';

export default function WidgetCustomization({ preferences, onUpdate }) {
  const [isOpen, setIsOpen] = useState(false);
  const [localPreferences, setLocalPreferences] = useState(preferences);

  const widgetCategories = {
    operations: [
      { id: 'efficiency-trends', name: 'Fleet Efficiency' },
      { id: 'asset-utilization', name: 'Asset Utilization' },
      { id: 'driver-performance', name: 'Driver Performance' }
    ],
    financial: [
      { id: 'revenue-metrics', name: 'Revenue Metrics' },
      { id: 'billing-summary', name: 'Billing Summary' },
      { id: 'profit-analysis', name: 'Profit Analysis' }
    ],
    analytics: [
      { id: 'predictive-maintenance', name: 'Predictive Maintenance' },
      { id: 'route-optimization', name: 'Route Optimization' },
      { id: 'fuel-analytics', name: 'Fuel Analytics' }
    ],
    external: [
      { id: 'weather-integration', name: 'Weather Data' },
      { id: 'traffic-conditions', name: 'Traffic Conditions' },
      { id: 'market-insights', name: 'Market Insights' }
    ]
  };

  const layoutOptions = [
    { id: 'grid-4x2', name: '4×2 Grid', description: 'Standard dashboard layout' },
    { id: 'grid-3x3', name: '3×3 Grid', description: 'Compact grid view' },
    { id: 'single-column', name: 'Single Column', description: 'Vertical layout' }
  ];

  const handleSave = async () => {
    try {
      await axios.post('/api/user/widget-preferences', localPreferences);
      onUpdate(localPreferences);
      setIsOpen(false);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'notification success';
      notification.textContent = 'Dashboard preferences saved successfully';
      document.body.appendChild(notification);
      
      setTimeout(() => {
        notification.remove();
      }, 3000);
    } catch (error) {
      console.error('Failed to save preferences:', error);
      
      // Show error notification
      const notification = document.createElement('div');
      notification.className = 'notification error';
      notification.textContent = 'Failed to save preferences';
      document.body.appendChild(notification);
      
      setTimeout(() => {
        notification.remove();
      }, 3000);
    }
  };

  const handleReset = () => {
    const defaultPreferences = {
      layout: 'grid-4x2',
      enabledWidgets: ['revenue-metrics', 'efficiency-trends', 'asset-utilization', 'billing-summary'],
      autoRefresh: true,
      refreshInterval: 30000
    };
    setLocalPreferences(defaultPreferences);
  };

  const toggleWidget = (widgetId) => {
    const enabledWidgets = localPreferences.enabledWidgets.includes(widgetId)
      ? localPreferences.enabledWidgets.filter(id => id !== widgetId)
      : [...localPreferences.enabledWidgets, widgetId];
    
    setLocalPreferences({
      ...localPreferences,
      enabledWidgets
    });
  };

  if (!isOpen) {
    return (
      <button 
        className="customize-btn"
        onClick={() => setIsOpen(true)}
      >
        ⚙️ Customize
      </button>
    );
  }

  return (
    <div className="customization-panel">
      <div className="customization-content">
        <div className="customization-header">
          <h3>Dashboard Customization</h3>
          <button 
            className="close-btn"
            onClick={() => setIsOpen(false)}
          >
            ×
          </button>
        </div>

        <div className="customization-body">
          <div className="customization-section">
            <h4>Layout Options</h4>
            <div className="layout-options">
              {layoutOptions.map(layout => (
                <div 
                  key={layout.id}
                  className={`layout-option ${localPreferences.layout === layout.id ? 'selected' : ''}`}
                  onClick={() => setLocalPreferences({...localPreferences, layout: layout.id})}
                >
                  <div className={`layout-preview ${layout.id}-preview`}></div>
                  <span>{layout.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="customization-section">
            <h4>Widget Selection</h4>
            {Object.entries(widgetCategories).map(([category, widgets]) => (
              <div key={category} className="widget-category">
                <h5>{category.charAt(0).toUpperCase() + category.slice(1)}</h5>
                <div className="widget-list">
                  {widgets.map(widget => (
                    <div key={widget.id} className="widget-item">
                      <input
                        type="checkbox"
                        checked={localPreferences.enabledWidgets.includes(widget.id)}
                        onChange={() => toggleWidget(widget.id)}
                      />
                      <span>{widget.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="customization-section">
            <h4>Settings</h4>
            <div className="settings-options">
              <label>
                <input
                  type="checkbox"
                  checked={localPreferences.autoRefresh}
                  onChange={(e) => setLocalPreferences({
                    ...localPreferences,
                    autoRefresh: e.target.checked
                  })}
                />
                Auto-refresh data
              </label>
              
              {localPreferences.autoRefresh && (
                <label>
                  Refresh interval:
                  <select
                    value={localPreferences.refreshInterval}
                    onChange={(e) => setLocalPreferences({
                      ...localPreferences,
                      refreshInterval: parseInt(e.target.value)
                    })}
                  >
                    <option value={15000}>15 seconds</option>
                    <option value={30000}>30 seconds</option>
                    <option value={60000}>1 minute</option>
                    <option value={300000}>5 minutes</option>
                  </select>
                </label>
              )}
            </div>
          </div>
        </div>

        <div className="customization-footer">
          <button className="btn-secondary" onClick={handleReset}>
            Reset to Default
          </button>
          <button className="btn-primary" onClick={handleSave}>
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}