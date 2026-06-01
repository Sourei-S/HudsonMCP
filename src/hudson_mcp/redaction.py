# src/hudson_mcp/redaction.py
"""秘密値スクラブ層。

中核要件#3「秘密の実値を evidence/log/report/出力に残さない」を一元的に担保する。
secret-policy の value_patterns に一致する文字列を <REDACTED> へ置換する。
"""
from __future__ import annotations
import functools
import re
from hudson_mcp import config

REDACTED = "<REDACTED>"


@functools.lru_cache(maxsize=None)
def _compiled() -> list[re.Pattern]:
    return [re.compile(p) for p in config.load_policy("secret-policy")["value_patterns"]]


def redact_text(text: str) -> str:
    """テキスト中の秘密値らしき部分を <REDACTED> に置換。"""
    if not text:
        return text
    out = text
    for pat in _compiled():
        out = pat.sub(REDACTED, out)
    return out


def redact_record(obj):
    """dict / list / str を再帰的にスクラブ（ログ永続化の境界で使用）。"""
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: redact_record(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_record(v) for v in obj]
    return obj
