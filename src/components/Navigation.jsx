import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Navigation() {
  return (
    <nav className="navigation">
      <div className="nav-header">
        <h1 className="nav-logo">TRAXOVO</h1>
        <span className="nav-subtitle">Fleet Intelligence</span>
      </div>
      
      <div className="nav-links">
        <NavLink 
          to="/dashboard" 
          className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}
        >
          📊 Dashboard
        </NavLink>
        
        <NavLink 
          to="/attendance" 
          className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}
        >
          👥 Attendance
        </NavLink>
        
        <NavLink 
          to="/billing" 
          className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}
        >
          💰 Billing
        </NavLink>
        
        <NavLink 
          to="/assets" 
          className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}
        >
          🚛 Assets
        </NavLink>
        
        <NavLink 
          to="/watson-admin" 
          className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}
        >
          ⚙️ Watson Admin
        </NavLink>
        
        <NavLink 
          to="/safe-mode" 
          className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}
        >
          🛡️ Safe Mode
        </NavLink>
      </div>
      
      <div className="nav-footer">
        <div className="status-indicator">
          <span className="status-dot active"></span>
          <span>GAUGE Connected</span>
        </div>
      </div>
    </nav>
  );
}