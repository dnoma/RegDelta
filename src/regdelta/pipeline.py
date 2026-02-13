from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

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
    for stage_name in stages:
        fn = STAGE_REGISTRY.get(stage_name)
        if fn is None:
            raise ValueError(f"Unknown stage: {stage_name}")

        result = fn(context)
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
