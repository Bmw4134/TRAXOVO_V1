import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const GPSAssetMap = () => {
  const [assets, setAssets] = useState([]);
  const [filteredAssets, setFilteredAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [assetDetails, setAssetDetails] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ active: 0, total: 0, coverage: 0 });
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);

  // Load Leaflet dynamically
  useEffect(() => {
    const loadLeaflet = async () => {
      if (!window.L) {
        // Load Leaflet CSS
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(link);

        // Load Leaflet JS
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.onload = () => initializeMap();
        document.head.appendChild(script);
      } else {
        initializeMap();
      }
    };

    loadLeaflet();
    loadAssets();
  }, []);

  const initializeMap = () => {
    if (mapRef.current && window.L && !mapInstance.current) {
      mapInstance.current = window.L.map(mapRef.current, {
        zoomControl: false
      }).setView([32.7767, -96.7970], 10);

      // Dark theme tile layer
      window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
      }).addTo(mapInstance.current);

      // Add zoom control to bottom right
      window.L.control.zoom({ position: 'bottomright' }).addTo(mapInstance.current);
    }
  };

  const loadAssets = async () => {
    try {
      const response = await axios.get('/api/live-assets');
      const assetData = response.data;
      setAssets(assetData);
      setFilteredAssets(assetData);
      updateStats(assetData);
      displayAssetsOnMap(assetData);
      setLoading(false);
    } catch (error) {
      console.error('Error loading assets:', error);
      setLoading(false);
    }
  };

  const updateStats = (assetData) => {
    const activeAssets = assetData.filter(a => a.active).length;
    const totalAssets = assetData.length;
    const withGPS = assetData.filter(a => a.lat && a.lng).length;
    const coverage = Math.round((withGPS / totalAssets) * 100);

    setStats({
      active: activeAssets,
      total: totalAssets,
      coverage: coverage
    });
  };

  const displayAssetsOnMap = (assetData) => {
    if (!mapInstance.current || !window.L) return;

    // Clear existing markers
    markersRef.current.forEach(marker => mapInstance.current.removeLayer(marker));
    markersRef.current = [];

    assetData.forEach(asset => {
      if (asset.lat && asset.lng) {
        const marker = createAssetMarker(asset);
        markersRef.current.push(marker);
        marker.addTo(mapInstance.current);
      }
    });
  };

  const createAssetMarker = (asset) => {
    const color = asset.active ? '#46d160' : '#ea0027';
    const icon = window.L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          background: ${color};
          width: 12px;
          height: 12px;
          border-radius: 50%;
          border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        "></div>
      `,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });

    const marker = window.L.marker([asset.lat, asset.lng], { icon });
    
    marker.bindPopup(`
      <div style="color: #333; font-family: Inter, sans-serif;">
        <strong>${asset.id}</strong><br>
        ${asset.label}<br>
        <small>${asset.location}</small><br>
        <button onclick="window.showAssetDetails('${asset.id}')" 
                style="margin-top: 8px; padding: 4px 8px; background: #0079d3; color: white; border: none; border-radius: 4px; cursor: pointer;">
          View Details
        </button>
      </div>
    `);

    marker.on('click', () => {
      selectAsset(asset.id);
    });

    return marker;
  };

  const selectAsset = (assetId) => {
    setSelectedAsset(assetId);
    const asset = assets.find(a => a.id === assetId);
    if (asset && asset.lat && asset.lng && mapInstance.current) {
      mapInstance.current.setView([asset.lat, asset.lng], 15);
    }
  };

  const filterAssets = (statusFilter, categoryFilter, assetData = assets) => {
    const filtered = assetData.filter(asset => {
      const statusMatch = statusFilter === 'all' || 
        (statusFilter === 'active' && asset.active) ||
        (statusFilter === 'inactive' && !asset.active);
      
      const categoryMatch = categoryFilter === 'all' || 
        asset.category === categoryFilter;
      
      return statusMatch && categoryMatch;
    });

    setFilteredAssets(filtered);
    displayAssetsOnMap(filtered);
  };

  const handleStatusFilter = (filter) => {
    setStatusFilter(filter);
    filterAssets(filter, categoryFilter);
  };

  const handleCategoryFilter = (filter) => {
    setCategoryFilter(filter);
    filterAssets(statusFilter, filter);
  };

  const showAssetDetails = async (assetId) => {
    try {
      const response = await axios.get(`/api/asset-details/${assetId}`);
      setAssetDetails(response.data);
      setShowModal(true);
      setActiveTab('overview');
    } catch (error) {
      console.error('Error loading asset details:', error);
    }
  };

  // Make showAssetDetails available globally for popup buttons
  useEffect(() => {
    window.showAssetDetails = showAssetDetails;
    return () => {
      delete window.showAssetDetails;
    };
  }, []);

  const closeModal = () => {
    setShowModal(false);
    setAssetDetails(null);
  };

  const refreshData = () => {
    setLoading(true);
    loadAssets();
  };

  const centerMap = () => {
    if (mapInstance.current && markersRef.current.length > 0) {
      const group = new window.L.featureGroup(markersRef.current);
      mapInstance.current.fitBounds(group.getBounds());
    }
  };

  return (
    <div className="gps-asset-map">
      <style jsx>{`
        .gps-asset-map {
          display: flex;
          height: 100vh;
          background: #0f1419;
          color: #d7dadc;
          font-family: 'Inter', sans-serif;
        }

        .sidebar {
          width: 380px;
          background: #1a1a1b;
          border-right: 1px solid #343536;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .sidebar-header {
          padding: 20px;
          border-bottom: 1px solid #343536;
          background: #272729;
        }

        .sidebar-title {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 8px;
          color: #d7dadc;
        }

        .sidebar-subtitle {
          font-size: 14px;
          color: #818384;
        }

        .stats-bar {
          display: flex;
          padding: 16px 20px;
          gap: 20px;
          background: #272729;
          border-bottom: 1px solid #343536;
        }

        .stat-item {
          text-align: center;
          flex: 1;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 600;
          color: #d7dadc;
          display: block;
        }

        .stat-label {
          font-size: 12px;
          color: #818384;
          margin-top: 4px;
        }

        .filters {
          padding: 16px 20px;
          border-bottom: 1px solid #343536;
        }

        .filter-group {
          margin-bottom: 16px;
        }

        .filter-label {
          font-size: 12px;
          color: #818384;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .filter-buttons {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .filter-btn {
          padding: 6px 12px;
          background: #272729;
          border: 1px solid #343536;
          border-radius: 16px;
          font-size: 12px;
          color: #d7dadc;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .filter-btn.active {
          background: #0079d3;
          border-color: #0079d3;
          color: white;
        }

        .filter-btn:hover {
          background: #343536;
        }

        .asset-list {
          flex: 1;
          overflow-y: auto;
          padding: 12px;
        }

        .asset-item {
          background: #272729;
          border: 1px solid #343536;
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .asset-item:hover {
          border-color: #0079d3;
          transform: translateY(-1px);
        }

        .asset-item.selected {
          border-color: #0079d3;
          background: rgba(0, 121, 211, 0.1);
        }

        .asset-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .asset-id {
          font-weight: 600;
          font-size: 14px;
          color: #d7dadc;
        }

        .asset-status {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .asset-status.active { background: #46d160; }
        .asset-status.inactive { background: #ea0027; }

        .asset-details {
          font-size: 12px;
          color: #818384;
          line-height: 1.4;
        }

        .asset-location {
          margin-top: 4px;
          font-size: 11px;
          color: #818384;
        }

        .map-area {
          flex: 1;
          position: relative;
        }

        .map-container {
          width: 100%;
          height: 100%;
          background: #0f1419;
        }

        .map-controls {
          position: absolute;
          top: 20px;
          right: 20px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          z-index: 1000;
        }

        .map-control {
          background: #272729;
          border: 1px solid #343536;
          border-radius: 8px;
          padding: 8px;
          cursor: pointer;
          color: #d7dadc;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .map-control:hover {
          background: #343536;
        }

        .loading {
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 40px;
          color: #818384;
        }

        .spinner {
          width: 20px;
          height: 20px;
          border: 2px solid #343536;
          border-top: 2px solid #0079d3;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-right: 8px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .modal {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 2000;
        }

        .modal-content {
          background: #1a1a1b;
          border: 1px solid #343536;
          border-radius: 12px;
          width: 90%;
          max-width: 800px;
          max-height: 90vh;
          overflow-y: auto;
        }

        .modal-header {
          padding: 20px;
          border-bottom: 1px solid #343536;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .modal-title {
          font-size: 18px;
          font-weight: 600;
          color: #d7dadc;
        }

        .close-btn {
          background: none;
          border: none;
          color: #818384;
          font-size: 24px;
          cursor: pointer;
          padding: 4px;
        }

        .close-btn:hover {
          color: #d7dadc;
        }

        .modal-body {
          padding: 20px;
        }

        .tabs {
          display: flex;
          border-bottom: 1px solid #343536;
          margin-bottom: 20px;
        }

        .tab {
          padding: 12px 16px;
          background: none;
          border: none;
          color: #818384;
          cursor: pointer;
          border-bottom: 2px solid transparent;
          transition: all 0.2s ease;
        }

        .tab.active {
          color: #0079d3;
          border-bottom-color: #0079d3;
        }

        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 16px;
        }

        .kpi-card {
          background: #272729;
          border: 1px solid #343536;
          border-radius: 8px;
          padding: 16px;
        }

        .kpi-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .kpi-title {
          font-size: 14px;
          color: #818384;
        }

        .kpi-status {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .kpi-status.good { background: #46d160; }
        .kpi-status.fair { background: #ff8700; }
        .kpi-status.poor { background: #ea0027; }

        .kpi-value {
          font-size: 24px;
          font-weight: 600;
          color: #d7dadc;
          margin-bottom: 4px;
        }

        .kpi-description {
          font-size: 12px;
          color: #818384;
        }

        @media (max-width: 768px) {
          .sidebar {
            width: 100%;
            position: absolute;
            left: -100%;
            transition: left 0.3s ease;
            z-index: 1500;
          }

          .sidebar.open {
            left: 0;
          }

          .mobile-toggle {
            position: absolute;
            top: 20px;
            left: 20px;
            background: #272729;
            border: 1px solid #343536;
            border-radius: 8px;
            padding: 8px;
            color: #d7dadc;
            cursor: pointer;
            z-index: 1000;
          }
        }
      `}</style>

      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title">Live Asset Tracking</div>
          <div className="sidebar-subtitle">701 assets • Real-time GPS</div>
        </div>

        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-value">{stats.active}</span>
            <div className="stat-label">Active</div>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.total}</span>
            <div className="stat-label">Total</div>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.coverage}%</span>
            <div className="stat-label">Coverage</div>
          </div>
        </div>

        <div className="filters">
          <div className="filter-group">
            <div className="filter-label">Status</div>
            <div className="filter-buttons">
              <button 
                className={`filter-btn ${statusFilter === 'all' ? 'active' : ''}`}
                onClick={() => handleStatusFilter('all')}
              >
                All
              </button>
              <button 
                className={`filter-btn ${statusFilter === 'active' ? 'active' : ''}`}
                onClick={() => handleStatusFilter('active')}
              >
                Active
              </button>
              <button 
                className={`filter-btn ${statusFilter === 'inactive' ? 'active' : ''}`}
                onClick={() => handleStatusFilter('inactive')}
              >
                Inactive
              </button>
            </div>
          </div>
          <div className="filter-group">
            <div className="filter-label">Category</div>
            <div className="filter-buttons">
              <button 
                className={`filter-btn ${categoryFilter === 'all' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('all')}
              >
                All
              </button>
              <button 
                className={`filter-btn ${categoryFilter === 'Excavator' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('Excavator')}
              >
                Excavators
              </button>
              <button 
                className={`filter-btn ${categoryFilter === 'Dozer' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('Dozer')}
              >
                Dozers
              </button>
              <button 
                className={`filter-btn ${categoryFilter === 'Loader' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('Loader')}
              >
                Loaders
              </button>
            </div>
          </div>
        </div>

        <div className="asset-list">
          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              Loading assets...
            </div>
          ) : (
            filteredAssets.map(asset => (
              <div 
                key={asset.id}
                className={`asset-item ${selectedAsset === asset.id ? 'selected' : ''}`}
                onClick={() => selectAsset(asset.id)}
              >
                <div className="asset-header">
                  <div className="asset-id">{asset.id}</div>
                  <div className={`asset-status ${asset.active ? 'active' : 'inactive'}`}></div>
                </div>
                <div className="asset-details">
                  {asset.category} • {asset.hours} hours
                </div>
                <div className="asset-location">{asset.location}</div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Map Area */}
      <div className="map-area">
        <div ref={mapRef} className="map-container"></div>
        <div className="map-controls">
          <div className="map-control" onClick={refreshData}>🔄</div>
          <div className="map-control" onClick={centerMap}>🎯</div>
        </div>
      </div>

      {/* Asset Detail Modal */}
      {showModal && assetDetails && (
        <div className="modal" onClick={(e) => e.target.className === 'modal' && closeModal()}>
          <div className="modal-content">
            <div className="modal-header">
              <div className="modal-title">{selectedAsset} Details</div>
              <button className="close-btn" onClick={closeModal}>&times;</button>
            </div>
            <div className="modal-body">
              <div className="tabs">
                <button 
                  className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                  onClick={() => setActiveTab('overview')}
                >
                  Overview
                </button>
                <button 
                  className={`tab ${activeTab === 'diagnostics' ? 'active' : ''}`}
                  onClick={() => setActiveTab('diagnostics')}
                >
                  Diagnostics
                </button>
                <button 
                  className={`tab ${activeTab === 'maintenance' ? 'active' : ''}`}
                  onClick={() => setActiveTab('maintenance')}
                >
                  Maintenance
                </button>
                <button 
                  className={`tab ${activeTab === 'kpis' ? 'active' : ''}`}
                  onClick={() => setActiveTab('kpis')}
                >
                  KPIs
                </button>
              </div>

              {activeTab === 'overview' && (
                <div className="kpi-grid">
                  <div className="kpi-card">
                    <div className="kpi-title">Make & Model</div>
                    <div className="kpi-value" style={{fontSize: '16px'}}>
                      {assetDetails.basic_info?.make} {assetDetails.basic_info?.model}
                    </div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-title">Location</div>
                    <div className="kpi-value" style={{fontSize: '16px'}}>
                      {assetDetails.location_data?.location}
                    </div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-title">Engine Hours</div>
                    <div className="kpi-value" style={{fontSize: '16px'}}>
                      {assetDetails.predictive_maintenance?.engine_hours}
                    </div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-title">Status</div>
                    <div className="kpi-value" style={{fontSize: '16px'}}>
                      {assetDetails.operational_status?.status}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'diagnostics' && (
                <div className="kpi-grid">
                  <div className="kpi-card">
                    <div className="kpi-header">
                      <div className="kpi-title">Voltage</div>
                      <div className={`kpi-status ${assetDetails.diagnostics?.voltage_status?.toLowerCase()}`}></div>
                    </div>
                    <div className="kpi-value">{assetDetails.diagnostics?.voltage}V</div>
                    <div className="kpi-description">{assetDetails.diagnostics?.voltage_status}</div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-header">
                      <div className="kpi-title">Battery</div>
                      <div className={`kpi-status ${assetDetails.diagnostics?.battery_status?.toLowerCase()}`}></div>
                    </div>
                    <div className="kpi-value">{assetDetails.diagnostics?.battery_percentage}%</div>
                    <div className="kpi-description">{assetDetails.diagnostics?.battery_status}</div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-title">Health Score</div>
                    <div className="kpi-value">{assetDetails.diagnostics?.overall_health}/100</div>
                    <div className="kpi-description">Overall condition</div>
                  </div>
                </div>
              )}

              {activeTab === 'maintenance' && (
                <div className="kpi-grid">
                  <div className="kpi-card">
                    <div className="kpi-title">Next Service</div>
                    <div className="kpi-value">{assetDetails.predictive_maintenance?.next_service_hours}</div>
                    <div className="kpi-description">{assetDetails.predictive_maintenance?.hours_to_service} hours remaining</div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-title">Priority</div>
                    <div className="kpi-value">{assetDetails.predictive_maintenance?.maintenance_priority}</div>
                    <div className="kpi-description">Maintenance priority level</div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-title">Replacement</div>
                    <div className="kpi-value">{assetDetails.predictive_maintenance?.replacement_timeline}</div>
                    <div className="kpi-description">Estimated timeline</div>
                  </div>
                </div>
              )}

              {activeTab === 'kpis' && (
                <div className="kpi-grid">
                  {assetDetails.kpi_metrics?.map((kpi, index) => (
                    <div key={index} className="kpi-card">
                      <div className="kpi-header">
                        <div className="kpi-title">{kpi.title}</div>
                        <div className={`kpi-status ${kpi.status}`}></div>
                      </div>
                      <div className="kpi-value">{kpi.value}</div>
                      <div className="kpi-description">{kpi.description}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GPSAssetMap;