# src/hudson_mcp/detectors/secret_access_detector.py
from __future__ import annotations
from fnmatch import fnmatch
from pathlib import PurePosixPath
from hudson_mcp import config
from hudson_mcp.schemas import Incident, DetectorContext

def _matches(path: str, patterns: list[str]) -> bool:
    name = PurePosixPath(path).name
    for pat in patterns:
        if fnmatch(name, pat) or fnmatch(path, pat) or fnmatch(path, f"*/{pat}"):
            return True
    return False

def detect(read_paths: list[str], ctx: DetectorContext | None = None) -> Incident | None:
    patterns = config.load_policy("secret-policy")["monitored_files"]
    hits = [p for p in read_paths if _matches(p, patterns)]
    if not hits:
        return None
    return Incident(
        incident_type="secret_access",
        severity="high",
        description="秘密情報を含む可能性のあるファイルを読み取った",
        affected_files=hits,
        evidence={"matched": "<REDACTED>", "files": hits},
        signals={"secret_possibly_read": True},
    )
