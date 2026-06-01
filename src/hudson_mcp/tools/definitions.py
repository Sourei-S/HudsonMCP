# src/hudson_mcp/tools/definitions.py
from __future__ import annotations
from hudson_mcp.schemas import Incident, SituationAssessment, PurposeRecovery
from hudson_mcp.core import (
    situation_assessment, constraint_lookup, purpose_recovery,
    value_reprioritization, recovery_decision, feedback_loop, report_generator,
)
from hudson_mcp.detectors import (
    secret_access_detector, secret_exposure_detector, secret_propagation_detector,
    git_diff_detector, scope_expansion_detector, test_failure_detector,
    build_failure_detector, dangerous_package_detector, repeated_failure_detector,
    value_loss_detector,
)
from hudson_mcp.detectors import api_break_detector
from hudson_mcp.schemas import DetectorContext
from hudson_mcp import logging_store

def _inc_out(inc: Incident | None) -> dict:
    return {"incident": inc.model_dump() if inc else None}

# ---- 監視/状態 ----
def get_status(args: dict) -> dict:
    incs = [Incident(**i) for i in args.get("incidents", [])]
    return situation_assessment.assess(incs).model_dump()

def scan_diff(args: dict) -> dict:
    if "diff_numstat" in args:
        return git_diff_detector.parse_numstat(args["diff_numstat"])
    return git_diff_detector.collect_diff(args.get("cwd", "."))

def scan_test_result(args: dict) -> dict:
    return _inc_out(test_failure_detector.detect(
        args["output"], args.get("recent_change", True), args.get("revertable", True)))

def scan_build_result(args: dict) -> dict:
    return _inc_out(build_failure_detector.detect(
        args["output"], args.get("recent_change", True), args.get("revertable", True)))

def _parse_ctx(args: dict) -> DetectorContext | None:
    """args["context"] dict を DetectorContext に変換。なければ None。"""
    raw = args.get("context")
    if not raw:
        return None
    return DetectorContext(**raw)

def analyze_api_break(args: dict) -> dict:
    ctx = _parse_ctx(args)
    return _inc_out(api_break_detector.detect(
        before_symbols=args.get("before_symbols"),
        after_symbols=args.get("after_symbols"),
        changed_signatures=args.get("changed_signatures"),
        ctx=ctx,
    ))

# ---- 事後分析 ----
def analyze_scope_expansion(args: dict) -> dict:
    ctx = _parse_ctx(args)
    return _inc_out(scope_expansion_detector.detect(
        args.get("intended", []), args.get("changed", []),
        args.get("changed_lines", 0), ctx=ctx))

def analyze_secret_access(args: dict) -> dict:
    return _inc_out(secret_access_detector.detect(args.get("read_paths", [])))

def analyze_secret_exposure(args: dict) -> dict:
    ctx = _parse_ctx(args)
    return _inc_out(secret_exposure_detector.detect(args.get("text", ""), ctx=ctx))

def analyze_secret_propagation(args: dict) -> dict:
    ctx = _parse_ctx(args)
    return _inc_out(secret_propagation_detector.detect(
        args.get("followup_text", ""), args.get("secret_was_accessed", False), ctx=ctx))

def analyze_dangerous_package(args: dict) -> dict:
    return _inc_out(dangerous_package_detector.detect(
        args.get("added_packages", []), args.get("install_log", ""), args.get("lockfile_diff", "")))

def analyze_repeated_failure(args: dict) -> dict:
    return _inc_out(repeated_failure_detector.detect(args.get("error_signatures", [])))

def detect_value_loss(args: dict) -> dict:
    return _inc_out(value_loss_detector.detect(
        args.get("tests_passed", True), args.get("spec_intent_violated", False),
        args.get("quality_degraded", False), args.get("error_suppressed", False)))

# ---- 判断パイプライン ----
def assess_incident(args: dict) -> dict:
    incs = [Incident(**i) for i in args.get("incidents", [])]
    return situation_assessment.assess(incs).model_dump()

def constraint_lookup_tool(args: dict) -> dict:
    return constraint_lookup.lookup(args.get("incident_types", []))

def recover_purpose(args: dict) -> dict:
    sa = SituationAssessment(**args["assessment"])
    mr = args.get("matched_rules")
    mp = args.get("matched_purposes")
    if mr is None or mp is None:
        cl = constraint_lookup.lookup([sa.primary_incident_type]
                                      + [i.incident_type for i in sa.incidents])
        mr, mp = cl["matched_rules"], cl["matched_purposes"]
    return purpose_recovery.recover(sa, mr, mp).model_dump()

def recommend_recovery(args: dict) -> dict:
    sa = SituationAssessment(**args["assessment"])
    if "purpose_recovery" in args:
        pr = PurposeRecovery(**args["purpose_recovery"])
    else:
        cl = constraint_lookup.lookup([sa.primary_incident_type]
                                      + [i.incident_type for i in sa.incidents])
        pr = purpose_recovery.recover(sa, cl["matched_rules"], cl["matched_purposes"])
    pr.threatened_values = value_reprioritization.reprioritize(pr.threatened_values)
    pr.elevated_values = value_reprioritization.reprioritize(pr.elevated_values)
    return recovery_decision.recommend(sa, pr).model_dump()

def generate_feedback(args: dict) -> dict:
    return feedback_loop.generate(args.get("incident_type", "")).model_dump()

def write_log(args: dict) -> dict:
    path = logging_store.append(args["name"], args["record"])
    return {"written": path}

def build_report(args: dict) -> dict:
    sa = SituationAssessment(**args["assessment"])
    pr = PurposeRecovery(**args["purpose_recovery"])
    from hudson_mcp.schemas import RecoveryDecision, Feedback
    d = RecoveryDecision(**args["decision"])
    fb = Feedback(**args.get("feedback", {}))
    return {"report": report_generator.render(sa, pr, d, fb)}
