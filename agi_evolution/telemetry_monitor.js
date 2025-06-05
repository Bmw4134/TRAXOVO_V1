const fs = require('fs');

function logTelemetry(route, latency, userAgent) {
  const log = {
    route,
    latency,
    userAgent,
    timestamp: new Date().toISOString()
  };
  fs.appendFileSync('./logs/agi_sync.json', JSON.stringify(log) + '\n');
}
module.exports = { logTelemetry };
