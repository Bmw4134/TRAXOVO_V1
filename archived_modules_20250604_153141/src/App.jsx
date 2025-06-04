import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import QuantumDashboard from './components/QuantumDashboard';
import FleetMap from './components/FleetMap';
import AttendanceMatrix from './components/AttendanceMatrix';
import AssetManager from './components/AssetManager';
import ExecutiveDashboard from './components/ExecutiveDashboard';
import SmartPOSystem from './components/SmartPOSystem';
import DispatchSystem from './components/DispatchSystem';
import EstimatingSystem from './components/EstimatingSystem';
import EquipmentLifecycle from './components/EquipmentLifecycle';
import PredictiveMaintenance from './components/PredictiveMaintenance';
import HeavyCivilMarket from './components/HeavyCivilMarket';
import DemoAccess from './components/DemoAccess';
import './App.css';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="loading-container">
        <div className="quantum-loader">
          <div className="loader-ring"></div>
          <div className="loader-text">TRAXOVO Quantum Loading...</div>
        </div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/demo" element={<DemoAccess />} />
            
            {/* Protected Routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <QuantumDashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/quantum-dashboard" element={
              <ProtectedRoute>
                <QuantumDashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/fleet-map" element={
              <ProtectedRoute>
                <FleetMap />
              </ProtectedRoute>
            } />
            
            <Route path="/attendance-matrix" element={
              <ProtectedRoute>
                <AttendanceMatrix />
              </ProtectedRoute>
            } />
            
            <Route path="/asset-manager" element={
              <ProtectedRoute>
                <AssetManager />
              </ProtectedRoute>
            } />
            
            <Route path="/executive-dashboard" element={
              <ProtectedRoute>
                <ExecutiveDashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/smart-po" element={
              <ProtectedRoute>
                <SmartPOSystem />
              </ProtectedRoute>
            } />
            
            <Route path="/dispatch-system" element={
              <ProtectedRoute>
                <DispatchSystem />
              </ProtectedRoute>
            } />
            
            <Route path="/estimating-system" element={
              <ProtectedRoute>
                <EstimatingSystem />
              </ProtectedRoute>
            } />
            
            <Route path="/equipment-lifecycle" element={
              <ProtectedRoute>
                <EquipmentLifecycle />
              </ProtectedRoute>
            } />
            
            <Route path="/predictive-maintenance" element={
              <ProtectedRoute>
                <PredictiveMaintenance />
              </ProtectedRoute>
            } />
            
            <Route path="/heavy-civil-market" element={
              <ProtectedRoute>
                <HeavyCivilMarket />
              </ProtectedRoute>
            } />
            
            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;