const dashboardState = {};
function updateDashboardSync(name, fingerprint, changes) {
  dashboardState[name] = { fingerprint, changes, timestamp: Date.now() };
  console.log(`🧠 Synced ${name} at ${new Date().toISOString()}`);
}
module.exports = { updateDashboardSync };
