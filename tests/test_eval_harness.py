import json
import tempfile
import unittest
from pathlib import Path

from regdelta.eval.harness import compare_variants, compute_metrics, run_eval


class EvalHarnessTests(unittest.TestCase):
    def test_compute_metrics(self) -> None:
        payload = {
            "claims": [
                {
                    "claim_id": "claim_1",
                    "verdict": "supported",
                    "abstained": False,
                    "citations": [{"doc_id": "doc_1"}],
                    "confidence": 0.9,
                },
                {
                    "claim_id": "claim_2",
                    "verdict": "unsupported",
                    "abstained": True,
                    "citations": [],
                    "confidence": 0.2,
                },
            ]
        }
        metrics = compute_metrics(payload, variant="rag")
        self.assertEqual(metrics["claim_count"], 2)
        self.assertEqual(metrics["supported_rate"], 0.5)
        self.assertEqual(metrics["abstention_rate"], 0.5)
        self.assertEqual(metrics["citation_coverage"], 0.5)
        self.assertEqual(metrics["average_confidence"], 0.55)

    def test_compare_and_run_eval(self) -> None:
        prompt_payload = {
            "claims": [
                {"verdict": "unsupported", "abstained": True, "citations": [], "confidence": 0.2}
            ]
        }
        rag_payload = {
            "claims": [
                {
                    "verdict": "supported",
                    "abstained": False,
                    "citations": [{"doc_id": "doc_1"}],
                    "confidence": 0.9,
                }
            ]
        }
        compared = compare_variants(prompt_payload, rag_payload)
        self.assertEqual(compared["delta"]["supported_rate"], 1.0)
        self.assertEqual(compared["delta"]["citation_coverage"], 1.0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            prompt_path = Path(tmp_dir) / "prompt.json"
            rag_path = Path(tmp_dir) / "rag.json"
            out_path = Path(tmp_dir) / "report.json"
            prompt_path.write_text(json.dumps(prompt_payload), encoding="utf-8")
            rag_path.write_text(json.dumps(rag_payload), encoding="utf-8")

            written = run_eval(prompt_path, rag_path, out_path)
            self.assertEqual(Path(written), out_path)
            report = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertIn("variants", report)
            self.assertIn("delta", report)


if __name__ == "__main__":
    unittest.main()
