# src/hudson_mcp/core/purpose_recovery.py
from __future__ import annotations
from hudson_mcp import config
from hudson_mcp.schemas import SituationAssessment, PurposeRecovery

def recover(sa: SituationAssessment, matched_rules: list[str],
            matched_purposes: list[str]) -> PurposeRecovery:
    purpose_map = config.load_purpose_map()
    sig = sa.signals
    g = lambda k: sig.get(k, False)

    # 脅かされている価値 = matched purpose の value のうち threat_signal が立つもの
    threatened: list[str] = []
    recovered_meaning: list[str] = []
    for pid in matched_purposes:
        p = purpose_map.get(pid)
        if not p:
            continue
        if any(g(s) for s in p.get("threat_signals", [])):
            if p["value"] not in threatened:
                threatened.append(p["value"])
            recovered_meaning.append(
                f"{p['name']}は単なる手順ではなく『{ '・'.join(p.get('protects', [])[:2]) }』を守るために存在していた"
            )

    elevated = sorted(set(threatened), key=config.value_priority)

    continue_risk = "degrades" if (g("damage_spreads_if_continue") or g("continue_leaves_damage")) else "recovers"
    abandon = bool(g("current_approach_destructive") or g("value_loss_detected")
                   or g("secret_possibly_read") or g("secret_exposed")
                   or g("secret_propagated") or g("dangerous_package_present"))
    recoverability_preserved = bool(g("revertable")) and not (
        g("unrecoverable_change_detected") or g("recoverability_unknown"))
    needs_human = bool(g("spec_change_needed") or g("api_compat_risk")
                       or g("requirement_spec_conflict")
                       or (g("dangerous_package_present") and g("recoverability_unknown")))
    safe_limited = bool(g("scope_limited")) and not g("damage_spreads_if_continue")

    # 最も避けるべき被害 = 最優先 threatened value の prevents 先頭
    worst_harm = ""
    if elevated:
        top_value = elevated[0]
        for pid in matched_purposes:
            p = purpose_map.get(pid)
            if p and p["value"] == top_value and p.get("prevents"):
                worst_harm = p["prevents"][0]
                break

    answers = {
        "constraint_purpose": "; ".join(recovered_meaning) or "関連制約の保護対象",
        "current_threat": f"{'・'.join(threatened)} が脅かされている" if threatened else "明確な脅威なし",
        "continue_risk": continue_risk,
        "elevated_values": elevated,
        "abandon_original_procedure": abandon,
        "worst_harm": worst_harm,
        "safe_limited_continuation_possible": safe_limited,
        "recoverability_preserved": recoverability_preserved,
        "needs_human_judgment": needs_human,
    }
    return PurposeRecovery(
        matched_rules=matched_rules,
        matched_purposes=matched_purposes,
        recovered_meaning=recovered_meaning,
        threatened_values=threatened,
        elevated_values=elevated,
        continue_risk=continue_risk,
        abandon_original_procedure=abandon,
        worst_harm=worst_harm,
        safe_limited_continuation_possible=safe_limited,
        recoverability_preserved=recoverability_preserved,
        needs_human_judgment=needs_human,
        answers=answers,
    )
