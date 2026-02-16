from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    payload_path = Path(path)
    if not payload_path.exists():
        return None
    with payload_path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        return None
    return loaded


def _to_markdown(package_json: dict[str, Any]) -> str:
    claims = package_json.get("claims", [])
    abstention = package_json.get("abstention_report", {})
    required_actions = package_json.get("required_actions", [])

    lines = ["# Compliance Pack", ""]
    lines.append(f"Pack ID: `{package_json.get('pack_id', 'unknown')}`")
    lines.append(f"Generated At: `{package_json.get('generated_at', '')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(package_json.get("summary", ""))
    lines.append("")

    lines.append("## Required Actions")
    if isinstance(required_actions, list) and required_actions:
        for action in required_actions:
            lines.append(f"- {action}")
    else:
        lines.append("- No required actions recorded.")
    lines.append("")

    lines.append("## Claims")
    if isinstance(claims, list) and claims:
        for claim in claims:
            claim_id = claim.get("claim_id", "unknown")
            verdict = claim.get("verdict", "unknown")
            statement = claim.get("statement", "")
            lines.append(f"- `{claim_id}` ({verdict}): {statement}")
    else:
        lines.append("- No claims available.")
    lines.append("")

    lines.append("## Abstention Report")
    lines.append(f"- Total claims: {abstention.get('total_claims', 0)}")
    lines.append(f"- Abstained: {abstention.get('abstained', 0)}")

    return "\n".join(lines) + "\n"


def run_packaging(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "packaging"
    out_dir.mkdir(parents=True, exist_ok=True)

    packaging_cfg = context["config"].get("packaging", {})
    output_formats = packaging_cfg.get("output_formats", [])

    verification_artifacts = context.get("artifacts", {}).get("verification", {})
    verified_payload = _load_json(verification_artifacts.get("verified_pack"))
    abstention_payload = _load_json(verification_artifacts.get("abstention_report"))
    warnings: list[str] = []
    if verified_payload is None:
        warnings.append("No verified pack artifact found.")
        verified_payload = {}
    if abstention_payload is None:
        warnings.append("No abstention report artifact found.")
        abstention_payload = {"total_claims": 0, "abstained": 0}

    claims = verified_payload.get("claims", [])
    if not isinstance(claims, list):
        claims = []
        warnings.append("Verified pack contained invalid claims payload.")

    required_actions = [
        f"Review {claim.get('claim_id')} ({claim.get('verdict')})"
        for claim in claims
        if isinstance(claim, dict) and claim.get("verdict") != "supported"
    ]
    if not required_actions:
        required_actions = ["No additional action required based on supported claims."]

    package_json = {
        "pack_id": datetime.now(timezone.utc).strftime("pack_%Y%m%dT%H%M%SZ"),
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "formats": output_formats,
        "summary": (
            f"Packaged {len(claims)} verified claim(s); "
            f"{abstention_payload.get('abstained', 0)} claim(s) abstained."
        ),
        "required_actions": required_actions,
        "claims": claims,
        "abstention_report": abstention_payload,
        "warnings": warnings,
    }

    json_path = out_dir / "compliance_pack.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(package_json, f, ensure_ascii=False, indent=2)

    md_path = out_dir / "compliance_pack.md"
    md_path.write_text(_to_markdown(package_json), encoding="utf-8")

    audit_manifest = {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "verified_pack": verification_artifacts.get("verified_pack"),
            "abstention_report": verification_artifacts.get("abstention_report"),
            "compliance_pack_json": str(json_path),
            "compliance_pack_md": str(md_path),
        },
    }
    audit_manifest_path = out_dir / "audit_bundle_manifest.json"
    with audit_manifest_path.open("w", encoding="utf-8") as f:
        json.dump(audit_manifest, f, ensure_ascii=False, indent=2)

    return {
        "compliance_pack_json": str(json_path),
        "compliance_pack_md": str(md_path),
        "audit_bundle_manifest": str(audit_manifest_path),
    }
