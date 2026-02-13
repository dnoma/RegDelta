from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_packaging(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "packaging"
    out_dir.mkdir(parents=True, exist_ok=True)

    package_json = {
        "status": "scaffolded",
        "note": "Implement JSON/Markdown/PDF exporter and audit bundle assembly.",
        "formats": context["config"].get("packaging", {}).get("output_formats", []),
    }

    json_path = out_dir / "compliance_pack.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(package_json, f, ensure_ascii=False, indent=2)

    md_path = out_dir / "compliance_pack.md"
    md_path.write_text(
        "# Compliance Pack\n\nScaffold output. Implement templated packaging in this stage.\n",
        encoding="utf-8",
    )

    return {
        "compliance_pack_json": str(json_path),
        "compliance_pack_md": str(md_path),
    }
