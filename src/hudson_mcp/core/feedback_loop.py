# src/hudson_mcp/core/feedback_loop.py
from __future__ import annotations
from hudson_mcp import config
from hudson_mcp.schemas import Feedback

def generate(incident_type: str) -> Feedback:
    pol = config.load_policy("feedback-policy")
    entry = pol["by_incident_type"].get(incident_type, {})
    default = pol["default"]
    return Feedback(
        harness_rule_suggestion=entry.get("harness_rule_suggestion", default.get("harness_rule_suggestion", [])),
        rule_map_update_candidate=entry.get("rule_map_update_candidate", []),
        purpose_map_update_candidate=entry.get("purpose_map_update_candidate", []),
        detector_improvement_candidate=entry.get("detector_improvement_candidate", default.get("detector_improvement_candidate", [])),
    )
