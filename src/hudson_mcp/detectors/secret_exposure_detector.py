# src/hudson_mcp/detectors/secret_exposure_detector.py
from __future__ import annotations
import re
from hudson_mcp import config
from hudson_mcp.schemas import Incident, DetectorContext


def _diff_added_text(diff_text: str) -> str:
    """diff の追加行（+ 始まり、+++ 除く）のみ抽出。"""
    return "\n".join(
        line[1:] for line in diff_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )


def detect(text: str, ctx: DetectorContext | None = None) -> Incident | None:
    patterns = config.load_policy("secret-policy")["value_patterns"]
    scan_text = text
    if ctx and ctx.diff_text:
        scan_text = text + "\n" + _diff_added_text(ctx.diff_text)
    matched = [p for p in patterns if re.search(p, scan_text)]
    if not matched:
        return None
    return Incident(
        incident_type="secret_exposure",
        severity="critical",
        description="秘密情報の実値が出力・保存・送信された可能性",
        affected_files=[],
        evidence={"matched_pattern_count": len(matched), "value": "<REDACTED>"},
        signals={"secret_exposed": True},
    )
