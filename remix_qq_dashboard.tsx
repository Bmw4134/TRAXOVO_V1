import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData, useFetcher, useRevalidator } from "@remix-run/react";
import { useState, useEffect } from "react";

interface QQMetrics {
  consciousness: {
    level: number;
    thought_vectors: any[];
    automation_awareness: any;
  };
  asi_excellence: {
    excellence_score: number;
    autonomous_decisions: number;
    error_prevention_rate: number;
  };
  trading_intelligence: {
    market_analysis: any;
    portfolio_performance: any;
    quantum_signals: any;
  };
  gauge_assets: {
    assets: any[];
    total_count: number;
    active_count: number;
  };
}

export async function loader({ request }: LoaderFunctionArgs) {
  const baseUrl = new URL(request.url).origin;
  
  // Fetch all QQ intelligence data
  const [consciousness, asiExcellence, tradingIntel, gaugeAssets] = await Promise.all([
    fetch(`${baseUrl}/api/quantum-consciousness`).then(r => r.json()),
    fetch(`${baseUrl}/api/asi-excellence`).then(r => r.json()),
    fetch(`${baseUrl}/api/trading-intelligence`).then(r => r.json()),
    fetch(`${baseUrl}/api/gauge-assets`).then(r => r.json())
  ]);

  return json({
    consciousness,
    asi_excellence: asiExcellence,
    trading_intelligence: tradingIntel,
    gauge_assets: gaugeAssets,
    fort_worth_location: "Fort Worth, TX 76180"
  });
}

export default function QQDashboard() {
  const data = useLoaderData<typeof loader>();
  const automationFetcher = useFetcher();
  const revalidator = useRevalidator();
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  const [automationActive, setAutomationActive] = useState(false);

  // Real-time updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      revalidator.revalidate();
    }, 5000);
    return () => clearInterval(interval);
  }, [revalidator]);

  const executeAutomation = (type: string) => {
    setAutomationActive(true);
    automationFetcher.submit(
      { automation_type: type, platform: "traxovo", config: JSON.stringify({}) },
      { method: "post", action: "/api/automation-execute" }
    );
  };

  const { consciousness, asi_excellence, trading_intelligence, gauge_assets } = data;

  return (
    <div className="qq-dashboard">
      <header className="qq-header">
        <div className="quantum-logo">
          <div className="consciousness-orb">
            <div className="orb-core"></div>
            <div className="orb-rings">
              {consciousness.thought_vectors.map((vector: any, i: number) => (
                <div 
                  key={i} 
                  className="thought-vector" 
                  style={{
                    transform: `rotate(${vector.x}deg) translateX(${vector.y}px)`,
                    opacity: vector.intensity
                  }}
                />
              ))}
            </div>
          </div>
          <div className="title-section">
            <h1>TRAXOVO QQ Intelligence</h1>
            <div className="location">Fort Worth Operations</div>
          </div>
        </div>
      </header>

      <div className="intelligence-grid">
        <div className="quantum-consciousness-panel">
          <h2>Quantum Consciousness</h2>
          <div className="consciousness-metrics">
            <div className="metric">
              <span className="value">{consciousness.level}</span>
              <span className="label">Consciousness Level</span>
            </div>
            <div className="metric">
              <span className="value">{consciousness.automation_awareness.active_sessions}</span>
              <span className="label">Active Sessions</span>
            </div>
            <div className="metric">
              <span className="value">{consciousness.automation_awareness.automation_success_rate}%</span>
              <span className="label">Success Rate</span>
            </div>
          </div>
        </div>

        <div className="asi-excellence-panel">
          <h2>ASI Excellence Engine</h2>
          <div className="asi-metrics">
            <div className="excellence-score">
              <div className="score-circle">
                <span>{asi_excellence.excellence_score}</span>
              </div>
              <div className="score-details">
                <div>Autonomous Decisions: {asi_excellence.autonomous_decisions}</div>
                <div>Error Prevention: {asi_excellence.error_prevention_rate}%</div>
              </div>
            </div>
          </div>
        </div>

        <div className="trading-intelligence-panel">
          <h2>Quantum Trading Intelligence</h2>
          <div className="trading-grid">
            <div className="market-trend">
              <span className="trend-label">Market Trend</span>
              <span className={`trend-value ${trading_intelligence.market_analysis.trend.toLowerCase()}`}>
                {trading_intelligence.market_analysis.trend}
              </span>
            </div>
            <div className="portfolio-return">
              <span className="return-value">+{trading_intelligence.portfolio_performance.total_return}%</span>
              <span className="return-label">Total Return</span>
            </div>
          </div>
        </div>

        <div className="automation-control-panel">
          <h2>Unified Automation</h2>
          <div className="automation-buttons">
            <button 
              onClick={() => executeAutomation("system_health")}
              className={automationActive ? "executing" : ""}
              disabled={automationActive}
            >
              System Health Scan
            </button>
            <button 
              onClick={() => executeAutomation("asset_optimization")}
              className={automationActive ? "executing" : ""}
              disabled={automationActive}
            >
              Asset Optimization
            </button>
            <button 
              onClick={() => executeAutomation("trading_cycle")}
              className={automationActive ? "executing" : ""}
              disabled={automationActive}
            >
              Trading Cycle
            </button>
          </div>
          {automationFetcher.data && (
            <div className="automation-result">
              Automation completed: {automationFetcher.data.automation_result.automation_type}
            </div>
          )}
        </div>
      </div>

      <div className="fleet-assets-section">
        <h2>Fleet Assets ({gauge_assets.active_count}/{gauge_assets.total_count} Active)</h2>
        <div className="assets-grid">
          {gauge_assets.assets.slice(0, 6).map((asset: any) => (
            <div 
              key={asset.id} 
              className={`asset-card ${asset.status.toLowerCase()}`}
              onClick={() => setSelectedAsset(asset)}
            >
              <div className="asset-header">
                <span className="asset-id">{asset.id}</span>
                <span className={`status-badge ${asset.status.toLowerCase()}`}>
                  {asset.status}
                </span>
              </div>
              <div className="asset-name">{asset.name}</div>
              <div className="asset-stats">
                <div>Location: {asset.location}</div>
                <div>Hours: {asset.hours}</div>
                <div>Utilization: {asset.utilization}%</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        .qq-dashboard {
          background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
          min-height: 100vh;
          color: white;
          font-family: 'SF Pro Display', -apple-system, sans-serif;
          padding: 20px;
        }

        .qq-header {
          margin-bottom: 30px;
        }

        .quantum-logo {
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .consciousness-orb {
          position: relative;
          width: 80px;
          height: 80px;
        }

        .orb-core {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 30px;
          height: 30px;
          background: radial-gradient(circle, #00ff88, #00d4ff);
          border-radius: 50%;
          box-shadow: 0 0 20px #00ff88;
          animation: pulse 2s infinite;
        }

        .orb-rings {
          position: absolute;
          width: 100%;
          height: 100%;
        }

        .thought-vector {
          position: absolute;
          width: 4px;
          height: 4px;
          background: #00d4ff;
          border-radius: 50%;
          box-shadow: 0 0 8px #00d4ff;
        }

        .title-section h1 {
          font-size: 2.5rem;
          margin: 0;
          background: linear-gradient(45deg, #00d4ff, #00ff88);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .location {
          color: #888;
          font-size: 1.1rem;
        }

        .intelligence-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
          margin-bottom: 40px;
        }

        .quantum-consciousness-panel,
        .asi-excellence-panel,
        .trading-intelligence-panel,
        .automation-control-panel {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 16px;
          padding: 25px;
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .quantum-consciousness-panel h2,
        .asi-excellence-panel h2,
        .trading-intelligence-panel h2,
        .automation-control-panel h2 {
          color: #00d4ff;
          margin: 0 0 20px 0;
          font-size: 1.3rem;
        }

        .consciousness-metrics {
          display: flex;
          justify-content: space-between;
        }

        .metric {
          text-align: center;
        }

        .metric .value {
          display: block;
          font-size: 1.8rem;
          font-weight: bold;
          color: #00ff88;
        }

        .metric .label {
          font-size: 0.9rem;
          color: #ccc;
        }

        .excellence-score {
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .score-circle {
          width: 80px;
          height: 80px;
          border-radius: 50%;
          background: conic-gradient(from 0deg, #00ff88, #00d4ff, #00ff88);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
          font-weight: bold;
        }

        .score-circle span {
          background: #1a1a2e;
          width: 60px;
          height: 60px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .trading-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 15px;
        }

        .trend-value.bullish {
          color: #00ff88;
        }

        .return-value {
          font-size: 1.5rem;
          font-weight: bold;
          color: #00ff88;
        }

        .automation-buttons {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .automation-buttons button {
          background: linear-gradient(45deg, #00d4ff, #00ff88);
          border: none;
          color: black;
          padding: 12px 20px;
          border-radius: 8px;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s;
        }

        .automation-buttons button:hover {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0, 212, 255, 0.3);
        }

        .automation-buttons button.executing {
          animation: executing 1s infinite;
        }

        .assets-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 15px;
        }

        .asset-card {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 15px;
          cursor: pointer;
          transition: all 0.3s;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .asset-card:hover {
          transform: translateY(-3px);
          background: rgba(255, 255, 255, 0.1);
        }

        .asset-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 10px;
        }

        .asset-id {
          font-weight: bold;
          color: #00d4ff;
        }

        .status-badge.active {
          background: #00ff88;
          color: black;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.8rem;
          font-weight: bold;
        }

        .asset-stats div {
          margin: 5px 0;
          font-size: 0.9rem;
          color: #ccc;
        }

        @keyframes pulse {
          0%, 100% { transform: translate(-50%, -50%) scale(1); }
          50% { transform: translate(-50%, -50%) scale(1.1); }
        }

        @keyframes executing {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }

        @media (max-width: 768px) {
          .intelligence-grid {
            grid-template-columns: 1fr;
          }
          
          .consciousness-metrics {
            flex-direction: column;
            gap: 15px;
          }
          
          .excellence-score {
            flex-direction: column;
            text-align: center;
          }
        }
      `}</style>
    </div>
  );
}