from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_verification(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "verification"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = context["config"].get("verification", {})
    payload = {
        "status": "scaffolded",
        "note": "Implement claim-evidence checking, contradiction detection, and abstention.",
        "abstain_when_unsupported": cfg.get("abstain_when_unsupported", True),
        "claims": [],
        "errors": [],
        "confidence_summary": {
            "min": 0.0,
            "max": 0.0,
            "average": 0.0,
        },
        "abstention_report": {
            "total_claims": 0,
            "abstained": 0,
        },
    }

    verified_path = out_dir / "verified_pack.json"
    with verified_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    abstention_path = out_dir / "abstention_report.json"
    with abstention_path.open("w", encoding="utf-8") as f:
        json.dump(payload["abstention_report"], f, ensure_ascii=False, indent=2)

    return {
        "verified_pack": str(verified_path),
        "abstention_report": str(abstention_path),
    }
