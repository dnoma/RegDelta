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


def _build_claims(
    deltas: list[dict[str, Any]], query_candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for idx, delta in enumerate(deltas, start=1):
        change_type = str(delta.get("change_type", "amended")).strip() or "amended"
        clause_id = str(delta.get("clause_id", "")).strip() or "unknown_clause"
        old_doc_id = str(delta.get("old_doc_id", "")).strip()
        new_doc_id = str(delta.get("new_doc_id", "")).strip() or "unknown_doc"

        statement = (
            f"Clause {clause_id} in {new_doc_id} was {change_type}"
            if not old_doc_id
            else f"Clause {clause_id} changed from {old_doc_id} to {new_doc_id}"
        )

        citations: list[dict[str, Any]] = []
        if idx - 1 < len(query_candidates):
            candidates = query_candidates[idx - 1].get("candidates", [])
            if isinstance(candidates, list):
                for candidate in candidates[:2]:
                    if not isinstance(candidate, dict):
                        continue
                    citations.append(
                        {
                            "doc_id": candidate.get("doc_id"),
                            "clause_id": candidate.get("clause_id"),
                            "segment_id": candidate.get("segment_id"),
                            "rank": candidate.get("rank"),
                        }
                    )

        claims.append(
            {
                "claim_id": f"claim_{idx:03d}",
                "statement": statement,
                "change_type": change_type,
                "citations": citations,
            }
        )

    return claims


def _validate_draft_schema(draft: dict[str, Any]) -> None:
    required = [
        "pack_id",
        "status",
        "schema_version",
        "generated_at",
        "summary",
        "effective_dates",
        "required_actions",
        "claims",
        "warnings",
    ]
    missing = [key for key in required if key not in draft]
    if missing:
        missing_display = ", ".join(sorted(missing))
        raise ValueError(f"Generation draft missing required schema fields: {missing_display}")

    if not isinstance(draft["claims"], list):
        raise ValueError("Generation draft field 'claims' must be a list")
    for claim in draft["claims"]:
        if not isinstance(claim, dict):
            raise ValueError("Generation draft contains non-object claim entry")
        for key in ("claim_id", "statement", "citations"):
            if key not in claim:
                raise ValueError(f"Generation claim missing required field: {key}")


def run_generation(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "generation"
    out_dir.mkdir(parents=True, exist_ok=True)

    generation_cfg = context["config"].get("generation", {})
    warnings: list[str] = []

    retrieval_payload = _load_json(
        context.get("artifacts", {}).get("retrieval", {}).get("retrieval_candidates")
    )
    if retrieval_payload is None:
        warnings.append("No retrieval candidates artifact found. Citations may be empty.")
    query_candidates = (
        retrieval_payload.get("candidates", [])
        if isinstance(retrieval_payload, dict)
        else []
    )
    if not isinstance(query_candidates, list):
        query_candidates = []
        warnings.append("Retrieval candidates artifact had invalid shape.")

    deltas_payload = _load_json(context.get("artifacts", {}).get("processing", {}).get("deltas"))
    if deltas_payload is None:
        warnings.append("No processing deltas artifact found. Generated claims may be generic.")
    deltas = deltas_payload.get("deltas", []) if isinstance(deltas_payload, dict) else []
    if not isinstance(deltas, list):
        deltas = []
        warnings.append("Processing deltas artifact had invalid shape.")

    claims = _build_claims(
        deltas=[delta for delta in deltas if isinstance(delta, dict)],
        query_candidates=[item for item in query_candidates if isinstance(item, dict)],
    )
    if not claims:
        claims = [
            {
                "claim_id": "claim_001",
                "statement": "No material deltas were identified in the selected snapshot.",
                "change_type": "none",
                "citations": [],
            }
        ]

    effective_dates = sorted(
        {
            str(delta.get("effective_date", "")).strip()
            for delta in deltas
            if isinstance(delta, dict) and str(delta.get("effective_date", "")).strip()
        }
    )
    required_actions = [
        f"Review {claim['change_type']} change in {claim['claim_id']}"
        for claim in claims
        if claim.get("change_type") in {"added", "amended", "repealed"}
    ]
    if not required_actions:
        required_actions = ["No immediate action required pending legal review."]

    payload = {
        "pack_id": datetime.now(timezone.utc).strftime("draft_%Y%m%dT%H%M%SZ"),
        "status": "ok",
        "schema_version": generation_cfg.get("schema_version", "compliance_pack_v1"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": (
            f"Generated draft with {len(claims)} claim(s) from {len(deltas)} detected delta(s)."
        ),
        "effective_dates": effective_dates,
        "required_actions": required_actions,
        "claims": claims,
        "warnings": warnings,
    }
    _validate_draft_schema(payload)

    draft_path = out_dir / "compliance_pack_draft.json"
    with draft_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {"compliance_pack_draft": str(draft_path)}
