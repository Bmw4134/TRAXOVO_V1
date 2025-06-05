/**
 * TRAXOVO Infinity Server - Secure Authentication System
 * Express.js server with Playwright integration and session management
 */

const express = require('express');
const session = require('express-session');
const cookieParser = require('cookie-parser');
const bcrypt = require('bcryptjs');
const flash = require('connect-flash');
const path = require('path');
const { chromium } = require('playwright');

// AGI Infinity Synthesis Components
const { updateDashboardSync } = require('./agi_evolution/sovereign_coordinator');
const { delegateAgentTask } = require('./agi_evolution/agent_relay');
const { logTelemetry } = require('./agi_evolution/telemetry_monitor');

const app = express();
const PORT = process.env.PORT || 5000;

// User database (in production, use proper database)
const users = {
    'admin': {
        password: bcrypt.hashSync('admin123', 10),
        role: 'admin',
        timeout: 3600000, // 1 hour
        name: 'Administrator'
    },
    'troy': {
        password: bcrypt.hashSync('troy2025', 10),
        role: 'exec',
        timeout: 7200000, // 2 hours
        name: 'Troy Ragle'
    },
    'william': {
        password: bcrypt.hashSync('william2025', 10),
        role: 'exec',
        timeout: 7200000, // 2 hours
        name: 'William Ragle'
    },
    'ops': {
        password: bcrypt.hashSync('ops123', 10),
        role: 'ops',
        timeout: 1800000, // 30 minutes
        name: 'Operations Manager'
    }
};

// Session configuration
app.use(session({
    secret: process.env.SESSION_SECRET || 'traxovo-infinity-secure-key-2025',
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: false, // Set to true in production with HTTPS
        httpOnly: true,
        maxAge: 3600000 // Default 1 hour, overridden per user
    },
    rolling: true // Reset timeout on activity
}));

// Middleware
app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(flash());
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

// AGI Telemetry Monitoring Middleware
app.use((req, res, next) => {
    const start = Date.now();
    
    res.on('finish', () => {
        const latency = Date.now() - start;
        const userAgent = req.get('User-Agent') || 'unknown';
        
        try {
            logTelemetry(req.path, latency, userAgent);
            
            // Update dashboard sync for key routes
            if (req.path.includes('/api/') || req.path === '/') {
                const fingerprint = `${req.path}-${Date.now()}`;
                updateDashboardSync(req.path, fingerprint, { latency, status: res.statusCode });
            }
        } catch (error) {
            console.error('Telemetry logging failed:', error);
        }
    });
    
    next();
});

// Authentication middleware
function requireAuth(req, res, next) {
    if (req.session && req.session.user) {
        // Check if session has expired based on user-specific timeout
        const user = users[req.session.user.username];
        if (user && req.session.lastActivity) {
            const timeElapsed = Date.now() - req.session.lastActivity;
            if (timeElapsed > user.timeout) {
                req.session.destroy();
                return res.redirect('/login?expired=true');
            }
        }
        // Update last activity
        req.session.lastActivity = Date.now();
        // Update cookie maxAge for user-specific timeout
        if (user) {
            req.session.cookie.maxAge = user.timeout;
        }
        return next();
    } else {
        return res.redirect('/login');
    }
}

// Role-based access control
function requireRole(roles) {
    return (req, res, next) => {
        if (req.session && req.session.user && roles.includes(req.session.user.role)) {
            return next();
        } else {
            return res.status(403).json({ error: 'Access denied' });
        }
    };
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        service: 'TRAXOVO Infinity',
        version: '1.0.0'
    });
});

// Login page (public access)
app.get('/login', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'login.html'));
});

// Login POST handler
app.post('/login', async (req, res) => {
    const { username, password } = req.body;
    const user = users[username];
    
    if (user && await bcrypt.compare(password, user.password)) {
        req.session.user = {
            username: username,
            role: user.role,
            name: user.name
        };
        req.session.lastActivity = Date.now();
        req.session.cookie.maxAge = user.timeout;
        res.redirect('/');
    } else {
        res.redirect('/login?error=invalid');
    }
});

// Logout handler
app.post('/logout', (req, res) => {
    req.session.destroy((err) => {
        res.redirect('/login');
    });
});

// Main dashboard route (protected)
app.get('/', requireAuth, (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Enhanced Ragle Inc landing page (protected)
app.get('/ragle', requireAuth, (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'ragle-enhanced.html'));
});

// User settings page (protected)
app.get('/settings', requireAuth, (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'settings.html'));
});

// Update user settings
app.post('/settings', requireAuth, (req, res) => {
    const { timeout } = req.body;
    const username = req.session.user.username;
    
    if (users[username] && timeout && timeout >= 300000 && timeout <= 86400000) {
        users[username].timeout = parseInt(timeout);
        req.session.cookie.maxAge = users[username].timeout;
        res.json({ success: true, message: 'Settings updated successfully' });
    } else {
        res.status(400).json({ error: 'Invalid timeout value' });
    }
});

// Redirect quantum dashboard to main Flask app (protected)
app.get('/quantum-dashboard', requireAuth, (req, res) => {
    res.redirect('http://localhost:5000/quantum-dashboard');
});

// Redirect fleet map to main Flask app (protected)
app.get('/fleet-map', requireAuth, (req, res) => {
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

// User information API (protected)
app.get('/api/user-info', requireAuth, (req, res) => {
    const username = req.session.user.username;
    const user = users[username];
    
    if (user) {
        res.json({
            user: {
                username: username,
                role: user.role,
                name: user.name,
                timeout: user.timeout
            },
            session: {
                lastActivity: req.session.lastActivity,
                maxAge: req.session.cookie.maxAge
            }
        });
    } else {
        res.status(404).json({ error: 'User not found' });
    }
});

// AGI Synthesis endpoints
app.get('/api/agi-status', requireAuth, (req, res) => {
    const memoryUsage = process.memoryUsage();
    const memoryUsedRatio = memoryUsage.heapUsed / memoryUsage.heapTotal;
    
    const agentStatus = delegateAgentTask('primary-agent', 'status-check', memoryUsedRatio);
    
    res.json({
        sovereignty: 'active',
        agent_relay: agentStatus,
        memory_usage: {
            used: memoryUsage.heapUsed,
            total: memoryUsage.heapTotal,
            ratio: memoryUsedRatio
        },
        telemetry_active: true,
        fingerprint_sync: 'operational',
        timestamp: new Date().toISOString()
    });
});

// Dashboard fingerprint status
app.get('/api/dashboard-fingerprints', requireAuth, (req, res) => {
    try {
        const fs = require('fs');
        let telemetryData = [];
        
        if (fs.existsSync('./logs/agi_sync.json')) {
            const data = fs.readFileSync('./logs/agi_sync.json', 'utf8');
            telemetryData = data.split('\n')
                .filter(line => line.trim())
                .map(line => JSON.parse(line))
                .slice(-10); // Last 10 entries
        }
        
        res.json({
            dashboard_fingerprints: 'synchronized',
            telemetry_entries: telemetryData.length,
            recent_activity: telemetryData,
            relay_status: 'balanced',
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to read telemetry data' });
    }
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