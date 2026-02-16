from __future__ import annotations

import json
import re
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


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower(), flags=re.UNICODE))


def _support_score(claim_text: str, candidate_texts: list[str]) -> float:
    claim_terms = _tokenize(claim_text)
    if not claim_terms:
        return 0.0

    best_score = 0.0
    for candidate_text in candidate_texts:
        evidence_terms = _tokenize(candidate_text)
        if not evidence_terms:
            continue
        overlap = len(claim_terms & evidence_terms) / len(claim_terms)
        if overlap > best_score:
            best_score = overlap
    return best_score


def _flatten_candidates(retrieval_payload: dict[str, Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for query_entry in retrieval_payload.get("candidates", []):
        if not isinstance(query_entry, dict):
            continue
        for candidate in query_entry.get("candidates", []):
            if isinstance(candidate, dict):
                flattened.append(candidate)
    return flattened


def run_verification(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "verification"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = context["config"].get("verification", {})
    threshold = float(cfg.get("claim_confidence_threshold", 0.75))
    abstain_when_unsupported = bool(cfg.get("abstain_when_unsupported", True))
    warnings: list[str] = []

    draft_payload = _load_json(
        context.get("artifacts", {}).get("generation", {}).get("compliance_pack_draft")
    )
    if draft_payload is None:
        warnings.append("No generation draft artifact found.")
        draft_claims: list[dict[str, Any]] = []
    else:
        raw_claims = draft_payload.get("claims", [])
        draft_claims = [claim for claim in raw_claims if isinstance(claim, dict)]

    retrieval_payload = _load_json(
        context.get("artifacts", {}).get("retrieval", {}).get("retrieval_candidates")
    )
    if retrieval_payload is None:
        warnings.append("No retrieval candidates artifact found.")
        candidates: list[dict[str, Any]] = []
    else:
        candidates = _flatten_candidates(retrieval_payload)
    candidate_texts = [str(item.get("text", "")) for item in candidates]

    verified_claims: list[dict[str, Any]] = []
    abstained_claim_ids: list[str] = []
    supported = 0
    contradicted = 0
    unsupported = 0
    confidences: list[float] = []

    for idx, claim in enumerate(draft_claims, start=1):
        claim_id = str(claim.get("claim_id", f"claim_{idx:03d}"))
        statement = str(claim.get("statement", "")).strip()
        citations = claim.get("citations", [])
        if not isinstance(citations, list):
            citations = []

        score = _support_score(statement, candidate_texts)
        confidences.append(score)
        if score >= threshold:
            verdict = "supported"
            supported += 1
        elif score <= 0.05 and candidate_texts:
            verdict = "contradicted"
            contradicted += 1
        else:
            verdict = "unsupported"
            unsupported += 1

        abstained = verdict != "supported" and abstain_when_unsupported
        if abstained:
            abstained_claim_ids.append(claim_id)

        evidence = candidates[:2]
        verified_claims.append(
            {
                "claim_id": claim_id,
                "statement": statement,
                "verdict": verdict,
                "confidence": round(score, 4),
                "abstained": abstained,
                "citations": citations,
                "evidence": [
                    {
                        "doc_id": item.get("doc_id"),
                        "clause_id": item.get("clause_id"),
                        "segment_id": item.get("segment_id"),
                    }
                    for item in evidence
                ],
            }
        )

    if not confidences:
        confidences = [0.0]

    abstention_report = {
        "total_claims": len(verified_claims),
        "supported": supported,
        "unsupported": unsupported,
        "contradicted": contradicted,
        "abstained": len(abstained_claim_ids),
        "abstained_claim_ids": abstained_claim_ids,
        "abstain_when_unsupported": abstain_when_unsupported,
        "threshold": threshold,
    }

    payload = {
        "status": "ok",
        "note": "Deterministic lexical verifier baseline.",
        "abstain_when_unsupported": abstain_when_unsupported,
        "claims": verified_claims,
        "errors": [],
        "warnings": warnings,
        "confidence_summary": {
            "min": round(min(confidences), 4),
            "max": round(max(confidences), 4),
            "average": round(sum(confidences) / len(confidences), 4),
        },
        "abstention_report": abstention_report,
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
