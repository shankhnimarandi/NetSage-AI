document.addEventListener("DOMContentLoaded", () => {
    initDecisionRatesChart();
});


function initDecisionRatesChart() {
    const canvas = document.getElementById("decisionRatesChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const accepted = parseFloat(
        canvas.dataset.accepted || "0"
    );

    const edited = parseFloat(
        canvas.dataset.edited || "0"
    );

    const rejected = parseFloat(
        canvas.dataset.rejected || "0"
    );

    new Chart(canvas, {
        type: "bar",

        data: {
            labels: [
                "Accepted",
                "Edited",
                "Rejected"
            ],

            datasets: [
                {
                    label: "Decision Rate",

                    data: [
                        accepted,
                        edited,
                        rejected
                    ],

                    borderWidth: 1,
                    borderRadius: 6
                }
            ]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,

                    ticks: {
                        callback: function (value) {
                            return value + "%";
                        }
                    }
                }
            },

            plugins: {
                legend: {
                    display: false
                },

                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.raw + "%";
                        }
                    }
                }
            }
        }
    });
}