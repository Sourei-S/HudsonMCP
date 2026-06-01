# src/hudson_mcp/detectors/api_break_detector.py
from __future__ import annotations
import re
from hudson_mcp.schemas import Incident, DetectorContext

_EXPORT_DEL = re.compile(
    r"^-.*\b(export|public|interface|type)\s+\w+",
    re.MULTILINE,
)
_FUNC_NAME = re.compile(
    r"\b(?:def|function|func|fn)\s+(\w+)\s*\(",
    re.MULTILINE,
)


def _count_args(sig: str) -> list[str]:
    """シグネチャ文字列から引数リストを返す（カンマ分割・概算）。"""
    m = re.search(r"\(([^)]*)\)", sig)
    if not m:
        return []
    return [a.strip() for a in m.group(1).split(",") if a.strip()]


def _has_default(arg: str) -> bool:
    return "=" in arg


def _check_signatures(changed_signatures: list[dict[str, str]]) -> bool:
    """True = 非互換変更あり。"""
    for entry in changed_signatures:
        before = entry.get("before", "")
        after = entry.get("after", "")
        if not before or not after:
            continue
        b_args = _count_args(before)
        a_args = _count_args(after)
        # 必須引数追加: 引数数増加かつ追加引数にデフォルト値なし
        if len(a_args) > len(b_args):
            new_args = a_args[len(b_args):]
            if any(not _has_default(a) for a in new_args):
                return True
        # 戻り型変更
        b_ret = re.search(r"->\s*(.+?)(?:\s*:|$)", before)
        a_ret = re.search(r"->\s*(.+?)(?:\s*:|$)", after)
        if b_ret and a_ret and b_ret.group(1).strip() != a_ret.group(1).strip():
            return True
    return False


def detect(
    before_symbols: list[str] | None = None,
    after_symbols: list[str] | None = None,
    changed_signatures: list[dict[str, str]] | None = None,
    ctx: DetectorContext | None = None,
) -> Incident | None:
    has_symbols = before_symbols is not None and after_symbols is not None
    has_sigs = bool(changed_signatures)
    has_diff = bool(ctx and ctx.diff_text)

    if not (has_symbols or has_sigs or has_diff):
        return None

    api_break = False
    api_compat = False

    # detection_mode = 一次検知ソース（symbols > signatures > diff_heuristic の優先順）。
    # changed_signatures は mode に関わらず、提供されていれば常に api_compat_risk チェックに使う。
    if has_symbols:
        detection_mode = "symbols"
        removed = set(before_symbols) - set(after_symbols)
        if removed:
            api_break = True
    elif has_sigs:
        detection_mode = "signatures"
    else:
        detection_mode = "diff_heuristic"

    if has_sigs:
        if _check_signatures(changed_signatures):
            api_compat = True

    # diff heuristic は symbols/signatures 未提供時のフォールバック。
    # symbols がある場合は diff を無視する（symbols の方が精度が高いため）。
    if not has_symbols and has_diff:
        if _EXPORT_DEL.search(ctx.diff_text):
            api_break = True
        del_funcs = set(_FUNC_NAME.findall(
            "\n".join(l for l in ctx.diff_text.splitlines() if l.startswith("-"))
        ))
        add_funcs = set(_FUNC_NAME.findall(
            "\n".join(l for l in ctx.diff_text.splitlines() if l.startswith("+"))
        ))
        if del_funcs & add_funcs:
            api_compat = True

    if not api_break and not api_compat:
        return None

    _revert = ctx.revertable if ctx is not None else True
    severity = "medium" if detection_mode == "diff_heuristic" else "high"

    return Incident(
        incident_type="api_break",
        severity=severity,
        description="公開APIの破壊的変更（シンボル削除または署名非互換変更）",
        evidence={
            "api_break_detected": api_break,
            "api_compat_risk": api_compat,
            "detection_mode": detection_mode,
        },
        signals={
            "api_break_detected": api_break,
            "api_compat_risk": api_compat,
            "spec_change_needed": True,
            "revertable": _revert,
            "current_state_harms_value": True,
        },
    )
