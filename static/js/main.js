document.addEventListener("DOMContentLoaded", () => {
    console.log("NetSage: Initializing state persistence...");

    const diagnoseForm = document.getElementById("diagnose-form");
    const loadingState = document.getElementById("loading-state");
    const resultsContainer = document.getElementById("results-container");
    const reviewForm = document.getElementById("review-form");

    const inputIds = [
        "case-select", "case_id",
        "symptom-input", "symptom",
        "topology-input", "topology_note",
        "show-outputs-input", "show_outputs"
    ];

    inputIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            const savedValue = localStorage.getItem("netsage_input_" + id);
            if (savedValue !== null && savedValue !== "") {
                element.value = savedValue;
                element.dispatchEvent(new Event("input", { bubbles: true }));
                element.dispatchEvent(new Event("change", { bubbles: true }));
                console.log(`Restored field [${id}] with value:`, savedValue);
            }

            element.addEventListener("input", () => {
                localStorage.setItem("netsage_input_" + id, element.value);
            });
            element.addEventListener("change", () => {
                localStorage.setItem("netsage_input_" + id, element.value);
            });
        }
    });

    const savedResults = localStorage.getItem("netsage_last_results");
    if (savedResults && resultsContainer) {
        try {
            const data = JSON.parse(savedResults);
            populateResultsData(data);
        } catch (e) {
            console.error("Error parsing saved results:", e);
        }
    }

    if (diagnoseForm) {
        diagnoseForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const caseIdInput = document.getElementById("case_id") || document.getElementById("case-select");
            const symptomInput = document.getElementById("symptom") || document.getElementById("symptom-input");
            const topologyInput = document.getElementById("topology_note") || document.getElementById("topology-input");
            const showOutputsInput = document.getElementById("show_outputs") || document.getElementById("show-outputs-input");

            const caseId = caseIdInput ? caseIdInput.value : "";
            const symptom = symptomInput ? symptomInput.value : "";
            const topology = topologyInput ? topologyInput.value : "";
            const showOutputs = showOutputsInput ? showOutputsInput.value : "";

            if (loadingState) loadingState.style.display = "block";
            if (resultsContainer) resultsContainer.style.display = "none";

            try {
                const response = await fetch("/diagnose", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        case_id: caseId,
                        symptom: symptom,
                        topology_note: topology,
                        show_outputs: showOutputs
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    localStorage.setItem("netsage_last_results", JSON.stringify(data));
                    populateResultsData(data);
                } else {
                    alert("Error during diagnosis: " + (data.error || "Unknown error"));
                }
            } catch (err) {
                console.error("Network or parsing error:", err);
                alert("Failed to connect to NetSage AI server.");
            } finally {
                if (loadingState) loadingState.style.display = "none";
            }
        });
    }

    if (reviewForm) {
        reviewForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const caseId = document.getElementById("review-case-id").value;
            const decision = document.querySelector('input[name="decision"]:checked');
            const notes = document.getElementById("review-notes").value;

            if (!decision) {
                alert("Please select a review decision (Accepted, Edited, or Rejected).");
                return;
            }

            try {
                const response = await fetch("/submit_review", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        case_id: caseId,
                        decision: decision.value,
                        notes: notes
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    alert("Human review successfully logged!");
                    window.location.href = "/analytics";
                } else {
                    alert("Error saving review: " + (data.error || "Unknown error"));
                }
            } catch (err) {
                console.error("Error submitting review:", err);
                alert("Failed to submit review log.");
            }
        });
    }
});

function populateResultsData(data) {
    const resultsContainer = document.getElementById("results-container");
    if (!resultsContainer) return;

    document.getElementById("res-root-cause").textContent = data.root_cause || "N/A";
    document.getElementById("res-confidence").textContent = data.confidence || "N/A";
    document.getElementById("res-osi").textContent = data.osi_layer || "N/A";
    document.getElementById("res-evidence").textContent = data.evidence || "N/A";
    document.getElementById("res-next-command").textContent = data.next_command || "N/A";

    const fixStepsList = document.getElementById("res-fix-steps");
    if (fixStepsList) {
        fixStepsList.innerHTML = "";
        if (data.fix_steps && Array.isArray(data.fix_steps)) {
            data.fix_steps.forEach(step => {
                const li = document.createElement("li");
                li.textContent = step;
                fixStepsList.appendChild(li);
            });
        }
    }

    const reviewCaseIdInput = document.getElementById("review-case-id");
    if (reviewCaseIdInput) {
        reviewCaseIdInput.value = data.case_id || "CUSTOM-CASE";
    }

    resultsContainer.style.display = "block";
}