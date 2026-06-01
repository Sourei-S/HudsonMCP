# src/hudson_mcp/core/situation_assessment.py
from __future__ import annotations
from hudson_mcp import config
from hudson_mcp.schemas import Incident, SituationAssessment

def _severity_rank(sev: str) -> int:
    order = config.load_policy("severity-policy")["order"]
    return order.index(sev) if sev in order else 0

def _derive_composite(sig: dict[str, bool]) -> dict[str, bool]:
    """基本シグナルから複合シグナルを合成する（決定エンジンの入力）。"""
    g = lambda k: sig.get(k, False)
    sig.setdefault("damage_spreads_if_continue",
        g("secret_propagated") or g("postinstall_executed")
        or g("unexpected_network_activity") or g("dangerous_package_present"))
    sig.setdefault("recoverability_unknown",
        (g("postinstall_executed") or g("unexpected_network_activity")
         or g("unrecoverable_change_detected")) and not g("revertable"))
    sig.setdefault("continue_leaves_damage",
        g("value_loss_detected") or g("api_break_detected") or g("current_approach_destructive"))
    # value_loss は rollback でなく safe_alternative が正なので current_state_harms_value から除外
    sig.setdefault("current_state_harms_value",
        g("test_failed") or g("build_failed") or g("typecheck_failed") or g("secret_exposed"))
    return sig

def assess(incidents: list[Incident]) -> SituationAssessment:
    if not incidents:
        return SituationAssessment(triggered=False)
    merged: dict[str, bool] = {}
    affected: list[str] = []
    for inc in incidents:
        for k, v in inc.signals.items():
            merged[k] = merged.get(k, False) or v
        affected.extend(inc.affected_files)
    _derive_composite(merged)
    primary = max(incidents, key=lambda i: _severity_rank(i.severity))
    return SituationAssessment(
        triggered=True,
        incidents=incidents,
        primary_incident_type=primary.incident_type,
        severity=primary.severity,
        affected_files=sorted(set(affected)),
        signals=merged,
    )
