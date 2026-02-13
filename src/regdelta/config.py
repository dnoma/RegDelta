from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping in JSON file: {path}")
    return loaded


def load_config(config_path: str | Path, profile: str | None = None) -> dict[str, Any]:
    config_path = Path(config_path)
    base = load_json(config_path)

    profile_name = profile or base.get("runtime", {}).get("profile")
    if profile_name:
        profile_path = config_path.parent / "profiles" / f"{profile_name}.json"
        if profile_path.exists():
            profile_cfg = load_json(profile_path)
            base = _deep_merge(base, profile_cfg)

    return base


def resolve_stage_list(config: dict[str, Any], stages: str | None = None) -> list[str]:
    if stages:
        return [stage.strip() for stage in stages.split(",") if stage.strip()]
    return list(config.get("pipeline", {}).get("enabled_stages", []))
