from __future__ import annotations

import argparse
from pathlib import Path

from regdelta.config import load_config, resolve_stage_list
from regdelta.pipeline import run_pipeline


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RegDelta on-prem pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", default="configs/base.json", help="Path to base config")
        p.add_argument("--profile", default=None, help="Override profile name")
        p.add_argument("--stages", default=None, help="Comma-separated subset of stages")

    add_common(subparsers.add_parser("plan", help="Print stage execution plan"))
    add_common(subparsers.add_parser("run", help="Run pipeline stages"))

    return parser


def main() -> None:
    args = _parser().parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    config = load_config(args.config, args.profile)
    stages = resolve_stage_list(config, args.stages)

    if args.command == "plan":
        print("Execution profile:", config.get("runtime", {}).get("profile"))
        print("Stages:", " -> ".join(stages))
        return

    summary_path = run_pipeline(config=config, stages=stages, repo_root=repo_root)
    print(f"Pipeline run completed. Summary: {summary_path}")


if __name__ == "__main__":
    main()
