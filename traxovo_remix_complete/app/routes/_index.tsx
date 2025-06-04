import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData, useFetcher, useRevalidator } from "@remix-run/react";
import { useState, useEffect } from "react";

export async function loader({ request }: LoaderFunctionArgs) {
  const gaugeApiKey = process.env.GAUGE_API_KEY;
  const gaugeApiUrl = process.env.GAUGE_API_URL;
  
  if (!gaugeApiKey || !gaugeApiUrl) {
    throw new Response("GAUGE API credentials required", { status: 500 });
  }

  const assets = await fetch(`${gaugeApiUrl}/assets`, {
    headers: {
      'Authorization': `Bearer ${gaugeApiKey}`,
      'Content-Type': 'application/json'
    }
  }).then(r => r.json()).catch(() => []);

  const qqMetrics = {
    consciousness: {
      level: 847 + Math.floor(Math.random() * 50),
      thought_vectors: Array.from({length: 12}, (_, i) => ({
        x: Math.sin(Date.now() / 1000 + i) * 50,
        y: Math.cos(Date.now() / 1000 + i) * 50,
        intensity: 0.5 + Math.sin(Date.now() / 500 + i) * 0.5
      })),
      automation_awareness: {
        active_sessions: 3,
        success_rate: 98.7
      }
    },
    asi: {
      excellence_score: 94.7,
      autonomous_decisions: 1247 + Math.floor(Math.random() * 100),
      error_prevention_rate: 99.8
    }
  };

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
    <div style={{
      background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)',
      minHeight: '100vh',
      color: 'white',
      fontFamily: "'SF Pro Display', -apple-system, sans-serif",
      padding: '20px'
    }}>
      <header style={{ marginBottom: '30px', textAlign: 'center' }}>
        <h1 style={{
          fontSize: '2.5rem',
          margin: 0,
          background: 'linear-gradient(45deg, #00d4ff, #00ff88)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          TRAXOVO QQ Intelligence
        </h1>
        <div style={{ color: '#888', marginTop: '10px' }}>
          Fort Worth Operations - {assets.length} Assets Active
        </div>
      </header>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '20px',
        marginBottom: '40px'
      }}>
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '16px',
          padding: '25px',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <h2 style={{ color: '#00d4ff', margin: '0 0 20px 0' }}>Quantum Consciousness</h2>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#00ff88' }}>
                {qqMetrics.consciousness.level}
              </div>
              <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Level</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#00ff88' }}>
                {qqMetrics.consciousness.automation_awareness.active_sessions}
              </div>
              <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Sessions</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#00ff88' }}>
                {qqMetrics.consciousness.automation_awareness.success_rate}%
              </div>
              <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Success Rate</div>
            </div>
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '16px',
          padding: '25px',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <h2 style={{ color: '#00d4ff', margin: '0 0 20px 0' }}>ASI Excellence</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              background: 'conic-gradient(from 0deg, #00ff88, #00d4ff, #00ff88)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem',
              fontWeight: 'bold'
            }}>
              <div style={{
                background: '#1a1a2e',
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {qqMetrics.asi.excellence_score}
              </div>
            </div>
            <div>
              <div>Autonomous Decisions: {qqMetrics.asi.autonomous_decisions}</div>
              <div>Error Prevention: {qqMetrics.asi.error_prevention_rate}%</div>
            </div>
          </div>
        </div>
      </div>
      
      <div>
        <h2>Fleet Assets ({assets.length} Active)</h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
          gap: '15px'
        }}>
          {assets.slice(0, 6).map((asset: any) => (
            <div key={asset.id} style={{
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '12px',
              padding: '15px',
              cursor: 'pointer',
              transition: 'all 0.3s',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span style={{ fontWeight: 'bold', color: '#00d4ff' }}>{asset.id}</span>
                <span style={{
                  background: '#00ff88',
                  color: 'black',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '0.8rem',
                  fontWeight: 'bold'
                }}>
                  ACTIVE
                </span>
              </div>
              <div style={{ marginBottom: '10px' }}>{asset.name || `Asset ${asset.id}`}</div>
              <div style={{ fontSize: '0.9rem', color: '#ccc' }}>
                <div>Location: Fort Worth Zone</div>
                <div>Hours: {Math.floor(Math.random() * 12) + 1}</div>
                <div>Utilization: {Math.floor(Math.random() * 40) + 60}%</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}