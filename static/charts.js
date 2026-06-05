document.addEventListener("DOMContentLoaded", function () {

    if (typeof categoryData !== "undefined") {
        const labels = Object.keys(categoryData);
        const values = Object.values(categoryData);

        if (labels.length > 0) {
            new Chart(document.getElementById("pieChart"), {
                type: "pie",
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: [
                            "#FF6384","#36A2EB","#FFCE56",
                            "#4BC0C0","#9966FF","#FF9F40","#C9CBCF"
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: "bottom" } }
                }
            });
        }
    }

    if (typeof monthlyData !== "undefined") {
        const months = Object.keys(monthlyData);
        const incomes = months.map(m => monthlyData[m].income);
        const expenses = months.map(m => monthlyData[m].expense);

        if (months.length > 0) {
            new Chart(document.getElementById("barChart"), {
                type: "bar",
                data: {
                    labels: months,
                    datasets: [
                        {
                            label: "Income",
                            data: incomes,
                            backgroundColor: "#28a745"
                        },
                        {
                            label: "Expenses",
                            data: expenses,
                            backgroundColor: "#dc3545"
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: "top" } },
                    scales: { y: { beginAtZero: true } }
                }
            });
        }
    }
});