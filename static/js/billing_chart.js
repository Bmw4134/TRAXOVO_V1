let chartInstance = null;
function renderBillingChart(rawData, timeframe = 30) {
const ctx = document.getElementById("billingChart").getContext("2d");
if (chartInstance) {
chartInstance.destroy();
}
const labels = rawData.labels.slice(-timeframe);
const dataPoints = rawData.data.slice(-timeframe);
chartInstance = new Chart(ctx, {
type: "line",
data: {
labels: labels,
datasets: [{
label: "Billing Amount ($)",
data: dataPoints,
fill: false,
borderColor: "rgba(75, 192, 192, 1)",
backgroundColor: "rgba(75, 192, 192, 0.2)",
tension: 0.1
}]
},
options: {
responsive: true,
maintainAspectRatio: false,
scales: {
y: {
beginAtZero: true,
ticks: {
callback: function(value) {
return '$' + value.toLocaleString();
}
}
}
}
}
});
}
function loadBillingData() {
fetch('/api/billing_data')
.then(response => response.json())
.then(data => {
window.billingData = data;
renderBillingChart(data, 30);
})
.catch(error => {
console.error('Error loading billing data:', error);
});
}
document.addEventListener('DOMContentLoaded', function() {
loadBillingData();
document.querySelectorAll(".timeframe-toggle").forEach(btn => {
btn.addEventListener("click", () => {
document.querySelectorAll(".timeframe-toggle").forEach(b => b.classList.remove('active'));
btn.classList.add('active');
const days = parseInt(btn.dataset.days);
if (window.billingData) {
renderBillingChart(window.billingData, days);
}
});
});
});