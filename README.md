# RegDelta

Open-source, self-hosted LLM system for Vietnamese regulatory intelligence.

RegDelta ingests newly issued Vietnamese laws/circulars, extracts compliance-relevant deltas, and produces verified English compliance packs for foreign investors and MNC legal/compliance teams.

## Problem

Cross-border teams often cannot track Vietnamese legal updates fast enough due to:
- Language barriers
- Fragmented publication channels
- High risk of hallucinated legal claims in generic LLM outputs

RegDelta targets high-recall ingestion and high-precision verified generation with abstention when source support is weak.

## Users

- Foreign investors evaluating market entry/regulatory risk
- MNC legal and compliance teams operating in Vietnam
- In-house counsel and external advisors preparing policy updates

## Core Pipeline

1. Ingestion: Fetch and version new laws, decrees, and circulars from official sources.
2. Processing: Segment articles/clauses, normalize metadata and references, and compute document deltas.
3. Grounding: Build retrieval indices over original Vietnamese text and metadata.
4. Generation: Produce structured English compliance packs from grounded evidence.
5. Verification: Check every generated claim against source spans; abstain if unsupported.
6. Packaging: Export machine-readable and human-readable compliance outputs.

## Technical Architecture (Open Source, Self-Hosted)

- `ingestion/`: Source connectors, scheduling, deduplication, change detection
- `processing/`: Text cleanup, clause segmentation, legal citation normalization
- `retrieval/`: Indexing, hybrid search (BM25 + embeddings), evidence ranking
- `generation/`: Prompt/model adapters and structured output schema
- `verification/`: Claim-to-evidence alignment, contradiction/unsupported checks, abstention policy
- `evaluation/`: Test sets, metrics, ablation runners, reproducible experiment logging
- `orchestration/`: End-to-end DAG, configs, checkpoints, and artifact management

## Experimental Plan (Minimum Two Approaches)

- Approach A: Prompt-only baseline (no retrieval)
- Approach B: RAG pipeline over Vietnamese source text
- Optional Approach C: RAG + LoRA fine-tuned model
- Optional Approach D: Single generator vs generator+verifier model split

Primary comparisons:
- Translation fidelity
- Extraction accuracy
- Hallucination rate / abstention quality
- End-to-end compliance pack usefulness

## Evaluation

Planned quantitative metrics:
- Translation fidelity: COMET/BLEU + targeted legal terminology checks
- Extraction accuracy: Precision/Recall/F1 against annotated deltas
- Hallucination bounding: Unsupported-claim rate, verifier precision/recall, abstention calibration
- Retrieval quality: Recall@k and MRR for evidence spans

Outputs include ablation tables, error taxonomy, and per-stage failure analysis.

## Reproducibility

RegDelta will ship:
- Fixed data snapshots/versioned manifests
- Deterministic configs and random seeds
- Saved local checkpoint(s) runnable on SUTD cluster
- Experiment tracking logs (for example Weights & Biases)
- One-command or scripted end-to-end pipeline execution

## Project Deliverables Mapping

### Week 6

- Working GitHub repository
- `PROJECT.md` covering:
  - Problem statement
  - Target users
  - Data sources
  - Planned ingestion → extraction → translation → verification → packaging pipeline
  - Experiment design with at least two approaches

### Week 13 (Graded)

- Complete GitHub repo with:
  - Proper `README.md`
  - Runnable instructions
  - Saved local model checkpoint for SUTD cluster
  - Reproducible training/evaluation logs
- PDF report with:
  - Experiments and results
  - Hardware and estimated GPU hours
  - Final architecture and design decisions
- Oral presentation and optional live demo

## Planned Repository Layout

```text
RegDelta/
  README.md
  PROJECT.md
  configs/
  data/
    raw/
    processed/
    eval/
  src/
    ingestion/
    processing/
    retrieval/
    generation/
    verification/
    packaging/
  eval/
  scripts/
  checkpoints/
  logs/
  reports/
```

## Quick Start (Target)

```bash
# 1) Clone
git clone https://github.com/dnoma/RegDelta.git
cd RegDelta

# 2) Install dependencies (to be finalized)
# make setup

# 3) Run end-to-end pipeline (to be finalized)
# make run

# 4) Run evaluation harness (to be finalized)
# make eval
```

## Status

Current milestone: foundation docs and architecture plan committed.

Next milestone: scaffold pipeline modules, baseline experiments, and first reproducible evaluation run.
