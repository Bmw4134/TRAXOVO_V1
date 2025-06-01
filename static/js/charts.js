function initializeCharts(statusCounts, categoryCounts, locationCounts) {
initializeStatusChart(statusCounts);
initializeCategoryChart(categoryCounts);
initializeLocationChart(locationCounts);
}
function initializeStatusChart(statusCounts) {
const ctx = document.getElementById('status-chart');
if (!ctx) return;
new Chart(ctx, {
type: 'pie',
data: {
labels: ['Active', 'Inactive'],
datasets: [{
data: [statusCounts.active, statusCounts.inactive],
backgroundColor: [
'rgba(40, 167, 69, 0.8)',  // Green for active
'rgba(220, 53, 69, 0.8)'   // Red for inactive
],
borderColor: [
'rgba(40, 167, 69, 1)',
'rgba(220, 53, 69, 1)'
],
borderWidth: 1
}]
},
options: {
responsive: true,
maintainAspectRatio: false,
plugins: {
legend: {
position: 'bottom',
labels: {
color: 'white'
}
},
title: {
display: true,
text: 'Asset Status Distribution',
color: 'white',
font: {
size: 16
}
},
tooltip: {
callbacks: {
label: function(context) {
const label = context.label || '';
const value = context.formattedValue || '';
const total = context.dataset.data.reduce((a, b) => a + b, 0);
const percentage = Math.round((context.raw / total) * 100);
return `${label}: ${value} (${percentage}%)`;
}
}
}
}
}
});
}
function initializeCategoryChart(categoryCounts) {
const ctx = document.getElementById('category-chart');
if (!ctx) return;
const categories = Object.keys(categoryCounts);
const counts = Object.values(categoryCounts);
const sortedIndices = counts.map((count, index) => ({ count, index }))
.sort((a, b) => b.count - a.count)
.map(item => item.index);
const sortedCategories = sortedIndices.map(index => categories[index]);
const sortedCounts = sortedIndices.map(index => counts[index]);
new Chart(ctx, {
type: 'bar',
data: {
labels: sortedCategories,
datasets: [{
label: 'Number of Assets',
data: sortedCounts,
backgroundColor: 'rgba(54, 162, 235, 0.8)',
borderColor: 'rgba(54, 162, 235, 1)',
borderWidth: 1
}]
},
options: {
responsive: true,
maintainAspectRatio: false,
scales: {
y: {
beginAtZero: true,
ticks: {
color: 'white'
},
grid: {
color: 'rgba(255, 255, 255, 0.1)'
}
},
x: {
ticks: {
color: 'white',
autoSkip: false,
maxRotation: 45,
minRotation: 45
},
grid: {
color: 'rgba(255, 255, 255, 0.1)'
}
}
},
plugins: {
legend: {
display: false
},
title: {
display: true,
text: 'Assets by Category',
color: 'white',
font: {
size: 16
}
}
}
}
});
}
function initializeLocationChart(locationCounts) {
const ctx = document.getElementById('location-chart');
if (!ctx) return;
const locations = Object.keys(locationCounts);
const counts = Object.values(locationCounts);
const backgroundColors = generateColors(locations.length, 0.8);
const borderColors = generateColors(locations.length, 1);
const sortedIndices = counts.map((count, index) => ({ count, index }))
.sort((a, b) => b.count - a.count)
.map(item => item.index);
const sortedLocations = sortedIndices.map(index => locations[index]);
const sortedCounts = sortedIndices.map(index => counts[index]);
const sortedBackgroundColors = sortedIndices.map(index => backgroundColors[index]);
const sortedBorderColors = sortedIndices.map(index => borderColors[index]);
new Chart(ctx, {
type: 'doughnut',
data: {
labels: sortedLocations,
datasets: [{
data: sortedCounts,
backgroundColor: sortedBackgroundColors,
borderColor: sortedBorderColors,
borderWidth: 1
}]
},
options: {
responsive: true,
maintainAspectRatio: false,
plugins: {
legend: {
position: 'right',
labels: {
color: 'white',
boxWidth: 15,
font: {
size: 10
}
}
},
title: {
display: true,
text: 'Assets by Location',
color: 'white',
font: {
size: 16
}
}
}
}
});
}
function generateColors(count, alpha) {
const colors = [];
const baseColors = [
`rgba(255, 99, 132, ${alpha})`,   // Red
`rgba(54, 162, 235, ${alpha})`,   // Blue
`rgba(255, 206, 86, ${alpha})`,   // Yellow
`rgba(75, 192, 192, ${alpha})`,   // Teal
`rgba(153, 102, 255, ${alpha})`,  // Purple
`rgba(255, 159, 64, ${alpha})`,   // Orange
`rgba(199, 199, 199, ${alpha})`,  // Gray
`rgba(83, 102, 255, ${alpha})`,   // Indigo
`rgba(255, 99, 255, ${alpha})`,   // Pink
`rgba(0, 190, 164, ${alpha})`     // Turquoise
];
for (let i = 0; i < count; i++) {
colors.push(baseColors[i % baseColors.length]);
}
return colors;
}