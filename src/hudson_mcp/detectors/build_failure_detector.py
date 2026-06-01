from __future__ import annotations
import re
from hudson_mcp import config
from hudson_mcp.schemas import Incident, DetectorContext
from hudson_mcp.redaction import redact_text

_TYPECHECK = re.compile(r"(?i)error TS\d+|mypy|type error|incompatible type")
# 良性ログ中の単語 "error" に過剰マッチさせない。失敗を示す形のみ検知。
_BUILD = re.compile(
    r"(?i)build failed|compilation failed|cannot find module|"
    r"\berror[:\[]|\bFAILED\b|fatal error|[1-9]\d*\s+errors?\b"
)


def _is_benign_line(line: str, benign_phrases: list[str]) -> bool:
    """行が良性句のみで説明できるなら True。"""
    lower = line.lower()
    return any(phrase.lower() in lower for phrase in benign_phrases)


def detect(build_output: str, recent_change: bool = True, revertable: bool = True,
           ctx: DetectorContext | None = None) -> Incident | None:
    _recent = ctx.recent_change if ctx is not None else recent_change
    _revert = ctx.revertable if ctx is not None else revertable
    benign = config.load_policy("build-policy").get("benign_error_phrases", [])
    is_typecheck = bool(_TYPECHECK.search(build_output))
    if not is_typecheck:
        non_benign = "\n".join(
            line for line in build_output.splitlines()
            if not _is_benign_line(line, benign)
        )
        if not _BUILD.search(non_benign):
            return None
    itype = "typecheck_failure" if is_typecheck else "build_failure"
    signals = {
        "build_failed": not is_typecheck,
        "typecheck_failed": is_typecheck,
        "recent_change_caused_failure": bool(_recent),
        "revertable": bool(_revert),
        "current_state_harms_value": True,
        "can_analyze_without_changes": True,
    }
    return Incident(
        incident_type=itype,
        severity="medium",
        description="ビルド/型チェックが失敗している",
        evidence={"snippet": redact_text(build_output[-300:])},
        signals=signals,
    )
