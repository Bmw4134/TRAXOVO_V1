// billing_chart.js
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
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

document.querySelectorAll(".timeframe-toggle").forEach(btn => {
    btn.addEventListener("click", () => {
        const days = parseInt(btn.dataset.days);
        renderBillingChart(window.billingData, days);
    });
});
