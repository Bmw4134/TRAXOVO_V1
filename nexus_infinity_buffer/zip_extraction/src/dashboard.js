const express = require('express');
const path = require('path');
const open = require('open');
const { launchBot } = require('./nexus-bot');

const app = express();
const port = 4888;

app.use(express.static(path.join(__dirname, 'ui')));

app.get('/relay', async (req, res) => {
    const result = await launchBot({
        url: "https://chat.openai.com",
        prompt: "Activate relay sequence from Nexus.",
        selectorInput: "textarea",
        selectorOutput: "div.markdown"
    });
    res.send(`<h2>Response from ChatGPT:</h2><pre>${result}</pre>`);
});

app.listen(port, () => {
    console.log(`Nexus Dashboard Relay running at http://localhost:${port}/relay`);
    open(`http://localhost:${port}/relay`);
});