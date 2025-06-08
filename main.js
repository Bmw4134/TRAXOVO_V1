const { spawn } = require('child_process');

// Start the Python Flask server
const pythonServer = spawn('python', ['app_minimal.py'], {
  stdio: 'inherit',
  cwd: process.cwd()
});

pythonServer.on('close', (code) => {
  console.log(`Python server exited with code ${code}`);
});

pythonServer.on('error', (err) => {
  console.error('Failed to start Python server:', err);
});