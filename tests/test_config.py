import unittest

from regdelta.config import load_config, resolve_stage_list


class ConfigTests(unittest.TestCase):
    def test_load_config_with_profile_override(self) -> None:
        cfg = load_config("configs/base.json", "dev_cpu")
        self.assertEqual(cfg["runtime"]["max_workers"], 2)
        self.assertEqual(cfg["retrieval"]["top_k"], 4)

    def test_resolve_stage_list_override(self) -> None:
        cfg = load_config("configs/base.json", "dev_cpu")
        stages = resolve_stage_list(cfg, "ingestion,processing")
        self.assertEqual(stages, ["ingestion", "processing"])


if __name__ == "__main__":
    unittest.main()
