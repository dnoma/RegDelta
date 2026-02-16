from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_payload(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _claims(payload: dict[str, Any]) -> list[dict[str, Any]]:
    claims = payload.get("claims", [])
    if not isinstance(claims, list):
        return []
    return [claim for claim in claims if isinstance(claim, dict)]


def compute_metrics(payload: dict[str, Any], variant: str) -> dict[str, Any]:
    claims = _claims(payload)
    claim_count = len(claims)
    if claim_count == 0:
        return {
            "variant": variant,
            "claim_count": 0,
            "supported_rate": 0.0,
            "abstention_rate": 0.0,
            "citation_coverage": 0.0,
            "average_confidence": 0.0,
        }

    supported = 0
    abstained = 0
    with_citations = 0
    confidences: list[float] = []
    for claim in claims:
        if claim.get("verdict") == "supported":
            supported += 1
        if bool(claim.get("abstained", False)):
            abstained += 1
        citations = claim.get("citations", [])
        if isinstance(citations, list) and len(citations) > 0:
            with_citations += 1

        confidence_value = claim.get("confidence")
        try:
            confidence = float(confidence_value)
        except (TypeError, ValueError):
            confidence = 0.0
        confidences.append(confidence)

    return {
        "variant": variant,
        "claim_count": claim_count,
        "supported_rate": round(supported / claim_count, 4),
        "abstention_rate": round(abstained / claim_count, 4),
        "citation_coverage": round(with_citations / claim_count, 4),
        "average_confidence": round(sum(confidences) / claim_count, 4),
    }


def compare_variants(prompt_payload: dict[str, Any], rag_payload: dict[str, Any]) -> dict[str, Any]:
    prompt_metrics = compute_metrics(prompt_payload, variant="prompt_only")
    rag_metrics = compute_metrics(rag_payload, variant="rag")

    return {
        "variants": [prompt_metrics, rag_metrics],
        "delta": {
            "supported_rate": round(
                rag_metrics["supported_rate"] - prompt_metrics["supported_rate"], 4
            ),
            "abstention_rate": round(
                rag_metrics["abstention_rate"] - prompt_metrics["abstention_rate"], 4
            ),
            "citation_coverage": round(
                rag_metrics["citation_coverage"] - prompt_metrics["citation_coverage"], 4
            ),
            "average_confidence": round(
                rag_metrics["average_confidence"] - prompt_metrics["average_confidence"], 4
            ),
        },
    }


def run_eval(prompt_path: str | Path, rag_path: str | Path, output_path: str | Path) -> Path:
    prompt_payload = load_payload(prompt_path)
    rag_payload = load_payload(rag_path)
    report = compare_variants(prompt_payload, rag_payload)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return output
