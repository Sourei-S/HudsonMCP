# src/hudson_mcp/core/value_reprioritization.py
from __future__ import annotations
from hudson_mcp import config

def reprioritize(threatened_values: list[str]) -> list[str]:
    """脅かされた価値を value-hierarchy の優先度順（高優先=先頭）に整列・重複除去。"""
    return sorted(set(threatened_values), key=config.value_priority)
