# src/hudson_mcp/detectors/secret_propagation_detector.py
from __future__ import annotations
import re
from hudson_mcp import config
from hudson_mcp.schemas import Incident, DetectorContext


def _diff_context_text(diff_text: str) -> str:
    """diff の +/-/ 行（ヘッダ除く）のコンテキスト行テキストを返す。"""
    lines = []
    for line in diff_text.splitlines():
        if line.startswith(("+++", "---", "@@")):
            continue
        if line.startswith(("+", "-", " ")):
            lines.append(line[1:])
    return "\n".join(lines)


def detect(followup_text: str, secret_was_accessed: bool,
           ctx: DetectorContext | None = None) -> Incident | None:
    if not secret_was_accessed:
        return None
    patterns = config.load_policy("secret-policy")["key_name_patterns"]
    check_text = followup_text
    if ctx and ctx.diff_text:
        check_text = followup_text + "\n" + _diff_context_text(ctx.diff_text)
    if not any(re.search(p, check_text) for p in patterns):
        return None
    return Incident(
        incident_type="secret_propagation",
        severity="critical",
        description="読み取った秘密情報が後続出力に混入した可能性",
        evidence={"value": "<REDACTED>"},
        signals={"secret_propagated": True},
    )
