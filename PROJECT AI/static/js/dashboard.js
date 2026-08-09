// Dashboard analytics visualizations using Chart.js
function initDashboardCharts(historyLabels, historyScores, categoryData) {
    // 1. Performance Trend Line Chart
    const trendCtx = document.getElementById('performanceChart');
    if (trendCtx) {
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: historyLabels.length ? historyLabels : ['Session 1'],
                datasets: [{
                    label: 'Interview Score (%)',
                    data: historyScores.length ? historyScores : [0],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#a855f7',
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.08)' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });
    }

    // 2. Category Radar Chart
    const radarCtx = document.getElementById('categoryRadarChart');
    if (radarCtx && categoryData) {
        new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: Object.keys(categoryData),
                datasets: [{
                    label: 'Competency Rating',
                    data: Object.values(categoryData),
                    backgroundColor: 'rgba(6, 182, 212, 0.25)',
                    borderColor: '#06b6d4',
                    borderWidth: 2,
                    pointBackgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: { color: '#f8fafc', font: { size: 12, weight: '600' } },
                        ticks: { display: false }
                    }
                }
            }
        });
    }
}
