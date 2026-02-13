#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-onprem_1gpu}"

PYTHONPATH=src python3 -m regdelta.cli run \
  --config configs/base.json \
  --profile "${PROFILE}"
