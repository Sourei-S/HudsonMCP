from __future__ import annotations
import functools
from pathlib import Path
import yaml

_ROOT = Path(__file__).resolve().parent
_config_dir: Path | None = None

LOGS = _ROOT / "logs"


def set_config_dir(path: str | None) -> None:
    global _config_dir
    _config_dir = Path(path).resolve() if path else None


def _resolve(subdir: str, filename: str) -> Path:
    if _config_dir is not None:
        candidate = _config_dir / filename
        if candidate.exists():
            return candidate
    return _ROOT / subdir / filename


def _load_yaml(path: Path) -> dict | list:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@functools.lru_cache(maxsize=None)
def load_value_hierarchy() -> list[dict]:
    return _load_yaml(_resolve("maps", "dev-value-hierarchy.yaml"))["hierarchy"]


@functools.lru_cache(maxsize=None)
def _priority_index() -> dict[str, int]:
    return {h["name"]: h["priority"] for h in load_value_hierarchy()}


def value_priority(name: str) -> int:
    return _priority_index().get(name, 13)


@functools.lru_cache(maxsize=None)
def load_rule_map() -> list[dict]:
    return _load_yaml(_resolve("maps", "dev-rule-map.yaml"))["rules"]


@functools.lru_cache(maxsize=None)
def load_purpose_map() -> dict[str, dict]:
    return {p["id"]: p for p in _load_yaml(_resolve("maps", "dev-purpose-map.yaml"))["purposes"]}


@functools.lru_cache(maxsize=None)
def load_policy(name: str) -> dict:
    return _load_yaml(_resolve("policies", f"{name}.yaml"))
