
import React, { useState, useEffect } from 'react';

const NexusNavigationOverlay = () => {
    const [isVisible, setIsVisible] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filteredRoutes, setFilteredRoutes] = useState([]);

    const allRoutes = {
  "primary_routes": [
    {
      "path": "/",
      "name": "NEXUS Landing",
      "access": "public"
    },
    {
      "path": "/admin-direct",
      "name": "Admin Control Center",
      "access": "admin"
    },
    {
      "path": "/nexus-dashboard",
      "name": "Intelligence Dashboard",
      "access": "authenticated"
    },
    {
      "path": "/executive-dashboard",
      "name": "Executive Analytics",
      "access": "executive"
    },
    {
      "path": "/upload",
      "name": "File Processing",
      "access": "authenticated"
    }
  ],
  "api_routes": [
    {
      "path": "/api/nexus/command",
      "name": "NEXUS Command Interface",
      "type": "POST"
    },
    {
      "path": "/api/nexus/metrics",
      "name": "System Metrics",
      "type": "GET"
    },
    {
      "path": "/api/platform/status",
      "name": "Platform Status",
      "type": "GET"
    },
    {
      "path": "/api/market/data",
      "name": "Market Data",
      "type": "GET"
    },
    {
      "path": "/api/weather/data",
      "name": "Weather Data",
      "type": "GET"
    },
    {
      "path": "/api/ez-integration/status",
      "name": "EZ-Integration Status",
      "type": "GET"
    },
    {
      "path": "/api/executive/metrics",
      "name": "Executive Metrics",
      "type": "GET"
    },
    {
      "path": "/api/ai-fix-regressions",
      "name": "AI Regression Fixer",
      "type": "GET"
    },
    {
      "path": "/api/self-heal/check",
      "name": "Self-Healing Check",
      "type": "GET"
    },
    {
      "path": "/api/platform/health",
      "name": "Platform Health",
      "type": "GET"
    },
    {
      "path": "/api/perplexity/search",
      "name": "Perplexity Search",
      "type": "POST"
    },
    {
      "path": "/api/auth/reset-password",
      "name": "Password Reset",
      "type": "POST"
    },
    {
      "path": "/api/nexus/integrity-report",
      "name": "Integrity Report",
      "type": "POST"
    }
  ],
  "hidden_routes": [
    {
      "path": "/repl-agent",
      "name": "Repl Agent Interface",
      "access": "developer"
    },
    {
      "path": "/nexus-core-diagnostics",
      "name": "Core Diagnostics",
      "access": "system"
    },
    {
      "path": "/automation-console",
      "name": "Automation Console",
      "access": "admin"
    },
    {
      "path": "/intelligence-core-test",
      "name": "Intelligence Test",
      "access": "developer"
    }
  ],
  "legacy_paths": [
    {
      "path": "/legacy-dashboard",
      "name": "Legacy Dashboard",
      "status": "deprecated"
    },
    {
      "path": "/old-admin",
      "name": "Old Admin Panel",
      "status": "deprecated"
    },
    {
      "path": "/beta-features",
      "name": "Beta Features",
      "status": "experimental"
    }
  ]
};

    useEffect(() => {
        // Keyboard shortcut: Cmd+K or Ctrl+K
        const handleKeyDown = (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                setIsVisible(!isVisible);
            }
            if (e.key === 'Escape') {
                setIsVisible(false);
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isVisible]);

    useEffect(() => {
        // Filter routes based on search term
        const filtered = [];
        Object.keys(allRoutes).forEach(category => {
            allRoutes[category].forEach(route => {
                if (route.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                    route.path.toLowerCase().includes(searchTerm.toLowerCase())) {
                    filtered.push({...route, category});
                }
            });
        });
        setFilteredRoutes(filtered);
    }, [searchTerm]);

    const navigateToRoute = (path) => {
        window.location.href = path;
        setIsVisible(false);
    };

    const getStatusColor = (route) => {
        if (route.status === 'deprecated') return '#ff6b6b';
        if (route.status === 'experimental') return '#4ecdc4';
        if (route.access === 'admin') return '#45b7d1';
        if (route.access === 'developer') return '#96ceb4';
        return '#2ecc71';
    };

    if (!isVisible) {
        return (
            <div className="nexus-nav-trigger" 
                 style={{
                     position: 'fixed',
                     bottom: '20px',
                     left: '20px',
                     zIndex: 1000,
                     background: 'rgba(0,0,0,0.8)',
                     color: 'white',
                     padding: '10px 15px',
                     borderRadius: '5px',
                     cursor: 'pointer',
                     fontSize: '12px'
                 }}
                 onClick={() => setIsVisible(true)}>
                ⌘K Navigate
            </div>
        );
    }

    return (
        <div className="nexus-navigation-overlay" 
             style={{
                 position: 'fixed',
                 top: 0,
                 left: 0,
                 width: '100%',
                 height: '100%',
                 background: 'rgba(0,0,0,0.8)',
                 zIndex: 10000,
                 display: 'flex',
                 justifyContent: 'center',
                 alignItems: 'flex-start',
                 paddingTop: '100px'
             }}>
            <div style={{
                background: 'white',
                borderRadius: '10px',
                width: '600px',
                maxHeight: '500px',
                overflow: 'hidden',
                boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
            }}>
                <div style={{padding: '20px', borderBottom: '1px solid #eee'}}>
                    <input
                        type="text"
                        placeholder="Search routes... (⌘K to toggle)"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '10px',
                            border: '1px solid #ddd',
                            borderRadius: '5px',
                            fontSize: '16px'
                        }}
                        autoFocus
                    />
                </div>
                
                <div style={{maxHeight: '400px', overflowY: 'auto'}}>
                    {filteredRoutes.map((route, index) => (
                        <div key={index}
                             onClick={() => navigateToRoute(route.path)}
                             style={{
                                 padding: '15px 20px',
                                 borderBottom: '1px solid #f0f0f0',
                                 cursor: 'pointer',
                                 display: 'flex',
                                 justifyContent: 'space-between',
                                 alignItems: 'center',
                                 ':hover': {background: '#f8f9fa'}
                             }}>
                            <div>
                                <div style={{fontWeight: 'bold', marginBottom: '5px'}}>
                                    {route.name}
                                </div>
                                <div style={{color: '#666', fontSize: '14px'}}>
                                    {route.path}
                                </div>
                            </div>
                            <div style={{
                                background: getStatusColor(route),
                                color: 'white',
                                padding: '4px 8px',
                                borderRadius: '3px',
                                fontSize: '12px'
                            }}>
                                {route.category}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default NexusNavigationOverlay;
