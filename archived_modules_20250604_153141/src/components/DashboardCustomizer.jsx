import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import axios from 'axios';
import './DashboardCustomizer.css';

const DashboardCustomizer = () => {
  const [availableWidgets, setAvailableWidgets] = useState([]);
  const [userDashboards, setUserDashboards] = useState([]);
  const [currentDashboard, setCurrentDashboard] = useState(null);
  const [dashboardWidgets, setDashboardWidgets] = useState([]);
  const [isCustomizing, setIsCustomizing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCustomizationData();
  }, []);

  const loadCustomizationData = async () => {
    try {
      const [widgetsRes, dashboardsRes] = await Promise.all([
        axios.get('/api/dashboard/widgets'),
        axios.get('/api/dashboard/list')
      ]);

      setAvailableWidgets(widgetsRes.data.widgets || []);
      setUserDashboards(dashboardsRes.data.dashboards || []);
      
      // Set default dashboard if available
      const defaultDashboard = dashboardsRes.data.dashboards?.find(d => d.is_default);
      if (defaultDashboard) {
        setCurrentDashboard(defaultDashboard);
        setDashboardWidgets(defaultDashboard.widget_preferences || []);
      }
    } catch (error) {
      console.error('Error loading customization data:', error);
    } finally {
      setLoading(false);
    }
  };

  const createNewDashboard = async (name) => {
    try {
      const response = await axios.post('/api/dashboard/create', {
        name,
        layout: { grid: '12-column', responsive: true },
        widgets: []
      });

      if (response.data.success) {
        await loadCustomizationData();
        return response.data.dashboard_id;
      }
    } catch (error) {
      console.error('Error creating dashboard:', error);
    }
  };

  const addWidgetToDashboard = async (widgetType) => {
    if (!currentDashboard) return;

    const newWidget = {
      id: `${widgetType}-${Date.now()}`,
      type: widgetType,
      x: 0,
      y: dashboardWidgets.length * 3,
      width: 4,
      height: 3,
      settings: availableWidgets.find(w => w.type === widgetType)?.default_settings || {}
    };

    const updatedWidgets = [...dashboardWidgets, newWidget];
    setDashboardWidgets(updatedWidgets);

    try {
      await axios.post('/api/dashboard/widget/preferences', {
        dashboard_id: currentDashboard.id,
        widget_type: widgetType,
        preferences: {
          x: newWidget.x,
          y: newWidget.y,
          width: newWidget.width,
          height: newWidget.height,
          settings: newWidget.settings,
          visible: true
        }
      });
    } catch (error) {
      console.error('Error adding widget:', error);
    }
  };

  const updateWidgetLayout = async (widgets) => {
    if (!currentDashboard) return;

    try {
      await axios.put(`/api/dashboard/${currentDashboard.id}/layout`, {
        layout: currentDashboard.layout_config,
        widgets: widgets.map(w => ({
          type: w.type,
          x: w.x,
          y: w.y,
          width: w.width,
          height: w.height
        }))
      });
    } catch (error) {
      console.error('Error updating layout:', error);
    }
  };

  const onDragEnd = (result) => {
    if (!result.destination) return;

    const items = Array.from(dashboardWidgets);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    setDashboardWidgets(items);
    updateWidgetLayout(items);
  };

  const WidgetPreview = ({ widget, index }) => (
    <Draggable draggableId={widget.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`widget-preview ${snapshot.isDragging ? 'dragging' : ''}`}
          style={{
            ...provided.draggableProps.style,
            gridColumn: `span ${widget.width}`,
            gridRow: `span ${widget.height}`
          }}
        >
          <div className="widget-header">
            <h5>{availableWidgets.find(w => w.type === widget.type)?.name}</h5>
            <div className="widget-controls">
              <button className="btn btn-sm btn-outline-primary">
                <i className="fas fa-cog"></i>
              </button>
              <button 
                className="btn btn-sm btn-outline-danger"
                onClick={() => removeWidget(widget.id)}
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
          </div>
          <div className="widget-content">
            {renderWidgetContent(widget.type)}
          </div>
        </div>
      )}
    </Draggable>
  );

  const renderWidgetContent = (widgetType) => {
    switch (widgetType) {
      case 'fleet_overview':
        return (
          <div className="widget-demo-content">
            <div className="metric-row">
              <div className="metric">
                <span className="value">738</span>
                <span className="label">Total Assets</span>
              </div>
              <div className="metric">
                <span className="value">614</span>
                <span className="label">Active</span>
              </div>
            </div>
          </div>
        );
      case 'attendance_summary':
        return (
          <div className="widget-demo-content">
            <div className="metric-row">
              <div className="metric">
                <span className="value">6</span>
                <span className="label">On Time</span>
              </div>
              <div className="metric">
                <span className="value">2</span>
                <span className="label">Late</span>
              </div>
            </div>
          </div>
        );
      case 'revenue_metrics':
        return (
          <div className="widget-demo-content">
            <div className="metric-row">
              <div className="metric">
                <span className="value">$2.0M</span>
                <span className="label">YTD Revenue</span>
              </div>
            </div>
          </div>
        );
      case 'predictive_alerts':
        return (
          <div className="widget-demo-content">
            <div className="alert-item critical">
              <span>D-26: High Risk</span>
            </div>
            <div className="alert-item warning">
              <span>RAM-03: Maintenance Due</span>
            </div>
          </div>
        );
      default:
        return <div className="widget-demo-content">Widget Content</div>;
    }
  };

  const removeWidget = (widgetId) => {
    const updatedWidgets = dashboardWidgets.filter(w => w.id !== widgetId);
    setDashboardWidgets(updatedWidgets);
    updateWidgetLayout(updatedWidgets);
  };

  if (loading) {
    return (
      <div className="customizer-loading">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p>Loading dashboard customization...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-customizer">
      <div className="customizer-header">
        <div className="header-left">
          <h2><i className="fas fa-th-large me-2"></i>Dashboard Customizer</h2>
          <p>Personalize your Fort Worth operations dashboard</p>
        </div>
        <div className="header-right">
          <button 
            className="btn btn-primary me-2"
            onClick={() => setIsCustomizing(!isCustomizing)}
          >
            {isCustomizing ? 'Save Layout' : 'Customize Layout'}
          </button>
          <button 
            className="btn btn-outline-secondary"
            onClick={() => loadCustomizationData()}
          >
            <i className="fas fa-refresh"></i>
          </button>
        </div>
      </div>

      <div className="customizer-content">
        {isCustomizing && (
          <div className="widget-palette">
            <h4>Available Widgets</h4>
            <div className="widget-list">
              {availableWidgets.map(widget => (
                <div 
                  key={widget.type}
                  className="widget-item"
                  onClick={() => addWidgetToDashboard(widget.type)}
                >
                  <i className="fas fa-plus-circle"></i>
                  <span>{widget.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="dashboard-preview">
          <DragDropContext onDragEnd={onDragEnd}>
            <Droppable droppableId="dashboard">
              {(provided) => (
                <div
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  className="dashboard-grid"
                >
                  {dashboardWidgets.map((widget, index) => (
                    <WidgetPreview key={widget.id} widget={widget} index={index} />
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </div>
      </div>

      {userDashboards.length > 0 && (
        <div className="dashboard-selector">
          <h4>My Dashboards</h4>
          <div className="dashboard-list">
            {userDashboards.map(dashboard => (
              <div 
                key={dashboard.id}
                className={`dashboard-item ${currentDashboard?.id === dashboard.id ? 'active' : ''}`}
                onClick={() => {
                  setCurrentDashboard(dashboard);
                  setDashboardWidgets(dashboard.widget_preferences || []);
                }}
              >
                <span>{dashboard.name}</span>
                {dashboard.is_default && <span className="badge bg-primary">Default</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardCustomizer;