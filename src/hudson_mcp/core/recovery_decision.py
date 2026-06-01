# src/hudson_mcp/core/recovery_decision.py
from __future__ import annotations
from hudson_mcp import config
from hudson_mcp.schemas import (
    SituationAssessment, PurposeRecovery, RecoveryDecision, ScoredDecision,
)

def _build_ctx(sa: SituationAssessment, pr: PurposeRecovery) -> dict[str, bool]:
    ctx = dict(sa.signals)
    ctx["abandon_original_procedure"] = pr.abandon_original_procedure
    ctx["safe_limited_continuation_possible"] = pr.safe_limited_continuation_possible
    ctx["recoverability_preserved"] = pr.recoverability_preserved
    ctx["needs_human_judgment"] = pr.needs_human_judgment
    ctx["continue_risk_degrades"] = pr.continue_risk == "degrades"
    return ctx

def _clause_satisfied(clause: dict, ctx: dict[str, bool]) -> bool:
    if "any" in clause:
        return any(ctx.get(s, False) for s in clause["any"])
    if "all" in clause:
        return bool(clause["all"]) and all(ctx.get(s, False) for s in clause["all"])
    if "none" in clause:
        return all(not ctx.get(s, False) for s in clause["none"])
    return False

def _safety_active(ctx: dict[str, bool], safety_signals: list[str]) -> bool:
    # 絶対安全ゲートは secret/危険pkg/postinstall のみ。
    # 「復旧可能性が不明」は recoverability_unknown シグナルが stop 句(rank1)として作用させる
    # （revertable 未指定だけで stop に過剰反応させない）。
    return any(ctx.get(s, False) for s in safety_signals)

def _score_all(ctx, threatened, policy):
    """全 Decision の base/value/eligible を算出（incident_type は不使用）。"""
    scored: list[ScoredDecision] = []
    meta: dict[str, dict] = {}
    for name, d in policy["decisions"].items():
        meta[name] = {"rank": d["safety_rank"], "next_actions": d.get("next_actions", [])}
        labels = [c["label"] for c in d["when"] if _clause_satisfied(c, ctx)]
        base = len(labels)
        vscore = sum(14 - config.value_priority(v) for v in d.get("protects", []) if v in threatened)
        scored.append(ScoredDecision(
            decision=name, base_score=base, value_score=vscore,
            total=base + vscore, eligible=base > 0, matched_labels=labels,
        ))
    return scored, meta

def recommend(sa: SituationAssessment, pr: PurposeRecovery) -> RecoveryDecision:
    policy = config.load_policy("recovery-decision-policy")
    ctx = _build_ctx(sa, pr)
    threatened = set(pr.threatened_values) | set(pr.elevated_values)
    safety_on = _safety_active(ctx, policy.get("safety_signals", []))
    scored, meta = _score_all(ctx, threatened, policy)
    by_name = {s.decision: s for s in scored}

    def _result(name: str, reason: list[str]) -> RecoveryDecision:
        return RecoveryDecision(
            decision=name, reason=reason, scored=scored,
            recovered_purposes=pr.matched_purposes,
            threatened_values=pr.threatened_values,
            next_actions=meta[name]["next_actions"],
        )

    # 1. 安全ゲート（最優先価値の強制保護）→ stop
    if safety_on:
        labels = by_name["stop"].matched_labels
        return _result("stop", labels or ["復旧可能性/秘密情報/危険依存により最優先で停止"])

    # 2. 適格が無ければフェイルセーフ → pause_and_ask
    eligibles = [s for s in scored if s.eligible]
    if not eligibles:
        return _result("pause_and_ask", ["判定根拠が不足しているため人間判断へ戻す（フェイルセーフ）"])

    # 3. 適格な中で最も保護的（safety_rank 最小）を採用。
    # safety_rank 自体が value-hierarchy 由来の保護度順（＝価値起点の実機構）。
    # value_score は同 rank 時のタイブレーク（現状 rank は一意）＋ scored[] の透明性表示用。
    chosen = min(eligibles, key=lambda s: (meta[s.decision]["rank"], -s.value_score, -s.base_score))
    return _result(chosen.decision, chosen.matched_labels)
