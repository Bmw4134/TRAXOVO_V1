import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Attendance from './pages/Attendance';
import Billing from './pages/Billing';
import Assets from './pages/Assets';
import WatsonAdmin from './pages/WatsonAdmin';
import SafeMode from './pages/SafeMode';
import Navigation from './components/Navigation';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/attendance" element={<Attendance />} />
            <Route path="/billing" element={<Billing />} />
            <Route path="/assets" element={<Assets />} />
            <Route path="/watson-admin" element={<WatsonAdmin />} />
            <Route path="/safe-mode" element={<SafeMode />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;