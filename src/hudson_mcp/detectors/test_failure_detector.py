# src/hudson_mcp/detectors/test_failure_detector.py
from __future__ import annotations
import re
from hudson_mcp.schemas import Incident, DetectorContext
from hudson_mcp.redaction import redact_text

# 「0 failed」は合格なので除外（[1-9]\d* のみ）。FAILED は大文字トークンのみ検知。
_FAIL = re.compile(r"[1-9]\d*\s+failed|\bFAILED\b|AssertionError|✗|✖")

def detect(test_output: str, recent_change: bool = True, revertable: bool = True,
           ctx: DetectorContext | None = None) -> Incident | None:
    _recent = ctx.recent_change if ctx is not None else recent_change
    _revert = ctx.revertable if ctx is not None else revertable
    if not _FAIL.search(test_output):
        return None
    return Incident(
        incident_type="test_regression",
        severity="medium",
        description="既存テストが失敗している",
        evidence={"snippet": redact_text(test_output[-300:])},
        signals={
            "test_failed": True,
            "recent_change_caused_failure": bool(_recent),
            "revertable": bool(_revert),
            "current_state_harms_value": True,
            "can_analyze_without_changes": True,
        },
    )
