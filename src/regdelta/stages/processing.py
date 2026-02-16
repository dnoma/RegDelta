from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _load_documents(context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    ingestion_artifacts = context.get("artifacts", {}).get("ingestion", {})
    documents_path = ingestion_artifacts.get("documents")

    if not documents_path:
        manifest_path = ingestion_artifacts.get("raw_manifest")
        if manifest_path and Path(manifest_path).exists():
            with Path(manifest_path).open("r", encoding="utf-8") as f:
                manifest = json.load(f)
            documents_path = manifest.get("documents_path")

    if not documents_path:
        warnings.append("No ingestion documents artifact found. Processing produced empty outputs.")
        return [], warnings

    path = Path(documents_path)
    if not path.exists():
        warnings.append(f"Ingestion documents artifact not found: {path}")
        return [], warnings

    documents: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                warnings.append(f"Invalid JSONL in ingestion documents at line {line_no}: {path}")
                continue
            if not isinstance(obj, dict):
                warnings.append(f"Expected JSON object in ingestion documents at line {line_no}: {path}")
                continue
            documents.append(obj)

    return documents, warnings


def _split_clauses(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        return lines

    split = [chunk.strip() for chunk in re.split(r"(?<=[.!?;])\s+", text.strip()) if chunk.strip()]
    if split:
        return split
    return [text.strip()] if text.strip() else []


def _segment_documents(
    documents: list[dict[str, Any]], granularity: str
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    word_pattern = re.compile(r"\w+", flags=re.UNICODE)
    segments: list[dict[str, Any]] = []
    segments_by_doc: dict[str, list[dict[str, Any]]] = {}

    for doc in documents:
        doc_id = str(doc.get("doc_id", "")).strip()
        text = str(doc.get("text", "")).strip()
        if not doc_id or not text:
            continue

        clauses = _split_clauses(text) if granularity == "clause" else [text]
        doc_segments: list[dict[str, Any]] = []
        for idx, clause in enumerate(clauses, start=1):
            clause_id = f"cl_{idx}"
            segment = {
                "segment_id": f"{doc_id}:{clause_id}",
                "doc_id": doc_id,
                "clause_id": clause_id,
                "text": clause,
                "token_count": len(word_pattern.findall(clause)),
            }
            doc_segments.append(segment)
            segments.append(segment)
        segments_by_doc[doc_id] = doc_segments

    return segments, segments_by_doc


def _extract_deltas(
    documents: list[dict[str, Any]], segments_by_doc: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    docs_by_id = {str(doc.get("doc_id", "")).strip(): doc for doc in documents}
    deltas: list[dict[str, Any]] = []

    for doc in documents:
        new_doc_id = str(doc.get("doc_id", "")).strip()
        old_doc_id = str(doc.get("replaces_doc_id", "")).strip()
        if not new_doc_id or not old_doc_id or old_doc_id not in docs_by_id:
            continue

        old_clauses = {segment["clause_id"]: segment["text"] for segment in segments_by_doc.get(old_doc_id, [])}
        new_clauses = {segment["clause_id"]: segment["text"] for segment in segments_by_doc.get(new_doc_id, [])}

        for clause_id, new_text in sorted(new_clauses.items()):
            old_text = old_clauses.get(clause_id)
            if old_text is None:
                deltas.append(
                    {
                        "old_doc_id": old_doc_id,
                        "new_doc_id": new_doc_id,
                        "change_type": "added",
                        "clause_id": clause_id,
                        "old_text": "",
                        "new_text": new_text,
                    }
                )
            elif old_text != new_text:
                deltas.append(
                    {
                        "old_doc_id": old_doc_id,
                        "new_doc_id": new_doc_id,
                        "change_type": "amended",
                        "clause_id": clause_id,
                        "old_text": old_text,
                        "new_text": new_text,
                    }
                )

        for clause_id, old_text in sorted(old_clauses.items()):
            if clause_id not in new_clauses:
                deltas.append(
                    {
                        "old_doc_id": old_doc_id,
                        "new_doc_id": new_doc_id,
                        "change_type": "repealed",
                        "clause_id": clause_id,
                        "old_text": old_text,
                        "new_text": "",
                    }
                )

    return deltas


def run_processing(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "processing"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = context["config"].get("processing", {})
    granularity = str(cfg.get("segmentation_granularity", "clause"))
    documents, warnings = _load_documents(context)
    segments, segments_by_doc = _segment_documents(documents, granularity)
    deltas = _extract_deltas(documents, segments_by_doc)

    segments_payload = {
        "status": "ok",
        "granularity": granularity,
        "document_count": len(documents),
        "segment_count": len(segments),
        "segments": segments,
        "warnings": warnings,
    }

    segments_path = out_dir / "normalized_segments.json"
    with segments_path.open("w", encoding="utf-8") as f:
        json.dump(segments_payload, f, ensure_ascii=False, indent=2)

    deltas_payload = {
        "status": "ok",
        "delta_count": len(deltas),
        "deltas": deltas,
    }

    deltas_path = out_dir / "deltas.json"
    with deltas_path.open("w", encoding="utf-8") as f:
        json.dump(deltas_payload, f, ensure_ascii=False, indent=2)

    return {
        "normalized_segments": str(segments_path),
        "deltas": str(deltas_path),
    }
