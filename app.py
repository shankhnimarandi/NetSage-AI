import os

import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for

from config import Config
from ai.gemini_service import GeminiDiagnosisService
from retrieval.case_retrieval import CaseRetrievalEngine
from validation.network_rules import NetworkRuleChecker
from review.review_manager import ReviewManager
from database.database import init_db, db


app = Flask(__name__)
app.config.from_object(Config)

init_db(app)


retrieval_engine = CaseRetrievalEngine()
diagnosis_service = GeminiDiagnosisService()
rule_checker = NetworkRuleChecker()
review_manager = ReviewManager()


def get_normalized_cases():
    """Load cases and normalize column headers to prevent blank fields."""
    df = retrieval_engine.cases_df

    if df is not None and not df.empty:
        df = df.dropna(how="all").copy()

        df.columns = [
            str(column).strip().lower().replace(" ", "_")
            for column in df.columns
        ]

        rename_map = {}

        for column in df.columns:
            if "fault" in column or "expected" in column:
                rename_map[column] = "fault"

            elif (
                "concept" in column
                or "domain" in column
                or "category" in column
            ):
                rename_map[column] = "concept"

            elif "osi" in column:
                rename_map[column] = "osi_layer"

            elif "symptom" in column:
                rename_map[column] = "symptom"

            elif "severity" in column:
                rename_map[column] = "severity"

            elif "case" in column and "id" in column:
                rename_map[column] = "case_id"

        df = df.rename(columns=rename_map)

        return df.to_dict(orient="records")

    return []


@app.route("/")
def index():
    """Render the network troubleshooting console."""
    cases = get_normalized_cases()

    return render_template(
        "index.html",
        cases=cases
    )


@app.route('/health')
def health_check():
    return "OK", 200


@app.route("/diagnose", methods=["POST"])
def diagnose():
    """Handle diagnosis requests using Gemini, RAG, and rule checking."""
    data = request.get_json() or {}

    case_id = data.get("case_id", "CUSTOM-CASE")
    symptom = data.get("symptom", "")
    topology_note = data.get("topology_note", "")
    show_outputs = data.get("show_outputs", "")

    if not symptom:
        return jsonify({
            "error": "Symptom input is required."
        }), 400

    query_text = f"{symptom} {topology_note} {show_outputs}"

    retrieved_cases = retrieval_engine.search(
        query_text,
        k=3
    )

    rule_results = rule_checker.check_all(
        show_outputs=show_outputs,
        symptom=symptom
    )

    ai_result = diagnosis_service.diagnose(
        symptom=symptom,
        topology_note=topology_note,
        show_outputs=show_outputs,
        retrieved_context=retrieved_cases
    )

    ai_result["case_id"] = case_id
    ai_result["rule_findings"] = rule_results
    ai_result["retrieved_cases"] = retrieved_cases

    return jsonify(ai_result)


@app.route("/submit_review", methods=["POST"])
def submit_review():
    """Save human review decisions."""
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict()

    case_id = data.get("case_id")
    decision = data.get("decision")
    notes = data.get("notes", "")

    if not case_id or not decision:
        return jsonify({
            "error": "Case ID and review decision are required."
        }), 400

    success = review_manager.save_review(
        case_id=case_id,
        decision=decision,
        notes=notes
    )

    if success:
        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            return jsonify({
                "status": "success",
                "message": "Review logged successfully."
            })

        return redirect(url_for("analytics"))

    if (
        request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        return jsonify({
            "error": "Failed to log review."
        }), 500

    return redirect(url_for("analytics"))


@app.route("/analytics")
def analytics():
    """Render the analytics dashboard with metrics and audit logs."""

    review_logs = ReviewManager.get_all_reviews()
    metrics = ReviewManager.get_metrics()
    analytics_stats = ReviewManager.get_analytics_stats()

    # ---------------------------------------------------------
    # Prepare case distribution data
    # ---------------------------------------------------------
    df = retrieval_engine.cases_df

    if df is not None and not df.empty:
        df = df.dropna(how="all").copy()

        df.columns = [
            str(column).strip().lower().replace(" ", "_")
            for column in df.columns
        ]

        domain_key = next(
            (
                column
                for column in df.columns
                if (
                    "concept" in column
                    or "domain" in column
                    or "category" in column
                )
            ),
            None
        )

        severity_key = next(
            (
                column
                for column in df.columns
                if "severity" in column
            ),
            None
        )

        issue_distribution = (
            df[domain_key].value_counts().to_dict()
            if domain_key
            else {}
        )

        severity_distribution = (
            df[severity_key].value_counts().to_dict()
            if severity_key
            else {}
        )

        total_cases = len(df)

    else:
        issue_distribution = {}
        severity_distribution = {}
        total_cases = 0

    # ---------------------------------------------------------
    # Render analytics dashboard
    # ---------------------------------------------------------
    return render_template(
        "analytics.html",
        review_logs=review_logs,
        metrics=metrics,
        analytics_stats=analytics_stats,
        total_cases=total_cases,
        issue_distribution=issue_distribution,
        severity_distribution=severity_distribution
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
