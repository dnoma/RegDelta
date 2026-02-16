from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _resolve_path(repo_root: Path, source_path: str) -> Path:
    path = Path(source_path)
    if path.is_absolute():
        return path
    return repo_root / path


def _load_records(source: dict[str, Any], repo_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    source_name = str(source.get("name", "unknown"))
    source_type = str(source.get("type", "")).strip().lower()
    source_path = source.get("path")

    warnings: list[str] = []
    records: list[dict[str, Any]] = []

    if source_type in {"jsonl", "jsonl_file"}:
        if not source_path:
            warnings.append(f"Source '{source_name}' missing required 'path'.")
            return records, warnings

        path = _resolve_path(repo_root, str(source_path))
        if not path.exists():
            warnings.append(f"Source '{source_name}' path not found: {path}")
            return records, warnings

        with path.open("r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    warnings.append(
                        f"Source '{source_name}' has invalid JSONL at line {line_no}: {path}"
                    )
                    continue
                if not isinstance(obj, dict):
                    warnings.append(
                        f"Source '{source_name}' expected JSON object at line {line_no}: {path}"
                    )
                    continue
                records.append(obj)
        return records, warnings

    if source_type in {"json", "json_file"}:
        if not source_path:
            warnings.append(f"Source '{source_name}' missing required 'path'.")
            return records, warnings

        path = _resolve_path(repo_root, str(source_path))
        if not path.exists():
            warnings.append(f"Source '{source_name}' path not found: {path}")
            return records, warnings

        with path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)

        if isinstance(loaded, dict):
            records.append(loaded)
        elif isinstance(loaded, list):
            for idx, item in enumerate(loaded, start=1):
                if isinstance(item, dict):
                    records.append(item)
                else:
                    warnings.append(
                        f"Source '{source_name}' expected JSON object at index {idx}: {path}"
                    )
        else:
            warnings.append(f"Source '{source_name}' expected object or list in JSON: {path}")
        return records, warnings

    warnings.append(
        f"Source '{source_name}' unsupported type '{source_type}'. Supported: jsonl, json."
    )
    return records, warnings


def _normalize_document(record: dict[str, Any], source_name: str) -> dict[str, Any] | None:
    doc_id = str(record.get("doc_id", "")).strip()
    text = str(record.get("text", "")).strip()
    if not doc_id or not text:
        return None

    checksum = str(record.get("checksum", "")).strip()
    if not checksum:
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()

    return {
        "doc_id": doc_id,
        "title": str(record.get("title", "")).strip(),
        "issuer": str(record.get("issuer", "")).strip(),
        "issue_date": str(record.get("issue_date", "")).strip(),
        "effective_date": str(record.get("effective_date", "")).strip(),
        "source_url": str(record.get("source_url", "")).strip(),
        "replaces_doc_id": str(record.get("replaces_doc_id", "")).strip() or None,
        "checksum": checksum,
        "source_name": source_name,
        "text": text,
    }


def run_ingestion(context: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(context["run_dir"]) / "ingestion"
    out_dir.mkdir(parents=True, exist_ok=True)

    repo_root = Path(context["repo_root"])
    sources = context["config"].get("ingestion", {}).get("sources", [])
    enabled_sources = [source for source in sources if source.get("enabled", True)]

    warnings: list[str] = []
    documents_by_id: dict[str, dict[str, Any]] = {}
    duplicate_doc_ids = 0

    for source in enabled_sources:
        source_name = str(source.get("name", "unknown"))
        records, source_warnings = _load_records(source, repo_root)
        warnings.extend(source_warnings)

        for record in records:
            normalized = _normalize_document(record, source_name)
            if normalized is None:
                warnings.append(
                    f"Source '{source_name}' dropped record missing required fields 'doc_id' or 'text'."
                )
                continue

            doc_id = normalized["doc_id"]
            if doc_id in documents_by_id:
                duplicate_doc_ids += 1
            documents_by_id[doc_id] = normalized

    documents = [documents_by_id[doc_id] for doc_id in sorted(documents_by_id)]
    documents_path = out_dir / "documents.jsonl"
    with documents_path.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    manifest = {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(enabled_sources),
        "document_count": len(documents),
        "duplicate_doc_ids": duplicate_doc_ids,
        "documents_path": str(documents_path),
        "sources": [
            {
                "name": source.get("name"),
                "type": source.get("type"),
                "enabled": source.get("enabled", True),
            }
            for source in sources
        ],
        "warnings": warnings,
    }
    manifest_path = out_dir / "raw_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return {
        "raw_manifest": str(manifest_path),
        "documents": str(documents_path),
    }
