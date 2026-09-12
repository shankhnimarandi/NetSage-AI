import os
import sys
import pandas as pd
import pytest

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from validation.network_rules import check_ip_configuration, run_all_checks

def test_ip_configuration_rule():
    """Test that the IP configuration check correctly flags unassigned interfaces."""
    data = {
        "case_id": ["CASE-001", "CASE-002"],
        "symptom": ["Issue with IP address configuration", "BGP peering down"],
        "show_outputs": ["interface GigabitEthernet0/1 is unassigned", "BGP state is Idle"]
    }
    df = pd.DataFrame(data)
    
    issues = check_ip_configuration(df)
    
    assert len(issues) == 1
    assert issues[0]["case_id"] == "CASE-001"
    assert issues[0]["rule"] == "IP Assignment Check"

def test_run_all_checks_empty():
    """Test that running checks on an empty DataFrame returns no issues."""
    empty_df = pd.DataFrame()
    issues = run_all_checks(empty_df)
    assert len(issues) == 0