from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_ingestion(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "ingestion"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "status": "scaffolded",
        "note": "Replace with source connectors and change detection.",
        "sources": context["config"].get("ingestion", {}).get("sources", []),
    }
    manifest_path = out_dir / "raw_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return {"raw_manifest": str(manifest_path)}
