function delegateAgentTask(agent, task, memoryUsed) {
  const limit = 0.8; // 80% memory threshold
  if (memoryUsed > limit) {
    console.log(`⚠️ ${agent} overloaded. Relaying to secondary...`);
    // Simulate agent relay handoff
    return `🔁 Task offloaded from ${agent} to backup agent`;
  } else {
    return `✅ ${agent} executed task`;
  }
}
module.exports = { delegateAgentTask };
