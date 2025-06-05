/**
 * TRAXOVO Infinity Server
 * Express.js server with Playwright integration
 */

const express = require('express');
const path = require('path');
const { chromium } = require('playwright');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

// CORS for development
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    if (req.method === 'OPTIONS') {
        res.sendStatus(200);
    } else {
        next();
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        service: 'TRAXOVO Infinity',
        version: '1.0.0'
    });
});

// Main dashboard route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Enhanced Ragle Inc landing page
app.get('/ragle', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'ragle-enhanced.html'));
});

// Redirect quantum dashboard to main Flask app
app.get('/quantum-dashboard', (req, res) => {
    res.redirect('http://localhost:5000/quantum-dashboard');
});

// Redirect fleet map to main Flask app
app.get('/fleet-map', (req, res) => {
    res.redirect('http://localhost:5000/fleet-map');
});

// API routes
app.get('/api/status', (req, res) => {
    res.json({
        status: 'operational',
        services: {
            express: 'running',
            playwright: 'available'
        },
        timestamp: new Date().toISOString()
    });
});

// Playwright automation endpoint
app.post('/api/automation', async (req, res) => {
    try {
        const { action, url, selector } = req.body;
        
        const browser = await chromium.launch({ headless: true });
        const context = await browser.newContext();
        const page = await context.newPage();
        
        let result = {};
        
        switch (action) {
            case 'navigate':
                await page.goto(url);
                result = { 
                    action: 'navigate', 
                    url: page.url(), 
                    title: await page.title() 
                };
                break;
                
            case 'screenshot':
                const screenshot = await page.screenshot({ fullPage: true });
                result = { 
                    action: 'screenshot', 
                    data: screenshot.toString('base64') 
                };
                break;
                
            case 'extract':
                if (selector) {
                    const element = await page.$(selector);
                    const text = element ? await element.textContent() : null;
                    result = { 
                        action: 'extract', 
                        selector, 
                        text 
                    };
                }
                break;
                
            default:
                result = { error: 'Unknown action' };
        }
        
        await browser.close();
        res.json(result);
        
    } catch (error) {
        res.status(500).json({ 
            error: 'Automation failed', 
            message: error.message 
        });
    }
});

// Dashboard data endpoint
app.get('/api/dashboard', (req, res) => {
    res.json({
        title: 'TRAXOVO Infinity Dashboard',
        metrics: {
            assets: 717,
            active_jobs: 42,
            fleet_utilization: 87.3,
            operational_efficiency: 94.2
        },
        status: {
            system: 'operational',
            automation: 'active',
            data_sync: 'current'
        },
        last_updated: new Date().toISOString()
    });
});

// Fleet management endpoint
app.get('/api/fleet', (req, res) => {
    res.json({
        total_assets: 717,
        active: 717,
        inactive: 0,
        zones: [
            'Fort Worth Main Yard',
            'Trinity River Project',
            'Downtown Construction Site',
            'Alliance Equipment Depot'
        ],
        last_sync: new Date().toISOString()
    });
});

// User management endpoint
app.get('/api/users', (req, res) => {
    res.json({
        total_users: 4,
        active_sessions: 2,
        roles: ['admin', 'ops', 'exec', 'viewer'],
        last_activity: new Date().toISOString()
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Server error:', err);
    res.status(500).json({ 
        error: 'Internal server error', 
        message: err.message 
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ 
        error: 'Not found', 
        path: req.path 
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 TRAXOVO Infinity Server running on port ${PORT}`);
    console.log(`📊 Dashboard: http://localhost:${PORT}`);
    console.log(`💚 Health check: http://localhost:${PORT}/health`);
    console.log(`🤖 Automation API: http://localhost:${PORT}/api/automation`);
    console.log(`✅ Server ready for requests`);
});

module.exports = app;