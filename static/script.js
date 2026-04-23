document.addEventListener('DOMContentLoaded', function() {
    // Check if we are on the dashboard (chartData exists)
    const dataEl = document.getElementById('chartData');
    if (!dataEl) return;

    try {
        const data = JSON.parse(dataEl.textContent);
        if (!data.labels || data.labels.length === 0) return;

        // Chart.js global defaults for dark theme
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true }
            }
        };

        // 1. Score Trend Chart
        const ctxScore = document.getElementById('scoreChart');
        if (ctxScore) {
            new Chart(ctxScore, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Health Score',
                        data: data.score,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    ...commonOptions,
                    scales: {
                        ...commonOptions.scales,
                        y: { min: 0, max: 100 }
                    }
                }
            });
        }

        // 2. Steps Chart (Bar)
        const ctxSteps = document.getElementById('stepsChart');
        if (ctxSteps) {
            new Chart(ctxSteps, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Steps',
                        data: data.steps,
                        backgroundColor: '#10b981',
                        borderRadius: 4
                    }]
                },
                options: commonOptions
            });
        }

        // 3. Sleep Chart (Line)
        const ctxSleep = document.getElementById('sleepChart');
        if (ctxSleep) {
            new Chart(ctxSleep, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Sleep Hours',
                        data: data.sleep,
                        borderColor: '#8b5cf6',
                        borderWidth: 2,
                        tension: 0.4
                    }]
                },
                options: commonOptions
            });
        }

    } catch (e) {
        console.error("Error parsing chart data", e);
    }
});

// Clear default zero values on focus
document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener('focus', function () {
        if (this.value === "0") {
            this.value = "";
        }
    });
});
