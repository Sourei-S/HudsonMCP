# src/hudson_mcp/detectors/git_diff_detector.py
from __future__ import annotations
import subprocess

def _rename_new_path(path: str) -> str:
    """rename/コピー行の新パスを返す。
    "old => new"（接頭辞なし）と "pre/{old => new}/suf"（brace 圧縮）両形式に対応。"""
    if " => " not in path:
        return path
    if "{" in path and "}" in path:
        pre = path[: path.index("{")]
        inner = path[path.index("{") + 1 : path.index("}")]
        suf = path[path.index("}") + 1 :]
        new = inner.split(" => ")[-1].strip()
        return pre + new + suf
    return path.split(" => ")[-1].strip()

def parse_numstat(raw: str) -> dict:
    files: list[str] = []
    changed_lines = 0
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        path = _rename_new_path(path)
        files.append(path)
        for n in (added, removed):
            if n.isdigit():
                changed_lines += int(n)
    return {"files": files, "changed_files": len(files), "changed_lines": changed_lines}

def collect_diff(cwd: str) -> dict:
    """git numstat を実行して差分要約を返す。git 不在時は空要約。"""
    try:
        raw = subprocess.run(
            ["git", "diff", "--numstat", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return {"files": [], "changed_files": 0, "changed_lines": 0, "git_available": False}
    summary = parse_numstat(raw)
    summary["git_available"] = True
    return summary
