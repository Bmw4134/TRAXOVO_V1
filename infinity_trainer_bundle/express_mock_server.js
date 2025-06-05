const express = require('express');
const app = express();
app.use(express.static('public'));

app.get('/api/assets', (req, res) => {
  res.json([{ id: 'asset1', lat: 40.71, lng: -74.00, value: 9800 }]);
});

app.get('/api/weather', (req, res) => {
  res.json({ temperature: 72, condition: 'clear', timestamp: Date.now() });
});

app.listen(3000, () => console.log('Server running at http://localhost:3000'));
