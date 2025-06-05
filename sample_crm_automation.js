// Sample CRM Automation Script
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    console.log('CRM automation started - saving API costs!');
    
    // Your automation logic here
    
    await browser.close();
})();