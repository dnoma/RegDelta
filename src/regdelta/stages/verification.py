from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_verification(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "verification"
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "status": "scaffolded",
        "note": "Implement claim-evidence checking, contradiction detection, and abstention.",
        "abstain_when_unsupported": context["config"].get("verification", {}).get(
            "abstain_when_unsupported", True
        ),
    }

    verified_path = out_dir / "verified_pack.json"
    with verified_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {"verified_pack": str(verified_path)}
