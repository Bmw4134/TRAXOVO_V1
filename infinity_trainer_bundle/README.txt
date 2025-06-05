# Infinity Express + Playwright Trainer

## What this bundle trains:
- Express.js mock server with asset + weather endpoints
- Playwright test simulation of opening a map, loading overlays

## Instructions:
1. Run `npm install express @playwright/test`
2. Start server: `node express_mock_server.js`
3. Run Playwright test: `npx playwright test map_simulation.test.js`
4. Confirm behavior in logs and browser window

## Use Cases:
- Agent training to simulate user behavior
- Backend simulation for dashboard interactions
- Replace stubs with real API keys/data later

✅ Good to use as intelligent behavior starter before real deployments.
