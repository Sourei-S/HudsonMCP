# src/hudson_mcp/core/constraint_lookup.py
from __future__ import annotations
from hudson_mcp import config

def lookup(incident_types: list[str]) -> dict:
    """incident_type は『どの制約/価値が関係するか』の索引にのみ使う。"""
    rules = config.load_rule_map()
    itset = set(incident_types)
    matched_rules: list[str] = []
    purposes: list[str] = []
    for rule in rules:
        if itset & set(rule.get("incident_types", [])):
            matched_rules.append(rule["id"])
            for p in rule.get("related_purposes", []):
                if p not in purposes:
                    purposes.append(p)
    return {"matched_rules": matched_rules, "matched_purposes": purposes}
