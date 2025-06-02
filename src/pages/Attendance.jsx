import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function Attendance() {
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAttendance = async () => {
      try {
        const response = await axios.get('/api/attendance');
        setAttendance(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to load attendance data from authentic sources');
        console.error('Attendance fetch failed:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAttendance();
  }, []);

  if (loading) {
    return <div className="loading-container">Loading driver attendance data...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Connection Error</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="attendance-page">
      <h2 className="page-title">Driver Attendance Matrix</h2>
      <div className="attendance-grid">
        {attendance.length > 0 ? (
          attendance.map(driver => (
            <div key={driver.id} className="attendance-card">
              <div className="driver-info">
                <h3>{driver.name}</h3>
                <span className={`status ${driver.status.toLowerCase()}`}>
                  {driver.status}
                </span>
              </div>
              <div className="attendance-details">
                <p>Clock In: {driver.clock_in || 'Not recorded'}</p>
                <p>Clock Out: {driver.clock_out || 'In progress'}</p>
                <p>Hours: {driver.hours || 'Calculating...'}</p>
              </div>
            </div>
          ))
        ) : (
          <div className="no-data">
            <p>No attendance data available from authentic sources</p>
          </div>
        )}
      </div>
    </div>
  );
}