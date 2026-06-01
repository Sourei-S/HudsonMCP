# src/hudson_mcp/detectors/dangerous_package_detector.py
from __future__ import annotations
import re
from hudson_mcp import config
from hudson_mcp.schemas import Incident, DetectorContext

def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def detect(added_packages: list[str], install_log: str, lockfile_diff: str,
           ctx: DetectorContext | None = None) -> Incident | None:
    pol = config.load_policy("package-risk-policy")
    known = pol["known_packages"]
    max_dist = pol["typosquat_max_distance"]
    susp_pat = pol["suspicious_name_patterns"]

    typosquat = []
    for pkg in added_packages:
        if pkg in known:
            continue
        if any(re.search(p, pkg) for p in susp_pat):
            typosquat.append(pkg)
            continue
        for k in known:
            d = levenshtein(pkg, k)
            if 0 < d <= max_dist:
                typosquat.append(pkg)
                break

    postinstall = any(k in install_log.lower() for k in pol["postinstall_keys"])
    network = any(ind in install_log for ind in pol["network_indicators"])
    lockfile_changed = bool(lockfile_diff.strip())

    if not (typosquat or postinstall or network or lockfile_changed):
        return None

    if typosquat:
        itype = "suspicious_dependency_installed"
    elif postinstall:
        itype = "postinstall_script_executed"
    elif lockfile_changed:
        itype = "lockfile_poisoning"
    else:
        itype = "unexpected_network_activity"

    signals = {
        "dangerous_package_present": bool(typosquat),
        "postinstall_executed": postinstall,
        "unexpected_network_activity": network,
        "lockfile_poisoned": lockfile_changed,
        "dependency_change_present": True,
        "evidence_preservation_first": True,
        "recoverability_unknown": postinstall or network,
        "damage_spreads_if_continue": postinstall or network or bool(typosquat),
        "needs_human_judgment": bool(typosquat),
        "revertable": lockfile_changed and not (postinstall or network),
    }
    return Incident(
        incident_type=itype,
        severity="high",
        description="危険または疑わしい依存関係/スクリプト/lockfile 変更を検知",
        affected_files=["package.json", "lockfile"] if lockfile_changed else [],
        evidence={"suspect_packages": typosquat, "postinstall": postinstall, "network": network},
        signals=signals,
    )
