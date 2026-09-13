import pandas as pd

class NetworkRuleChecker:    
    def __init__(self):
        pass

    def check_all(self, show_outputs: str = "", symptom: str = "") -> list:
        findings = []
        
        outputs_lower = show_outputs.lower() if show_outputs else ""
        symptom_lower = symptom.lower() if symptom else ""

        if "shutdown" in outputs_lower or "administratively down" in outputs_lower:
            findings.append({
                "rule": "Interface Status Check",
                "status": "Warning",
                "message": "Interface or line protocol is administratively down."
            })

        if "no ip routing" in outputs_lower:
            findings.append({
                "rule": "IP Routing Configuration",
                "status": "Critical",
                "message": "IP routing is explicitly disabled on the device."
            })

        if "duplex mismatch" in outputs_lower or "collitions" in outputs_lower or "collisions" in outputs_lower:
            findings.append({
                "rule": "Layer 1/2 Framing Check",
                "status": "Warning",
                "message": "Potential duplex or interface error indicators found in logs."
            })

        if not findings:
            findings.append({
                "rule": "Deterministic Baseline",
                "status": "Passed",
                "message": "No critical layer-1 or structural configuration rule flags triggered."
            })

        return findings

def check_ip_configuration(df):
    issues = []
    if df.empty:
        return issues
    
    for index, row in df.iterrows():
        symptom = str(row.get("symptom", "")).lower()
        show_output = str(row.get("show_outputs", "")).lower()
        
        if "ip address" in symptom and "unassigned" in show_output:
            issues.append({
                "case_id": row.get("case_id", f"Row-{index}"),
                "rule": "IP Assignment Check",
                "message": "Interface appears unassigned despite IP configuration symptom."
            })
    return issues

def run_all_checks(df):
    all_issues = []
    all_issues.extend(check_ip_configuration(df))
    return all_issues
