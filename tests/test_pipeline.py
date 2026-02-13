import unittest
from pathlib import Path

from regdelta.config import load_config, resolve_stage_list
from regdelta.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_summary(self) -> None:
        cfg = load_config("configs/base.json", "dev_cpu")
        stages = resolve_stage_list(cfg, "ingestion,processing")
        summary_path = run_pipeline(cfg, stages, repo_root=Path("."))
        self.assertTrue(summary_path.exists())


if __name__ == "__main__":
    unittest.main()
