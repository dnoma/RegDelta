from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def _load_segments(context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    processing_artifacts = context.get("artifacts", {}).get("processing", {})
    segments_path = processing_artifacts.get("normalized_segments")

    if not segments_path:
        warnings.append("No processing normalized_segments artifact found.")
        return [], warnings

    path = Path(segments_path)
    if not path.exists():
        warnings.append(f"Processing normalized_segments artifact not found: {path}")
        return [], warnings

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict):
        warnings.append(f"Expected JSON object in normalized_segments artifact: {path}")
        return [], warnings

    segments = payload.get("segments", [])
    if not isinstance(segments, list):
        warnings.append(f"Expected 'segments' list in normalized_segments artifact: {path}")
        return [], warnings

    parsed_segments = [segment for segment in segments if isinstance(segment, dict)]
    return parsed_segments, warnings


def _build_lexical_index(
    segments: list[dict[str, Any]],
) -> tuple[dict[str, set[str]], dict[str, list[str]], dict[str, dict[str, Any]]]:
    term_to_segment_ids: dict[str, set[str]] = {}
    segment_id_to_terms: dict[str, list[str]] = {}
    segment_lookup: dict[str, dict[str, Any]] = {}

    for segment in segments:
        segment_id = str(segment.get("segment_id", "")).strip()
        if not segment_id:
            continue

        text = str(segment.get("text", ""))
        terms = _tokenize(text)
        unique_terms = sorted(set(terms))
        segment_id_to_terms[segment_id] = unique_terms
        segment_lookup[segment_id] = segment

        for term in unique_terms:
            term_to_segment_ids.setdefault(term, set()).add(segment_id)

    return term_to_segment_ids, segment_id_to_terms, segment_lookup


def _load_queries(context: dict[str, Any]) -> list[dict[str, str]]:
    retrieval_cfg = context.get("config", {}).get("retrieval", {})
    configured = retrieval_cfg.get("queries", [])
    queries: list[dict[str, str]] = []

    if isinstance(configured, list):
        for idx, item in enumerate(configured, start=1):
            if not isinstance(item, dict):
                continue
            query_text = str(item.get("query_text", "")).strip()
            if not query_text:
                continue
            query_id = str(item.get("query_id", "")).strip() or f"q_{idx}"
            queries.append({"query_id": query_id, "query_text": query_text})

    if queries:
        return queries

    deltas_path = context.get("artifacts", {}).get("processing", {}).get("deltas")
    if deltas_path and Path(deltas_path).exists():
        with Path(deltas_path).open("r", encoding="utf-8") as f:
            payload = json.load(f)
        for idx, delta in enumerate(payload.get("deltas", []), start=1):
            if not isinstance(delta, dict):
                continue
            query_text = str(delta.get("new_text", "")).strip() or str(delta.get("old_text", "")).strip()
            if not query_text:
                continue
            queries.append({"query_id": f"delta_{idx}", "query_text": query_text})

    if queries:
        return queries

    return [{"query_id": "default_1", "query_text": "regulatory update"}]


def _score_segment(query_terms: set[str], segment_terms: set[str]) -> tuple[float, float]:
    if not query_terms:
        return 0.0, 0.0
    overlap = query_terms & segment_terms
    overlap_ratio = len(overlap) / len(query_terms)
    jaccard = len(overlap) / len(query_terms | segment_terms) if query_terms | segment_terms else 0.0
    return overlap_ratio, jaccard


def run_retrieval(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "retrieval"
    out_dir.mkdir(parents=True, exist_ok=True)

    retrieval_cfg = context["config"].get("retrieval", {})
    top_k = int(retrieval_cfg.get("top_k", 8))
    rerank_top_k = int(retrieval_cfg.get("rerank_top_k", min(4, top_k)))

    segments, warnings = _load_segments(context)
    term_to_segment_ids, segment_id_to_terms, segment_lookup = _build_lexical_index(segments)
    queries = _load_queries(context)

    query_results: list[dict[str, Any]] = []
    for query in queries:
        query_id = query["query_id"]
        query_text = query["query_text"]
        query_term_set = set(_tokenize(query_text))

        candidate_ids: set[str] = set()
        for term in query_term_set:
            candidate_ids.update(term_to_segment_ids.get(term, set()))

        scored: list[dict[str, Any]] = []
        for segment_id in candidate_ids:
            segment = segment_lookup.get(segment_id)
            if segment is None:
                continue

            segment_terms = set(segment_id_to_terms.get(segment_id, []))
            score, rerank_score = _score_segment(query_term_set, segment_terms)
            scored.append(
                {
                    "segment_id": segment_id,
                    "doc_id": segment.get("doc_id"),
                    "clause_id": segment.get("clause_id"),
                    "score": score,
                    "rerank_score": rerank_score,
                    "text": segment.get("text", ""),
                }
            )

        scored.sort(key=lambda item: (item["score"], item["rerank_score"], item["segment_id"]), reverse=True)
        top_scored = scored[:top_k]
        reranked = sorted(
            top_scored[:rerank_top_k],
            key=lambda item: (item["rerank_score"], item["score"], item["segment_id"]),
            reverse=True,
        )
        final = reranked + top_scored[rerank_top_k:]

        for rank, item in enumerate(final, start=1):
            item["rank"] = rank

        query_results.append(
            {
                "query_id": query_id,
                "query_text": query_text,
                "candidate_count": len(final),
                "candidates": final,
            }
        )

    candidates_payload = {
        "status": "ok",
        "top_k": top_k,
        "rerank_top_k": rerank_top_k,
        "query_count": len(query_results),
        "candidates": query_results,
        "warnings": warnings,
    }

    candidates_path = out_dir / "retrieval_candidates.json"
    with candidates_path.open("w", encoding="utf-8") as f:
        json.dump(candidates_payload, f, ensure_ascii=False, indent=2)

    term_document_frequency = {
        term: len(segment_ids) for term, segment_ids in sorted(term_to_segment_ids.items())
    }
    index_payload = {
        "status": "ok",
        "index": {
            "segment_count": len(segment_id_to_terms),
            "vocabulary_size": len(term_document_frequency),
            "term_document_frequency": term_document_frequency,
        },
    }

    index_path = out_dir / "evidence_index.json"
    with index_path.open("w", encoding="utf-8") as f:
        json.dump(index_payload, f, ensure_ascii=False, indent=2)

    return {
        "retrieval_candidates": str(candidates_path),
        "evidence_index": str(index_path),
    }
