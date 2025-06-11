// Trigger headless job
async function triggerDiag(assetId) {
  const resp = await fetch('/api/automation/trigger', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ assetId, task: 'healthCheck' })
  });
  const json = await resp.json();
  console.log('Automation started:', json.jobId);
}
