/**
 * TRAXOVO Playwright Automation Engine
 * Replaces all Puppeteer dependencies with advanced Playwright automation
 * Quantum-enhanced automation for enterprise operations
 */

import { chromium, Browser, Page, BrowserContext } from 'playwright';
import { WebSocketServer } from 'ws';

interface AutomationConfig {
    headless: boolean;
    slowMo: number;
    timeout: number;
    viewport: { width: number; height: number };
    userAgent: string;
}

interface AutomationTask {
    id: string;
    type: 'navigation' | 'form_fill' | 'data_extraction' | 'interaction';
    target: string;
    actions: AutomationAction[];
    timeout?: number;
}

interface AutomationAction {
    type: 'click' | 'type' | 'wait' | 'screenshot' | 'extract';
    selector?: string;
    value?: string;
    timeout?: number;
}

class TRAXOVOPlaywrightEngine {
    private browser: Browser | null = null;
    private context: BrowserContext | null = null;
    private page: Page | null = null;
    private wsServer: WebSocketServer | null = null;
    private config: AutomationConfig;
    private isRunning: boolean = false;

    constructor(config: Partial<AutomationConfig> = {}) {
        this.config = {
            headless: false,
            slowMo: 100,
            timeout: 30000,
            viewport: { width: 1920, height: 1080 },
            userAgent: 'TRAXOVO-Automation-Engine/1.0',
            ...config
        };
    }

    async initialize(): Promise<void> {
        console.log('🚀 Initializing TRAXOVO Playwright Engine...');
        
        try {
            // Launch browser with enhanced configuration
            this.browser = await chromium.launch({
                headless: this.config.headless,
                slowMo: this.config.slowMo,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            });

            // Create browser context with enhanced capabilities
            this.context = await this.browser.newContext({
                viewport: this.config.viewport,
                userAgent: this.config.userAgent,
                permissions: ['notifications', 'geolocation'],
                recordVideo: {
                    dir: './automation-recordings/',
                    size: this.config.viewport
                }
            });

            // Create page with enhanced monitoring
            this.page = await this.context.newPage();
            
            // Set default timeout
            this.page.setDefaultTimeout(this.config.timeout);
            
            // Add console logging
            this.page.on('console', msg => {
                console.log(`🌐 Browser Console: ${msg.text()}`);
            });

            // Add error handling
            this.page.on('pageerror', error => {
                console.error(`❌ Page Error: ${error.message}`);
            });

            // Initialize WebSocket server for real-time communication
            await this.initializeWebSocketServer();

            this.isRunning = true;
            console.log('✅ TRAXOVO Playwright Engine initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize Playwright Engine:', error);
            throw error;
        }
    }

    private async initializeWebSocketServer(): Promise<void> {
        this.wsServer = new WebSocketServer({ port: 8080 });
        
        this.wsServer.on('connection', (ws) => {
            console.log('🔌 WebSocket client connected');
            
            ws.on('message', async (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    await this.handleWebSocketMessage(ws, message);
                } catch (error) {
                    ws.send(JSON.stringify({ 
                        type: 'error', 
                        message: `Failed to process message: ${error}` 
                    }));
                }
            });

            ws.on('close', () => {
                console.log('🔌 WebSocket client disconnected');
            });
        });

        console.log('🌐 WebSocket server started on port 8080');
    }

    private async handleWebSocketMessage(ws: any, message: any): Promise<void> {
        switch (message.type) {
            case 'execute_task':
                const result = await this.executeAutomationTask(message.task);
                ws.send(JSON.stringify({ 
                    type: 'task_result', 
                    taskId: message.task.id,
                    result 
                }));
                break;
                
            case 'navigate':
                await this.navigateToUrl(message.url);
                ws.send(JSON.stringify({ 
                    type: 'navigation_complete', 
                    url: message.url 
                }));
                break;
                
            case 'screenshot':
                const screenshot = await this.takeScreenshot();
                ws.send(JSON.stringify({ 
                    type: 'screenshot_taken', 
                    screenshot 
                }));
                break;
                
            default:
                ws.send(JSON.stringify({ 
                    type: 'error', 
                    message: `Unknown message type: ${message.type}` 
                }));
        }
    }

    async executeAutomationTask(task: AutomationTask): Promise<any> {
        if (!this.page) {
            throw new Error('Playwright engine not initialized');
        }

        console.log(`🔄 Executing automation task: ${task.id} (${task.type})`);
        
        try {
            const results: any[] = [];
            
            for (const action of task.actions) {
                const actionResult = await this.executeAction(action);
                results.push(actionResult);
            }
            
            console.log(`✅ Task ${task.id} completed successfully`);
            return {
                taskId: task.id,
                status: 'completed',
                results
            };
            
        } catch (error) {
            console.error(`❌ Task ${task.id} failed:`, error);
            return {
                taskId: task.id,
                status: 'failed',
                error: error.message
            };
        }
    }

    private async executeAction(action: AutomationAction): Promise<any> {
        if (!this.page) {
            throw new Error('Page not available');
        }

        console.log(`⚡ Executing action: ${action.type}`);
        
        switch (action.type) {
            case 'click':
                if (!action.selector) throw new Error('Selector required for click action');
                await this.page.click(action.selector, { timeout: action.timeout });
                return { type: 'click', selector: action.selector, status: 'completed' };
                
            case 'type':
                if (!action.selector || !action.value) {
                    throw new Error('Selector and value required for type action');
                }
                await this.page.fill(action.selector, action.value, { timeout: action.timeout });
                return { type: 'type', selector: action.selector, value: action.value, status: 'completed' };
                
            case 'wait':
                if (action.selector) {
                    await this.page.waitForSelector(action.selector, { timeout: action.timeout });
                } else {
                    await this.page.waitForTimeout(action.timeout || 1000);
                }
                return { type: 'wait', status: 'completed' };
                
            case 'screenshot':
                const screenshot = await this.page.screenshot({ 
                    fullPage: true,
                    type: 'png'
                });
                return { 
                    type: 'screenshot', 
                    screenshot: screenshot.toString('base64'), 
                    status: 'completed' 
                };
                
            case 'extract':
                if (!action.selector) throw new Error('Selector required for extract action');
                const element = await this.page.$(action.selector);
                const content = element ? await element.textContent() : null;
                return { 
                    type: 'extract', 
                    selector: action.selector, 
                    content, 
                    status: 'completed' 
                };
                
            default:
                throw new Error(`Unknown action type: ${action.type}`);
        }
    }

    async navigateToUrl(url: string): Promise<void> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        console.log(`🌐 Navigating to: ${url}`);
        await this.page.goto(url, { 
            waitUntil: 'domcontentloaded',
            timeout: this.config.timeout 
        });
    }

    async takeScreenshot(fullPage: boolean = true): Promise<string> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        const screenshot = await this.page.screenshot({ 
            fullPage,
            type: 'png'
        });
        
        return screenshot.toString('base64');
    }

    async extractPageData(selectors: Record<string, string>): Promise<Record<string, string>> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        const data: Record<string, string> = {};
        
        for (const [key, selector] of Object.entries(selectors)) {
            try {
                const element = await this.page.$(selector);
                data[key] = element ? await element.textContent() || '' : '';
            } catch (error) {
                console.warn(`Failed to extract data for ${key}: ${error}`);
                data[key] = '';
            }
        }
        
        return data;
    }

    async fillForm(formData: Record<string, string>): Promise<void> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        for (const [selector, value] of Object.entries(formData)) {
            try {
                await this.page.fill(selector, value);
                console.log(`✅ Filled ${selector} with value`);
            } catch (error) {
                console.error(`❌ Failed to fill ${selector}: ${error}`);
                throw error;
            }
        }
    }

    async waitForElement(selector: string, timeout?: number): Promise<void> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        await this.page.waitForSelector(selector, { 
            timeout: timeout || this.config.timeout 
        });
    }

    async getPageTitle(): Promise<string> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        return await this.page.title();
    }

    async getCurrentUrl(): Promise<string> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        return this.page.url();
    }

    async evaluateScript(script: string): Promise<any> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        return await this.page.evaluate(script);
    }

    async addScript(scriptPath: string): Promise<void> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        await this.page.addScriptTag({ path: scriptPath });
    }

    async addStylesheet(cssPath: string): Promise<void> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        await this.page.addStyleTag({ path: cssPath });
    }

    async mockResponse(url: string, response: any): Promise<void> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        await this.page.route(url, route => {
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(response)
            });
        });
    }

    async interceptRequest(urlPattern: string, handler: (route: any) => void): Promise<void> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        await this.page.route(urlPattern, handler);
    }

    async getPerformanceMetrics(): Promise<any> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        return await this.page.evaluate(() => {
            const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
            return {
                loadTime: navigation.loadEventEnd - navigation.loadEventStart,
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
            };
        });
    }

    async shutdown(): Promise<void> {
        console.log('🔄 Shutting down TRAXOVO Playwright Engine...');
        
        try {
            if (this.wsServer) {
                this.wsServer.close();
                console.log('✅ WebSocket server closed');
            }
            
            if (this.page) {
                await this.page.close();
                console.log('✅ Page closed');
            }
            
            if (this.context) {
                await this.context.close();
                console.log('✅ Browser context closed');
            }
            
            if (this.browser) {
                await this.browser.close();
                console.log('✅ Browser closed');
            }
            
            this.isRunning = false;
            console.log('✅ TRAXOVO Playwright Engine shutdown complete');
            
        } catch (error) {
            console.error('❌ Error during shutdown:', error);
        }
    }

    isEngineRunning(): boolean {
        return this.isRunning;
    }

    getConfig(): AutomationConfig {
        return { ...this.config };
    }

    async getPageMetadata(): Promise<any> {
        if (!this.page) {
            throw new Error('Page not available');
        }
        
        return await this.page.evaluate(() => {
            return {
                title: document.title,
                url: window.location.href,
                userAgent: navigator.userAgent,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                timestamp: new Date().toISOString()
            };
        });
    }
}

// Factory function for creating automation engine instances
export function createTRAXOVOAutomation(config?: Partial<AutomationConfig>): TRAXOVOPlaywrightEngine {
    return new TRAXOVOPlaywrightEngine(config);
}

// Main execution when run directly
async function main() {
    console.log('🚀 Starting TRAXOVO Playwright Automation Engine...');
    
    const automation = createTRAXOVOAutomation({
        headless: false,
        slowMo: 250
    });
    
    try {
        await automation.initialize();
        
        // Keep the engine running
        process.on('SIGINT', async () => {
            console.log('\n🛑 Received shutdown signal...');
            await automation.shutdown();
            process.exit(0);
        });
        
        console.log('✅ TRAXOVO Playwright Engine is running...');
        console.log('📡 WebSocket server listening on ws://localhost:8080');
        console.log('🔄 Ready for automation tasks...');
        
        // Keep process alive
        setInterval(() => {
            if (automation.isEngineRunning()) {
                console.log('💚 Engine heartbeat - all systems operational');
            }
        }, 30000);
        
    } catch (error) {
        console.error('❌ Failed to start automation engine:', error);
        await automation.shutdown();
        process.exit(1);
    }
}

// Export the engine class and factory function
export { TRAXOVOPlaywrightEngine, AutomationConfig, AutomationTask, AutomationAction };

// Run main function if this file is executed directly
if (require.main === module) {
    main().catch(console.error);
}