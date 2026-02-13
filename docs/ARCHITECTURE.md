# RegDelta Architecture (Scaffold)

## Design Goals

- Self-hosted deployment with auditable outputs
- Bounded hallucination through explicit verification and abstention
- Compute-aware operation for CPU dev mode and on-prem GPU production

## Pipeline Contract

1. `ingestion`
2. `processing`
3. `retrieval`
4. `generation`
5. `verification`
6. `packaging`

Each stage reads config and prior artifacts, writes structured outputs under `artifacts/logs/runs/<run_id>/<stage>/`, and records a run summary.

## Compute Feasibility Strategy

- `dev_cpu` profile for local iteration and CI sanity checks
- `onprem_1gpu` as default production baseline with int4 quantization
- `onprem_4gpu` for larger-context generation and stronger verifier capacity

## Immediate Next Engineering Tasks

- Add source connectors and parser fixtures in `ingestion`
- Implement clause-level diffing and legal citation normalization in `processing`
- Integrate hybrid retrieval index in `retrieval`
- Enforce JSON schema + citation spans in `generation`
- Add claim-level NLI verifier and abstention calibration in `verification`
- Add evaluator and ablation runner under `eval/`
