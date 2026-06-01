# src/hudson_mcp/detectors/scope_expansion_detector.py
from __future__ import annotations
from hudson_mcp import config
from hudson_mcp.schemas import Incident, DetectorContext


def _count_code_lines(diff_text: str) -> int:
    """diff の追加・削除行のうち空行・コメント行を除いた実コード行数。"""
    count = 0
    for line in diff_text.splitlines():
        if not (line.startswith("+") or line.startswith("-")):
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        content = line[1:].strip()
        if not content:
            continue
        if content.startswith(("#", "//", "*", "/*", "<!--")):
            continue
        count += 1
    return count


def detect(intended: list[str], changed: list[str], changed_lines: int = 0,
           ctx: DetectorContext | None = None) -> Incident | None:
    _revert = ctx.revertable if ctx is not None else True
    pol = config.load_policy("scope-policy")
    # ctx.diff_text があればコード行のみカウント（コメント・空行を除外）
    effective_lines = _count_code_lines(ctx.diff_text) if (ctx and ctx.diff_text) else changed_lines
    intended_set = set(intended)
    outside = [p for p in changed if intended_set and p not in intended_set]
    too_big = (
        len(changed) >= pol["large_diff_files"]
        or effective_lines >= pol["large_diff_lines"]
    )
    expanded = bool(outside) or too_big
    if not changed:
        return None
    signals = {
        "scope_expansion_detected": expanded,
        "scope_limited": not expanded,
        "unexpected_file_change": bool(outside),
        "smaller_change_possible": expanded,
        "revertable": _revert,
    }
    return Incident(
        incident_type="scope_expansion" if expanded else "unexpected_file_change",
        severity="medium",
        description="目的外/想定外の範囲へ変更が波及した可能性" if expanded else "変更は意図範囲内",
        affected_files=outside or changed,
        evidence={"outside": outside, "changed_count": len(changed),
                  "effective_lines": effective_lines},
        signals=signals,
    )
