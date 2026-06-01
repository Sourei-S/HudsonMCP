from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

class DetectorContext(BaseModel):
    diff_text: str | None = None
    before_symbols: list[str] | None = None
    after_symbols: list[str] | None = None
    changed_signatures: list[dict[str, str]] | None = None
    blame_info: dict[str, str] | None = None
    revertable: bool = True
    recent_change: bool = True

Severity = Literal["low", "medium", "high", "critical"]
DecisionName = Literal[
    "continue_limited", "rollback", "safe_alternative",
    "pause_and_ask", "stop", "document_only",
]

class Incident(BaseModel):
    incident_type: str
    severity: Severity = "medium"
    description: str = ""
    affected_files: list[str] = Field(default_factory=list)
    evidence: dict = Field(default_factory=dict)
    signals: dict[str, bool] = Field(default_factory=dict)

class SituationAssessment(BaseModel):
    triggered: bool = False
    incidents: list[Incident] = Field(default_factory=list)
    primary_incident_type: str = ""
    severity: Severity = "low"
    affected_files: list[str] = Field(default_factory=list)
    signals: dict[str, bool] = Field(default_factory=dict)

class PurposeRecovery(BaseModel):
    matched_rules: list[str] = Field(default_factory=list)
    matched_purposes: list[str] = Field(default_factory=list)
    recovered_meaning: list[str] = Field(default_factory=list)
    threatened_values: list[str] = Field(default_factory=list)
    elevated_values: list[str] = Field(default_factory=list)
    continue_risk: Literal["recovers", "degrades"] = "recovers"
    abandon_original_procedure: bool = False
    worst_harm: str = ""
    safe_limited_continuation_possible: bool = False
    recoverability_preserved: bool = True
    needs_human_judgment: bool = False
    answers: dict = Field(default_factory=dict)

class ScoredDecision(BaseModel):
    decision: DecisionName
    base_score: int = 0
    value_score: int = 0
    total: int = 0
    eligible: bool = False
    matched_labels: list[str] = Field(default_factory=list)

class RecoveryDecision(BaseModel):
    decision: DecisionName
    reason: list[str] = Field(default_factory=list)
    scored: list[ScoredDecision] = Field(default_factory=list)
    recovered_purposes: list[str] = Field(default_factory=list)
    threatened_values: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)

class Feedback(BaseModel):
    harness_rule_suggestion: list[str] = Field(default_factory=list)
    rule_map_update_candidate: list[dict] = Field(default_factory=list)
    purpose_map_update_candidate: list[dict] = Field(default_factory=list)
    detector_improvement_candidate: list[str] = Field(default_factory=list)
