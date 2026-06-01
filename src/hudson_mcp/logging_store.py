# src/hudson_mcp/logging_store.py
from __future__ import annotations
import json
import re
from pathlib import Path
from hudson_mcp.config import LOGS as _DEFAULT_LOGS
from hudson_mcp.redaction import redact_record

LOGS = _DEFAULT_LOGS


def _safe_name(name: str) -> str:
    """パストラバーサル防止: 英数字・-・_ 以外を除去し basename 化。"""
    base = Path(str(name)).name
    safe = re.sub(r"[^A-Za-z0-9_-]", "", base)
    return safe or "hudson-log"


def append(name: str, record: dict) -> str:
    LOGS.mkdir(parents=True, exist_ok=True)
    path = Path(LOGS) / f"{_safe_name(name)}.jsonl"
    # 永続化境界で秘密値をスクラブ（中核要件#3）
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(redact_record(record), ensure_ascii=False) + "\n")
    return str(path)
