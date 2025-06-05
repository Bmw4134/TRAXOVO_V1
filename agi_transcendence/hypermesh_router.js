const AGINetwork = {};

function routeTask(task, context) {
  const target = Object.keys(AGINetwork).find(agent => AGINetwork[agent].canHandle(task));
  return target ? `🔗 Routed ${task} to ${target}` : `❌ No optimal agent found`;
}

function registerAgent(name, capabilities) {
  AGINetwork[name] = { canHandle: (task) => capabilities.includes(task) };
  console.log(`🧠 ${name} registered in AGI HyperMesh`);
}

module.exports = { routeTask, registerAgent };
