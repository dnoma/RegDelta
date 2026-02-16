from __future__ import annotations

import argparse
from pathlib import Path

from regdelta.eval.harness import run_eval


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Compare prompt-only and RAG outputs.")
    p.add_argument("--prompt", required=True, help="Path to prompt-only verified pack JSON")
    p.add_argument("--rag", required=True, help="Path to RAG verified pack JSON")
    p.add_argument(
        "--out",
        default="artifacts/reports/eval/comparison_report.json",
        help="Output report path",
    )
    return p


def main() -> None:
    args = parser().parse_args()
    report_path = run_eval(args.prompt, args.rag, args.out)
    print(f"Evaluation report written to: {Path(report_path)}")


if __name__ == "__main__":
    main()
