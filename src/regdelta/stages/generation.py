from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_generation(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "generation"
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "status": "scaffolded",
        "note": "Implement evidence-grounded English compliance pack generation.",
        "schema_version": context["config"].get("generation", {}).get("schema_version"),
        "claims": [
            {
                "id": "claim_001",
                "text": "Placeholder generated claim",
                "evidence": [],
            }
        ],
    }

    draft_path = out_dir / "compliance_pack_draft.json"
    with draft_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {"compliance_pack_draft": str(draft_path)}
