#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install -e .
echo "Environment ready. Use 'make plan' or 'make run-dev'."
