# RegDelta

RegDelta is a self-hosted MLOps pipeline for Vietnamese regulatory intelligence.
It ingests legal documents, extracts compliance-relevant deltas, generates English compliance packs, and verifies claims against source evidence with abstention for unsupported statements.

## Project Status

Current branch includes a runnable scaffold:
- Config-driven pipeline orchestration
- Runtime profiles (`dev_cpu`, `onprem_1gpu`, `onprem_4gpu`)
- Stage module contracts and artifact logging
- Baseline unit tests for config and pipeline execution

Stage internals are still implementation-ready placeholders.

## Scope for v0.1 (Recommended)

Use a **time-frozen, one-time offline pipeline** first.

Why:
- Public raw legal text is available, but high-quality labeled supervision is limited.
- Frozen corpora make results reproducible and easier to grade/audit.
- Offline execution reduces complexity versus continuous crawling + streaming updates.

Suggested corpus cutoff for milestone evaluation: `2025-12-31` (adjustable in your experiment protocol).

## Problem and Users

Target users:
- Foreign investors operating in Vietnam
- MNC legal and compliance teams
- Counsel and policy analysts requiring traceable, evidence-backed outputs

Core risk addressed:
- Generic summarization can introduce unsupported legal claims.

## Pipeline Architecture

Configured stage order:
1. `ingestion`
2. `processing`
3. `retrieval`
4. `generation`
5. `verification`
6. `packaging`

Contract-level stage I/O (`pipelines/regdelta_pipeline.json`):

| Stage | Inputs | Outputs |
|---|---|---|
| `ingestion` | - | `raw_manifest` |
| `processing` | `raw_manifest` | `normalized_segments`, `deltas` |
| `retrieval` | `normalized_segments` | `evidence_index`, `retrieval_candidates` |
| `generation` | `retrieval_candidates`, `deltas` | `compliance_pack_draft` |
| `verification` | `compliance_pack_draft`, `retrieval_candidates` | `verified_pack`, `abstention_report` |
| `packaging` | `verified_pack`, `abstention_report` | `compliance_pack_json`, `compliance_pack_md` |

## Data Availability and Required Datasets

### Availability reality

- **Available**: official Vietnamese legal documents (HTML/PDF + metadata) from government portals.
- **Limited**: open, high-quality labels for retrieval relevance, claim support, and legal deltas.

### Minimum datasets needed for this repo

1. `documents` dataset (raw legal corpus):
   - `doc_id`, `title`, `issuer`, `issue_date`, `effective_date`, `source_url`, `text`, `checksum`
2. `version_pairs` dataset (delta extraction):
   - `old_doc_id`, `new_doc_id`, `change_type`, `changed_spans`
3. `retrieval_eval` dataset:
   - `query_id`, `query_text`, `relevant_doc_ids` or span-level qrels
4. `verification_eval` dataset:
   - `claim_id`, `claim_text`, `label` (`supported|unsupported|contradicted`), `evidence_spans`

### Recommended freeze protocol

1. Fix corpus cutoff date.
2. Snapshot source URLs and checksums into a manifest.
3. Normalize to stable JSONL schemas under `data/`.
4. Build frozen train/dev/test splits for evaluation.
5. Version all manifests and splits in git-tracked metadata.

## Model Input and Output Contract

### Generation input (example)

```json
{
  "query": "What changed for reporting deadlines?",
  "corpus_cutoff": "2025-12-31",
  "retrieval_candidates": [
    {
      "doc_id": "vn_decree_x",
      "clause_id": "art_12_cl_3",
      "text": "Vietnamese evidence text...",
      "score": 0.87
    }
  ],
  "deltas": [
    {
      "change_type": "amended",
      "reference": "Article 12 Clause 3"
    }
  ]
}
```

### Verified output (example)

```json
{
  "pack_id": "pack_20260213_001",
  "summary": "Reporting deadlines were tightened for ...",
  "effective_dates": ["2025-11-01"],
  "required_actions": [
    "Submit compliance report within 15 days"
  ],
  "claims": [
    {
      "claim_id": "claim_001",
      "statement": "Deadline changed from 30 to 15 days",
      "verdict": "supported",
      "citations": [
        {
          "doc_id": "vn_decree_x",
          "clause_id": "art_12_cl_3"
        }
      ]
    }
  ],
  "abstentions": [],
  "confidence": 0.82
}
```

## Repository Layout

```text
RegDelta/
  configs/                 # Base config + runtime profiles
  pipelines/               # Stage contract specification
  src/regdelta/            # CLI, config loader, pipeline runner, stages
  data/                    # Raw/interim/processed/eval datasets
  artifacts/               # Checkpoints, indices, logs, reports
  eval/                    # Evaluation harness plan and scripts (WIP)
  docs/                    # Architecture docs
  tests/                   # Unit tests
```

## Quickstart

```bash
git clone https://github.com/dnoma/RegDelta.git
cd RegDelta
./scripts/bootstrap.sh
make plan
make run-dev
make test
```

Default full run:

```bash
make run
```

Run summaries are written to:
- `artifacts/logs/runs/<UTC_TIMESTAMP>/run_summary.json`

## Configuration and Profiles

Primary config:
- `configs/base.json`

Profile overrides:
- `configs/profiles/dev_cpu.json`
- `configs/profiles/onprem_1gpu.json`
- `configs/profiles/onprem_4gpu.json`

Execution examples:

```bash
PYTHONPATH=src python3 -m regdelta.cli plan --config configs/base.json --profile dev_cpu
PYTHONPATH=src python3 -m regdelta.cli run --config configs/base.json --stages ingestion,processing
```

## Evaluation Plan

Baseline comparisons:
1. Prompt-only generation
2. Retrieval-grounded generation (RAG)

Planned metrics:
- Translation fidelity and legal term consistency
- Delta extraction precision/recall/F1
- Unsupported claim rate and abstention calibration
- Retrieval Recall@k and MRR

`eval/README.md` contains the current harness plan.

## Reproducibility Checklist

- Fixed random seed in config
- Frozen corpus manifest and checksums
- Versioned config profiles
- Deterministic run artifacts per timestamped run directory
- Test suite runnable via `make test`

## Roadmap

- Implement real source connectors and parser fixtures in `ingestion`
- Add clause segmentation and version diffing in `processing`
- Implement hybrid retrieval + reranking in `retrieval`
- Enforce schema + citation spans in `generation`
- Add claim-level verifier + abstention report in `verification`
- Add full exporter and audit bundle in `packaging`
- Build evaluation runner and ablation reports in `eval/`
