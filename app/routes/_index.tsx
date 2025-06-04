import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData, useFetcher, useRevalidator } from "@remix-run/react";
import { useState, useEffect } from "react";
import { executeQQAutomation, getQQMetrics } from "~/lib/qq-intelligence";

export async function loader({ request }: LoaderFunctionArgs) {
  const gaugeApiKey = process.env.GAUGE_API_KEY;
  const gaugeApiUrl = process.env.GAUGE_API_URL;
  
  if (!gaugeApiKey || !gaugeApiUrl) {
    throw new Response("GAUGE API credentials required", { status: 500 });
  }

  const qqMetrics = await getQQMetrics();
  const assets = await fetch(`${gaugeApiUrl}/assets`, {
    headers: {
      'Authorization': `Bearer ${gaugeApiKey}`,
      'Content-Type': 'application/json'
    }
  }).then(r => r.json()).catch(() => []);

  return json({
    qqMetrics,
    assets,
    location: "Fort Worth, TX 76180",
    timestamp: new Date().toISOString()
  });
}

export default function QQDashboard() {
  const { qqMetrics, assets } = useLoaderData<typeof loader>();
  const automationFetcher = useFetcher();
  const revalidator = useRevalidator();

  useEffect(() => {
    const interval = setInterval(() => {
      revalidator.revalidate();
    }, 5000);
    return () => clearInterval(interval);
  }, [revalidator]);

  return (
    <div className="qq-dashboard">
      <header className="dashboard-header">
        <h1>TRAXOVO QQ Intelligence</h1>
        <div className="metrics-summary">
          <div>Consciousness Level: {qqMetrics.consciousness.level}</div>
          <div>ASI Score: {qqMetrics.asi.excellence_score}</div>
          <div>Assets: {assets.length}</div>
        </div>
      </header>
      
      <div className="intelligence-panels">
        <div className="consciousness-panel">
          <h2>Quantum Consciousness</h2>
          <div className="consciousness-visualization">
            {qqMetrics.consciousness.thought_vectors.map((vector, i) => (
              <div 
                key={i} 
                className="thought-vector"
                style={{
                  transform: `translateX(${vector.x}px) translateY(${vector.y}px)`,
                  opacity: vector.intensity
                }}
              />
            ))}
          </div>
        </div>
        
        <div className="asi-panel">
          <h2>ASI Excellence</h2>
          <div className="asi-metrics">
            <div>Excellence Score: {qqMetrics.asi.excellence_score}</div>
            <div>Autonomous Decisions: {qqMetrics.asi.autonomous_decisions}</div>
            <div>Error Prevention: {qqMetrics.asi.error_prevention_rate}%</div>
          </div>
        </div>
      </div>
      
      <div className="fleet-section">
        <h2>Fleet Assets</h2>
        <div className="assets-grid">
          {assets.map((asset) => (
            <div key={asset.id} className="asset-card">
              <div>{asset.id}</div>
              <div>{asset.name}</div>
              <div>Status: {asset.status}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}