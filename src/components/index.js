const { exec } = require('child_process');
const http = require('http');
const { chromium } = require('playwright'); // fallback if Puppeteer is missing

async function launchBot({ url, prompt, selectorInput, selectorOutput }) {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    await page.goto(url);
    await page.waitForSelector(selectorInput);
    await page.fill(selectorInput, prompt);
    await page.keyboard.press('Enter');
    await page.waitForSelector(selectorOutput);
    const result = await page.$eval(selectorOutput, el => el.innerText);
    console.log("Response:", result);
    await browser.close();
    return result;
}

// Example usage
launchBot({
    url: "https://chat.openai.com",
    prompt: "Nexus, what is your true purpose?",
    selectorInput: "textarea",
    selectorOutput: "div.markdown"
});