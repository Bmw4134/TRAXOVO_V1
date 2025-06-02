import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function Billing() {
  const [billing, setBilling] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBilling = async () => {
      try {
        const response = await axios.get('/api/billing');
        setBilling(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to load billing data from RAGLE systems');
        console.error('Billing fetch failed:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchBilling();
  }, []);

  if (loading) {
    return <div className="loading-container">Loading billing intelligence from RAGLE...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Connection Error</h2>
        <p>{error}</p>
        <p>Please ensure RAGLE billing system credentials are configured.</p>
      </div>
    );
  }

  return (
    <div className="billing-page">
      <h2 className="page-title">Billing Intelligence</h2>
      <div className="billing-summary">
        <div className="summary-card">
          <h3>Monthly Revenue</h3>
          <span className="amount">$2.1M</span>
        </div>
        <div className="summary-card">
          <h3>Outstanding Invoices</h3>
          <span className="amount">{billing.filter(item => item.status === 'pending').length}</span>
        </div>
      </div>
      
      <div className="billing-grid">
        {billing.length > 0 ? (
          billing.map(item => (
            <div key={item.invoice_id} className="billing-card">
              <div className="billing-header">
                <h3>{item.client}</h3>
                <span className={`status ${item.status}`}>
                  {item.status}
                </span>
              </div>
              <div className="billing-details">
                <p>Amount: <strong>${item.amount}</strong></p>
                <p>Invoice: {item.invoice_id}</p>
                <p>Date: {item.date}</p>
              </div>
            </div>
          ))
        ) : (
          <div className="no-data">
            <p>No billing data available from RAGLE systems</p>
            <p>Contact administrator to verify RAGLE connection credentials</p>
          </div>
        )}
      </div>
    </div>
  );
}