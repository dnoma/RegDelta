# Evaluation Harness

Current baseline harness includes a deterministic comparison runner for:
- `prompt_only` outputs
- `rag` outputs

## Report Metrics

The runner computes:
- `claim_count`
- `supported_rate`
- `abstention_rate`
- `citation_coverage`
- `average_confidence`
- metric deltas (`rag - prompt_only`)

## Usage

```bash
PYTHONPATH=src python3 eval/run_eval.py \
  --prompt artifacts/reports/prompt_only/verified_pack.json \
  --rag artifacts/reports/rag/verified_pack.json \
  --out artifacts/reports/eval/comparison_report.json
```

## Output

The output is a JSON report containing per-variant metrics and a delta block for quick ablation review.
