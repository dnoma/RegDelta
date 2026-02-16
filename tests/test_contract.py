import unittest
from pathlib import Path
from unittest.mock import patch

from regdelta.config import load_config
from regdelta.pipeline import run_pipeline


class ContractValidationTests(unittest.TestCase):
    def test_stage_order_validation(self) -> None:
        cfg = load_config("configs/base.json", "dev_cpu")
        with self.assertRaisesRegex(ValueError, "out of contract order"):
            run_pipeline(cfg, ["processing", "ingestion"], repo_root=Path("."))

    def test_missing_inputs_validation(self) -> None:
        cfg = load_config("configs/base.json", "dev_cpu")
        with self.assertRaisesRegex(ValueError, "missing required inputs"):
            run_pipeline(cfg, ["processing"], repo_root=Path("."))

    def test_missing_outputs_validation(self) -> None:
        cfg = load_config("configs/base.json", "dev_cpu")

        with patch(
            "regdelta.pipeline.STAGE_REGISTRY",
            {"ingestion": lambda _context: {"unexpected_output": "x"}},
        ):
            with self.assertRaisesRegex(ValueError, "missing required outputs"):
                run_pipeline(cfg, ["ingestion"], repo_root=Path("."))


if __name__ == "__main__":
    unittest.main()
