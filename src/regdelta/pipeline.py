from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from regdelta.contract import (
    load_pipeline_contract,
    stage_contract_map,
    validate_stage_order,
)
from regdelta.stages.generation import run_generation
from regdelta.stages.ingestion import run_ingestion
from regdelta.stages.packaging import run_packaging
from regdelta.stages.processing import run_processing
from regdelta.stages.retrieval import run_retrieval
from regdelta.stages.verification import run_verification

StageFn = Callable[[dict[str, Any]], dict[str, Any]]

STAGE_REGISTRY: dict[str, StageFn] = {
    "ingestion": run_ingestion,
    "processing": run_processing,
    "retrieval": run_retrieval,
    "generation": run_generation,
    "verification": run_verification,
    "packaging": run_packaging,
}


def run_pipeline(config: dict[str, Any], stages: list[str], repo_root: Path) -> Path:
    contract_path = config.get("pipeline", {}).get(
        "contract_path", "pipelines/regdelta_pipeline.json"
    )
    contract = load_pipeline_contract(repo_root=repo_root, contract_path=contract_path)
    contract_map = stage_contract_map(contract)
    validate_stage_order(contract=contract, stages=stages)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = repo_root / config["paths"]["logs"] / "runs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    context: dict[str, Any] = {
        "config": config,
        "repo_root": repo_root,
        "run_dir": run_dir,
        "artifacts": {},
    }

    executed: list[dict[str, Any]] = []
    available_artifacts: set[str] = set()
    for stage_name in stages:
        fn = STAGE_REGISTRY.get(stage_name)
        if fn is None:
            raise ValueError(f"Unknown stage: {stage_name}")

        stage_contract = contract_map[stage_name]
        required_inputs = stage_contract.get("inputs", [])
        missing_inputs = [
            artifact for artifact in required_inputs if artifact not in available_artifacts
        ]
        if missing_inputs:
            missing = ", ".join(missing_inputs)
            raise ValueError(f"Stage '{stage_name}' missing required inputs: {missing}")

        result = fn(context)
        if not isinstance(result, dict):
            raise ValueError(f"Stage '{stage_name}' returned non-mapping output")

        expected_outputs = stage_contract.get("outputs", [])
        missing_outputs = [output for output in expected_outputs if output not in result]
        if missing_outputs:
            missing = ", ".join(missing_outputs)
            raise ValueError(f"Stage '{stage_name}' missing required outputs: {missing}")

        available_artifacts.update(expected_outputs)
        context["artifacts"][stage_name] = result
        executed.append({"stage": stage_name, "result": result})

    summary = {
        "run_id": timestamp,
        "stages": executed,
        "profile": config.get("runtime", {}).get("profile"),
        "seed": config.get("runtime", {}).get("seed"),
    }

    summary_path = run_dir / "run_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary_path
