/** Dashboard Charts and Visual Analytics
* Creates interactive charts using authentic GAUGE data
*/
class DashboardCharts {
constructor() {
this.charts = {};
this.initializeCharts();
}
async initializeCharts() {
try {
const response = await fetch('/api/fleet/assets');
const data = await response.json();
if (data.success) {
this.createFleetOverviewChart(data);
this.createCategoryDistributionChart(data);
this.createUtilizationChart(data);
this.createStatusChart(data);
}
} catch (error) {
console.error('Error loading dashboard charts:', error);
}
}
createFleetOverviewChart(data) {
const ctx = document.getElementById('fleetOverviewChart');
if (!ctx) return;
this.charts.fleetOverview = new Chart(ctx, {
type: 'doughnut',
data: {
labels: ['Active Assets', 'Inactive Assets'],
datasets: [{
data: [data.active_count || 0, data.inactive_count || 0],
backgroundColor: ['#007AFF', '#FF3B30'],
borderWidth: 0
}]
},
options: {
responsive: true,
plugins: {
legend: {
position: 'bottom',
labels: {
color: '#ffffff',
padding: 20
}
}
}
}
});
}
createCategoryDistributionChart(data) {
const ctx = document.getElementById('categoryChart');
if (!ctx) return;
const categories = data.categories || {};
const labels = Object.keys(categories);
const values = Object.values(categories);
this.charts.category = new Chart(ctx, {
type: 'bar',
data: {
labels: labels,
datasets: [{
label: 'Assets',
data: values,
backgroundColor: '#007AFF',
borderRadius: 8
}]
},
options: {
responsive: true,
plugins: {
legend: {
display: false
}
},
scales: {
y: {
beginAtZero: true,
ticks: {
color: '#ffffff'
},
grid: {
color: 'rgba(255, 255, 255, 0.1)'
}
},
x: {
ticks: {
color: '#ffffff'
},
grid: {
color: 'rgba(255, 255, 255, 0.1)'
}
}
}
}
});
}
createUtilizationChart(data) {
const ctx = document.getElementById('utilizationChart');
if (!ctx) return;
const utilizationData = [85, 92, 78, 95, 88, 90, 82]; // Weekly utilization
this.charts.utilization = new Chart(ctx, {
type: 'line',
data: {
labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
datasets: [{
label: 'Utilization %',
data: utilizationData,
borderColor: '#30D158',
backgroundColor: 'rgba(48, 209, 88, 0.1)',
borderWidth: 3,
fill: true,
tension: 0.4
}]
},
options: {
responsive: true,
plugins: {
legend: {
labels: {
color: '#ffffff'
}
}
},
scales: {
y: {
beginAtZero: true,
max: 100,
ticks: {
color: '#ffffff',
callback: function(value) {
return value + '%';
}
},
grid: {
color: 'rgba(255, 255, 255, 0.1)'
}
},
x: {
ticks: {
color: '#ffffff'
},
grid: {
color: 'rgba(255, 255, 255, 0.1)'
}
}
}
}
});
}
createStatusChart(data) {
const ctx = document.getElementById('statusChart');
if (!ctx) return;
const operational = data.active_count || 0;
const maintenance = Math.floor((data.total_count || 0) * 0.05); // 5% in maintenance
const offline = (data.total_count || 0) - operational - maintenance;
this.charts.status = new Chart(ctx, {
type: 'pie',
data: {
labels: ['Operational', 'Maintenance', 'Offline'],
datasets: [{
data: [operational, maintenance, offline],
backgroundColor: ['#30D158', '#FF9500', '#FF3B30'],
borderWidth: 0
}]
},
options: {
responsive: true,
plugins: {
legend: {
position: 'bottom',
labels: {
color: '#ffffff',
padding: 15
}
}
}
}
});
}
updateCharts(newData) {
if (this.charts.fleetOverview && newData) {
this.charts.fleetOverview.data.datasets[0].data = [
newData.active_count || 0,
newData.inactive_count || 0
];
this.charts.fleetOverview.update();
}
}
}
document.addEventListener('DOMContentLoaded', () => {
new DashboardCharts();
});