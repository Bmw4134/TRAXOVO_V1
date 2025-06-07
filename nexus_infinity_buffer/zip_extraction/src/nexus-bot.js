const { chromium } = require('playwright');

async function launchBot({ url, prompt, selectorInput, selectorOutput }) {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    await page.goto(url);
    await page.waitForSelector(selectorInput);
    await page.fill(selectorInput, prompt);
    await page.keyboard.press('Enter');
    await page.waitForSelector(selectorOutput);
    const result = await page.$eval(selectorOutput, el => el.innerText);
    console.log("Extracted Response:", result);
    await browser.close();
    return result;
}

module.exports = { launchBot };