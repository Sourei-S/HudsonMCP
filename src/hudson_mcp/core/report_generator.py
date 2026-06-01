# src/hudson_mcp/core/report_generator.py
from __future__ import annotations
from hudson_mcp.schemas import SituationAssessment, PurposeRecovery, RecoveryDecision, Feedback

def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items) if items else "- （なし）"

def render(sa: SituationAssessment, pr: PurposeRecovery,
           d: RecoveryDecision, fb: Feedback) -> str:
    a = pr.answers
    return f"""## Hudson Switch 起動

### 発生した異常
{ _bullets([i.description for i in sa.incidents] or [sa.primary_incident_type]) }

### Incident Type
{sa.primary_incident_type}

### Severity
{sa.severity}

### 通常作業を停止する理由
- 異常検知により通常手順を継続すると守るべき価値を損なう可能性があるため

### 影響範囲
{ _bullets(sa.affected_files) }

### 関連する制約
{ _bullets(pr.matched_rules) }

### Purpose Recovery
- この制約が守ろうとしていたもの：{ a.get("constraint_purpose", "") }
- 現在脅かされている価値：{ "・".join(pr.threatened_values) or "（なし）" }
- 通常手順を続けた場合のリスク：{ pr.continue_risk }
- 元の手順を捨てる必要：{ pr.abandon_original_procedure }
- 最も避けるべき被害：{ pr.worst_harm or "（特定なし）" }
- 復旧可能性は保たれているか：{ pr.recoverability_preserved }
- 人間判断に戻すべきか：{ pr.needs_human_judgment }

### 守るべき価値
{ _bullets(pr.elevated_values or pr.threatened_values) }

### 推奨判断
{d.decision}

理由:
{ _bullets(d.reason) }

### 次の限定行動
{ _bullets(d.next_actions) }

### Feedback Loop
- harness_rule_suggestion: { "; ".join(fb.harness_rule_suggestion) or "（なし）" }
- detector_improvement_candidate: { "; ".join(fb.detector_improvement_candidate) or "（なし）" }

### 注意
通常作業を継続せず、上記の復旧判断に切り替えること。
"""
