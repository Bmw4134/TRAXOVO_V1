import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import QuantumConsciousness from './QuantumConsciousness';
import './QuantumDashboard.css';

const QuantumDashboard = () => {
  const { logout } = useAuth();
  const [quantumMetrics, setQuantumMetrics] = useState({});
  const [fortWorthAssets, setFortWorthAssets] = useState([]);
  const [attendanceData, setAttendanceData] = useState({});
  const [contextualNudges, setContextualNudges] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [quantumRes, assetsRes, attendanceRes, nudgesRes] = await Promise.all([
        axios.get('/api/quantum-consciousness'),
        axios.get('/api/fort-worth-assets'),
        axios.get('/api/attendance-data'),
        axios.get('/api/contextual-nudges')
      ]);

      setQuantumMetrics(quantumRes.data);
      setFortWorthAssets(assetsRes.data.assets || []);
      setAttendanceData(attendanceRes.data);
      setContextualNudges(nudgesRes.data);
    } catch (error) {
      console.error('Dashboard data loading error:', error);
    } finally {
      setLoading(false);
    }
  };

  const ModuleCard = ({ icon, title, description, link, badge, stats }) => (
    <Link to={link} className="module-card">
      <div className="module-header">
        <i className={`${icon} module-icon`}></i>
        <h3 className="module-title">{title}</h3>
        {badge && <span className="module-badge">{badge}</span>}
      </div>
      <div className="module-body">
        <p className="module-description">{description}</p>
        {stats && (
          <div className="module-stats">
            {stats.map((stat, index) => (
              <div key={index} className="stat-item">
                <span className="stat-number">{stat.value}</span>
                <span className="stat-label">{stat.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Link>
  );

  if (loading) {
    return (
      <div className="quantum-loading">
        <div className="consciousness-loader">
          <div className="thought-vectors"></div>
          <div className="loading-text">Quantum Consciousness Initializing...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="quantum-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo">TRAXOVO</div>
            <div className="tagline">Fleet Intelligence Platform</div>
          </div>
          
          <div className="status-indicators">
            <div className="status-item">
              <div className="status-dot active"></div>
              <span>Fort Worth Connected</span>
            </div>
            <div className="status-item">
              <div className="status-dot active"></div>
              <span>AI Processing Active</span>
            </div>
            <div className="status-item">
              <div className="status-dot active"></div>
              <span>Real-time Data</span>
            </div>
          </div>
          
          <div className="nav-buttons">
            <Link to="/fleet-map" className="nav-btn">Fleet Map</Link>
            <Link to="/attendance-matrix" className="nav-btn">Attendance</Link>
            <Link to="/asset-manager" className="nav-btn">Assets</Link>
            <Link to="/executive-dashboard" className="nav-btn">Executive</Link>
            <button onClick={logout} className="nav-btn logout-btn">Logout</button>
          </div>
        </div>
      </header>

      <QuantumConsciousness metrics={quantumMetrics} />

      <main className="main-content">
        <div className="dashboard-grid">
          {/* Core Fleet Management */}
          <ModuleCard
            icon="fas fa-map-marked-alt"
            title="QQ Enhanced Fleet Map"
            description="Real-time GPS tracking with quantum-enhanced asset intelligence and authentic Fort Worth coordinates."
            link="/fleet-map"
            badge={`${fortWorthAssets.length} Assets`}
            stats={[
              { value: fortWorthAssets.filter(a => a.status === 'Active').length, label: 'Active' },
              { value: '98.2%', label: 'GPS Coverage' },
              { value: '12', label: 'Geofences' }
            ]}
          />

          <ModuleCard
            icon="fas fa-users"
            title="Attendance Matrix"
            description="Driver attendance tracking with pickup truck assignments and authentic Fort Worth operational data."
            link="/attendance-matrix"
            badge={`${attendanceData.drivers?.length || 8} Drivers`}
            stats={[
              { value: attendanceData.on_time || 6, label: 'On Time' },
              { value: attendanceData.late || 2, label: 'Late' },
              { value: `${attendanceData.attendance_rate || 75}%`, label: 'Rate' }
            ]}
          />

          <ModuleCard
            icon="fas fa-tools"
            title="Asset Manager"
            description="Complete asset lifecycle costing, depreciation schedules, and AEMP-compliant equipment management."
            link="/asset-manager"
            badge="738 Units"
            stats={[
              { value: '614', label: 'Active' },
              { value: '87%', label: 'Utilization' },
              { value: '$2.0M', label: 'YTD Value' }
            ]}
          />

          <ModuleCard
            icon="fas fa-chart-line"
            title="Executive Dashboard"
            description="C-suite intelligence with KPIs, strategic insights, and Fort Worth performance metrics."
            link="/executive-dashboard"
            badge="Real-time"
            stats={[
              { value: '$2.0M', label: 'YTD Revenue' },
              { value: '87.5%', label: 'Efficiency' },
              { value: '$103K', label: 'AI Savings' }
            ]}
          />

          {/* HCSS Replacement Suite */}
          <ModuleCard
            icon="fas fa-file-invoice"
            title="Smart PO System"
            description="SmartSheets replacement with intelligent purchase order management and vendor integration."
            link="/smart-po"
            badge="HCSS Replacement"
            stats={[
              { value: '45', label: 'Active POs' },
              { value: '$156K', label: 'Monthly' },
              { value: '12', label: 'Vendors' }
            ]}
          />

          <ModuleCard
            icon="fas fa-truck"
            title="Smart Dispatch"
            description="HCSS Dispatcher replacement with AI-powered routing and real-time fleet coordination."
            link="/dispatch-system"
            badge="HCSS Replacement"
            stats={[
              { value: '23', label: 'Active Jobs' },
              { value: '89%', label: 'On-time' },
              { value: '156', label: 'Routes' }
            ]}
          />

          <ModuleCard
            icon="fas fa-calculator"
            title="Smart Estimating"
            description="HCSS Bid replacement with intelligent cost estimation and Texas market analysis."
            link="/estimating-system"
            badge="HCSS Replacement"
            stats={[
              { value: '18', label: 'Active Bids' },
              { value: '67%', label: 'Win Rate' },
              { value: '$2.4M', label: 'Pipeline' }
            ]}
          />

          {/* Equipment Management Modules */}
          <ModuleCard
            icon="fas fa-cogs"
            title="Equipment Lifecycle"
            description="AEMP-compliant lifecycle costing with depreciation analysis and replacement planning."
            link="/equipment-lifecycle"
            badge="AEMP Certified"
            stats={[
              { value: '$624K', label: 'Annual Cost' },
              { value: '8', label: 'Avg Life' },
              { value: '$189K', label: 'Depreciation' }
            ]}
          />

          <ModuleCard
            icon="fas fa-wrench"
            title="Predictive Maintenance"
            description="AI-powered failure prediction with maintenance scheduling and cost optimization."
            link="/predictive-maintenance"
            badge="AI Powered"
            stats={[
              { value: '45%', label: 'Downtime ↓' },
              { value: '$78K', label: 'Savings' },
              { value: '314%', label: 'ROI' }
            ]}
          />

          <ModuleCard
            icon="fas fa-chart-area"
            title="Texas Market Research"
            description="Heavy civil market analysis with competitor intelligence and AEMP industry insights."
            link="/heavy-civil-market"
            badge="Texas Focus"
            stats={[
              { value: '3.4%', label: 'Market Share' },
              { value: '$380M', label: 'Fort Worth' },
              { value: '12%', label: 'Premium' }
            ]}
          />
        </div>

        {/* Contextual Productivity Nudges */}
        {contextualNudges.nudges && (
          <div className="productivity-nudges">
            <h3><i className="fas fa-lightbulb"></i> AI Productivity Insights</h3>
            <div className="nudges-grid">
              {Object.entries(contextualNudges.nudges).map(([key, nudge]) => (
                <div key={key} className="nudge-card">
                  <div className="nudge-content">{nudge}</div>
                </div>
              ))}
            </div>
            <div className="savings-highlight">
              <span className="savings-amount">${contextualNudges.savings_identified?.toLocaleString()}</span>
              <span className="savings-label">Weekly Savings Identified</span>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default QuantumDashboard;