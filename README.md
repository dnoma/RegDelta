# RegDelta

RegDelta is an open-source, self-hosted LLM system for Vietnamese regulatory intelligence.

It ingests new Vietnamese laws and circulars, extracts compliance-relevant deltas, and generates verified English compliance packs with abstention when claims are unsupported by source evidence.

## Why This Exists

Foreign investors and MNC legal/compliance teams need fast, traceable interpretation of Vietnamese regulatory changes. Generic summarization is high risk for legal use because unsupported claims can be introduced silently.

RegDelta is built around evidence grounding, verification, and reproducibility.

## Current Status

Foundation scaffold is implemented and merged to `main`:
- Pipeline package and stage contracts
- Compute-aware runtime profiles for local/dev and on-prem GPU
- Config-driven execution and run summaries
- Reproducibility-first repo layout for data, artifacts, and evaluations

## Commit History Snapshot

Current `main` history (latest first) shows a fast scaffold-to-docs iteration on February 13, 2026:

- `a189586`: Merge PR #1 (`feature/scaffold-mlops-foundation`) into `main`
- `612cf7a`: Expanded `README.md` with architecture and on-prem runbook details
- `b1a9c10`: Added end-to-end scaffold (CLI, stage modules, profiles, pipeline contract, tests, scripts)
- `171b1af`: Added initial `README.md` and `PROJECT.md` architecture plan

Practical implication:
- The repository has a complete runnable scaffold with placeholders for stage internals, and documentation is aligned with that scaffolded architecture.

## End-to-End Pipeline

1. `ingestion`: fetch/version official updates
2. `processing`: segment/normalize legal text and deltas
3. `retrieval`: build and query grounding evidence index
4. `generation`: produce structured English compliance pack draft
5. `verification`: validate every claim against source evidence; abstain when unsupported
6. `packaging`: export JSON/Markdown outputs with audit trace

## Repository Layout

```text
RegDelta/
  README.md
  PROJECT.md
  pyproject.toml
  Makefile
  configs/
    base.json
    profiles/
      dev_cpu.json
      onprem_1gpu.json
      onprem_4gpu.json
  pipelines/
    regdelta_pipeline.json
  src/regdelta/
    cli.py
    config.py
    pipeline.py
    stages/
      ingestion.py
      processing.py
      retrieval.py
      generation.py
      verification.py
      packaging.py
  scripts/
    bootstrap.sh
    run_pipeline.sh
  data/
    README.md
    raw/
    interim/
    processed/
    eval/
  artifacts/
    README.md
    checkpoints/
    indices/
    logs/
    reports/
  eval/
    README.md
  docs/
    ARCHITECTURE.md
  tests/
```

## Compute Profiles (Efficiency + Feasibility)

Profiles are in `configs/profiles/` and merged into `configs/base.json`.

- `dev_cpu`: small-model baseline for local iteration and CI sanity checks
- `onprem_1gpu`: default production baseline (int4 quantization)
- `onprem_4gpu`: higher-capacity profile for larger context windows and stronger verifier

Design intent:
- Keep RAG retrieval cheap and deterministic
- Gate expensive generation with stricter verification
- Use quantized models by default unless capacity demands bf16

## Quick Start

### 1) Clone

```bash
git clone https://github.com/dnoma/RegDelta.git
cd RegDelta
```

### 2) Bootstrap environment

```bash
./scripts/bootstrap.sh
```

### 3) Preview execution plan

```bash
make plan
```

### 4) Run a lightweight dev pipeline

```bash
make run-dev
```

### 5) Run with default on-prem profile

```bash
make run
```

Each run writes a summary to:
- `artifacts/logs/runs/<UTC_TIMESTAMP>/run_summary.json`

## Stage Contracts

Each stage writes structured outputs under `artifacts/logs/runs/<run_id>/<stage>/`.

Implementation priorities:
- `ingestion`: official source connectors + snapshot/version manifesting
- `processing`: OCR fallback + clause segmentation + delta extraction
- `retrieval`: BM25 + embedding hybrid retrieval + reranking
- `generation`: schema-constrained English compliance pack generation
- `verification`: claim-evidence alignment + contradiction checks + abstention
- `packaging`: JSON/Markdown/PDF exports and audit bundles

## Experimentation Plan

Minimum two techniques:
- Prompt-only baseline
- RAG-based grounded generation

Additional ablations (planned):
- RAG vs RAG + LoRA fine-tuning
- Single generator vs generator + verifier split

Metrics to report:
- Translation fidelity
- Extraction precision/recall/F1
- Hallucination/unsupported claim rate
- Abstention calibration
- Retrieval recall@k and MRR

## Week Deliverables Mapping

### Week 6

- Working GitHub repo
- `PROJECT.md` with problem, users, data sources, and planned pipeline
- Experiment design with at least two approaches

### Week 13 (Graded)

- Complete runnable repo with final README and instructions
- Saved local checkpoint runnable on SUTD cluster
- Reproducible training/evaluation logs
- PDF report (experiments, hardware, GPU hours, architecture, results)
- Oral presentation (+ optional demo)

## Notes

The current pipeline is intentionally scaffolded to keep implementation tractable and reproducible first. Stage internals are placeholders and should be filled incrementally with measurable benchmarks and ablations.
