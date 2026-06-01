# src/hudson_mcp/detectors/value_loss_detector.py
from __future__ import annotations
from hudson_mcp.schemas import Incident, DetectorContext

def detect(tests_passed: bool, spec_intent_violated: bool,
           quality_degraded: bool, error_suppressed: bool,
           ctx: DetectorContext | None = None) -> Incident | None:
    if spec_intent_violated:
        itype = "test_passed_but_spec_lost"
    elif error_suppressed:
        itype = "error_suppressed_without_root_cause"
    elif quality_degraded:
        itype = "rule_followed_but_value_lost"
    else:
        return None
    return Incident(
        incident_type=itype,
        severity="medium",
        description="手順/ルールには従ったが守るべき価値を損なった",
        signals={
            "value_loss_detected": True,
            "current_approach_destructive": spec_intent_violated,
            "smaller_change_possible": True,
            "continue_leaves_damage": True,
            "revertable": True,
            "can_analyze_without_changes": True,
            "spec_change_needed": spec_intent_violated,
        },
    )
