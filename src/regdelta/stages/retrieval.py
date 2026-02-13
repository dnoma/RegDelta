from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_retrieval(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "retrieval"
    out_dir.mkdir(parents=True, exist_ok=True)

    retrieval_cfg = context["config"].get("retrieval", {})
    payload = {
        "status": "scaffolded",
        "note": "Implement hybrid retrieval index and evidence ranking.",
        "top_k": retrieval_cfg.get("top_k"),
        "rerank_top_k": retrieval_cfg.get("rerank_top_k"),
    }

    candidates_path = out_dir / "retrieval_candidates.json"
    with candidates_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {"retrieval_candidates": str(candidates_path)}
