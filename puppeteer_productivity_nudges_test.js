const puppeteer = require('puppeteer');

async function testContextualProductivityNudges() {
    console.log('🚀 Starting Contextual Productivity Nudges Test');
    
    const browser = await puppeteer.launch({
        headless: false,
        defaultViewport: null,
        args: ['--start-maximized', '--no-sandbox']
    });
    
    const page = await browser.newPage();
    
    try {
        // Navigate to Quantum ASI Dashboard
        console.log('📊 Navigating to Quantum ASI Dashboard...');
        await page.goto('http://localhost:5000/quantum_asi_dashboard', { 
            waitUntil: 'networkidle2',
            timeout: 30000 
        });
        
        // Wait for productivity nudges to load
        console.log('🧠 Waiting for productivity nudges to load...');
        await page.waitForSelector('.productivity-nudges', { timeout: 10000 });
        
        // Test nudge card interactions
        console.log('🎯 Testing nudge card interactions...');
        const nudgeCards = await page.$$('.nudge-card');
        console.log(`Found ${nudgeCards.length} nudge cards`);
        
        // Test first nudge action button
        if (nudgeCards.length > 0) {
            console.log('⚡ Testing first nudge action...');
            const firstActionButton = await page.$('.nudge-action');
            if (firstActionButton) {
                await firstActionButton.click();
                console.log('✅ First nudge action executed');
                
                // Wait for visual feedback
                await page.waitForTimeout(2000);
            }
        }
        
        // Test Kaizen Quantum Sweep
        console.log('🌟 Testing Kaizen Quantum Sweep...');
        const kaizenButton = await page.$('button[onclick="executeKaizenSweep()"]');
        if (kaizenButton) {
            await kaizenButton.click();
            console.log('✅ Kaizen Quantum Sweep initiated');
            await page.waitForTimeout(3000);
        }
        
        // Test workflow optimization
        console.log('⚙️ Testing workflow optimization...');
        const optimizeButton = await page.$('button[onclick="optimizeWorkflows()"]');
        if (optimizeButton) {
            await optimizeButton.click();
            console.log('✅ Workflow optimization triggered');
            await page.waitForTimeout(2000);
        }
        
        // Test insights generation
        console.log('💡 Testing insights generation...');
        const insightsButton = await page.$('button[onclick="generateInsights()"]');
        if (insightsButton) {
            await insightsButton.click();
            console.log('✅ Insights generation triggered');
            await page.waitForTimeout(2000);
        }
        
        // Check contextual insights feed
        console.log('📈 Checking contextual insights feed...');
        const insightItems = await page.$$('.insight-item');
        console.log(`Found ${insightItems.length} insight items in feed`);
        
        // Verify quantum status metrics
        console.log('🔬 Verifying quantum status metrics...');
        const statusCards = await page.$$('.status-card');
        console.log(`Found ${statusCards.length} status metric cards`);
        
        for (let i = 0; i < statusCards.length; i++) {
            const title = await statusCards[i].$eval('.status-title', el => el.textContent);
            const value = await statusCards[i].$eval('.status-value', el => el.textContent);
            console.log(`📊 ${title}: ${value}`);
        }
        
        // Take screenshot of dashboard
        console.log('📸 Taking dashboard screenshot...');
        await page.screenshot({ 
            path: 'contextual_productivity_nudges_test.png',
            fullPage: true 
        });
        
        console.log('🎉 Contextual Productivity Nudges test completed successfully!');
        
        // Keep browser open for 30 seconds for manual inspection
        console.log('👀 Keeping browser open for 30 seconds for manual inspection...');
        await page.waitForTimeout(30000);
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        
        // Take error screenshot
        await page.screenshot({ 
            path: 'productivity_nudges_error.png',
            fullPage: true 
        });
    } finally {
        await browser.close();
        console.log('🔚 Test completed');
    }
}

// Run the test
testContextualProductivityNudges().catch(console.error);