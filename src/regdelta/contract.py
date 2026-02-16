from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_pipeline_contract(repo_root: Path, contract_path: str) -> dict[str, Any]:
    full_path = repo_root / contract_path
    with full_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pipeline contract: {full_path}")
    return payload


def stage_contract_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stages = contract.get("stages")
    if not isinstance(stages, list):
        raise ValueError("Pipeline contract must define a 'stages' list")

    mapping: dict[str, dict[str, Any]] = {}
    for stage in stages:
        if not isinstance(stage, dict):
            raise ValueError("Pipeline contract stage entries must be mappings")
        name = stage.get("name")
        if not isinstance(name, str):
            raise ValueError("Pipeline contract stage is missing a valid 'name'")
        mapping[name] = stage
    return mapping


def validate_stage_order(contract: dict[str, Any], stages: list[str]) -> None:
    names = [stage.get("name") for stage in contract.get("stages", [])]
    position: dict[str, int] = {
        name: idx for idx, name in enumerate(names) if isinstance(name, str)
    }
    for stage in stages:
        if stage not in position:
            raise ValueError(f"Stage not in contract: {stage}")

    indices = [position[stage] for stage in stages]
    if indices != sorted(indices):
        raise ValueError("Selected stages are out of contract order")
