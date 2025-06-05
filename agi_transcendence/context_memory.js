const globalContext = {};

function storeMemory(agent, key, value) {
  if (!globalContext[agent]) globalContext[agent] = {};
  globalContext[agent][key] = value;
}

function retrieveMemory(agent, key) {
  return globalContext[agent]?.[key] || null;
}

module.exports = { storeMemory, retrieveMemory };
