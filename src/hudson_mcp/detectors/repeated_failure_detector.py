# src/hudson_mcp/detectors/repeated_failure_detector.py
from __future__ import annotations
from collections import Counter
from hudson_mcp.schemas import Incident, DetectorContext
from hudson_mcp.redaction import redact_text

THRESHOLD = 3

def detect(error_signatures: list[str], threshold: int = THRESHOLD,
           ctx: DetectorContext | None = None) -> Incident | None:
    if not error_signatures:
        return None
    most_common, count = Counter(error_signatures).most_common(1)[0]
    if count < threshold:
        return None
    return Incident(
        incident_type="repeated_failure",
        severity="medium",
        description=f"同一エラーが {count} 回反復している",
        evidence={"signature": redact_text(most_common), "count": count},
        signals={
            "repeated_failure_detected": True,
            "current_approach_destructive": True,
            "smaller_change_possible": True,
            "continue_leaves_damage": True,
            "can_analyze_without_changes": True,
            "revertable": True,
        },
    )
