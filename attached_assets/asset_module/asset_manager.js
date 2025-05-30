fetch('/api/assets')
  .then(response => response.json())
  .then(data => {
    document.getElementById('total-assets').textContent = data.total;
    document.getElementById('active-assets').textContent = data.active;
    document.getElementById('utilization-rate').textContent = data.utilization + '%';
    const tbody = document.getElementById('asset-table-body');
    tbody.innerHTML = '';
    data.assets.forEach(asset => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${asset.id}</td>
        <td>${asset.description}</td>
        <td>${asset.category}</td>
        <td>${asset.make_model}</td>
        <td>${asset.year}</td>
        <td>${asset.status}</td>
        <td>${asset.location}</td>
      `;
      tbody.appendChild(row);
    });
  });
