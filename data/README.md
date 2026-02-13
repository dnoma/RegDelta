# Data Layout

- `raw/`: fetched source docs and metadata snapshots
- `interim/`: OCR output, parsed segments, intermediate transforms
- `processed/`: normalized clause-level records and delta sets
- `eval/`: benchmark/test annotations and evaluation datasets

Keep large or sensitive datasets out of Git; version with manifests and checksums.
