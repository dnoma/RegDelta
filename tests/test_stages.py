import json
import tempfile
import unittest
from pathlib import Path

from regdelta.stages.processing import run_processing
from regdelta.stages.retrieval import run_retrieval
from regdelta.stages.verification import run_verification


class ProcessingStageTests(unittest.TestCase):
    def test_processing_writes_segments_and_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "processing" / "test_run"
            run_dir.mkdir(parents=True, exist_ok=True)

            context = {
                "config": {"processing": {"segmentation_granularity": "clause"}},
                "run_dir": run_dir,
            }

            result = run_processing(context)

            segments_path = Path(result["normalized_segments"])
            deltas_path = Path(result["deltas"])  # type: ignore[assignment]

            self.assertTrue(segments_path.exists())
            with segments_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            self.assertEqual(payload.get("status"), "ok")
            self.assertIn("granularity", payload)

            self.assertTrue(deltas_path.exists())
            with deltas_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            self.assertEqual(payload.get("status"), "ok")
            self.assertIn("delta_count", payload)


class RetrievalStageTests(unittest.TestCase):
    def test_retrieval_writes_candidates_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "retrieval" / "test_run"
            run_dir.mkdir(parents=True, exist_ok=True)

            context = {
                "config": {"retrieval": {"top_k": 5, "rerank_top_k": 2}},
                "run_dir": run_dir,
            }

            result = run_retrieval(context)

            candidates_path = Path(result["retrieval_candidates"])
            index_path = Path(result["evidence_index"])

            self.assertTrue(candidates_path.exists())
            with candidates_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            self.assertEqual(payload.get("status"), "ok")
            self.assertEqual(payload.get("top_k"), 5)

            self.assertTrue(index_path.exists())
            with index_path.open("r", encoding="utf-8") as f:
                index_payload = json.load(f)
            self.assertEqual(index_payload.get("status"), "ok")
            self.assertIn("index", index_payload)


class VerificationStageTests(unittest.TestCase):
    def test_verification_writes_pack_and_abstention_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "verification" / "test_run"
            run_dir.mkdir(parents=True, exist_ok=True)

            context = {
                "config": {"verification": {"abstain_when_unsupported": True}},
                "run_dir": run_dir,
            }

            result = run_verification(context)

            verified_path = Path(result["verified_pack"])
            abstention_path = Path(result["abstention_report"])

            self.assertTrue(verified_path.exists())
            with verified_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            self.assertEqual(payload.get("status"), "scaffolded")
            self.assertIn("confidence_summary", payload)

            self.assertTrue(abstention_path.exists())
            with abstention_path.open("r", encoding="utf-8") as f:
                abstention_payload = json.load(f)
            self.assertIn("total_claims", abstention_payload)


if __name__ == "__main__":
    unittest.main()
