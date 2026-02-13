from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_processing(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "processing"
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "status": "scaffolded",
        "note": "Implement OCR fallback, segmentation, normalization, and delta detection.",
        "granularity": context["config"].get("processing", {}).get("segmentation_granularity"),
    }

    segments_path = out_dir / "normalized_segments.json"
    with segments_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {"normalized_segments": str(segments_path)}
