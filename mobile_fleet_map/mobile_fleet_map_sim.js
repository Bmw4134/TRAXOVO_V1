// mobile_fleet_map_sim.js
const simulateLogin = (user) => {
  console.log(`Simulating login for: ${user}`);
  for (let i = 0; i < 1_000_000; i++) {
    // Simulated login processing
    if (i % 100000 === 0) console.log(`Iteration ${i}...`);
  }
  console.log(`${user} login simulation complete.`);
};

simulateLogin("Troy");
simulateLogin("William");
