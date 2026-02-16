import json
import tempfile
import unittest
from pathlib import Path

from regdelta.stages.generation import run_generation


class GenerationStageTests(unittest.TestCase):
    def test_generation_builds_schema_enforced_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            run_dir = repo_root / "artifacts" / "logs" / "runs" / "run_1"
            run_dir.mkdir(parents=True, exist_ok=True)

            processing_dir = run_dir / "processing"
            processing_dir.mkdir(parents=True, exist_ok=True)
            deltas_path = processing_dir / "deltas.json"
            deltas_path.write_text(
                json.dumps(
                    {
                        "status": "ok",
                        "deltas": [
                            {
                                "old_doc_id": "doc_old",
                                "new_doc_id": "doc_new",
                                "change_type": "amended",
                                "clause_id": "cl_1",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            retrieval_dir = run_dir / "retrieval"
            retrieval_dir.mkdir(parents=True, exist_ok=True)
            retrieval_path = retrieval_dir / "retrieval_candidates.json"
            retrieval_path.write_text(
                json.dumps(
                    {
                        "status": "ok",
                        "candidates": [
                            {
                                "query_id": "delta_1",
                                "candidates": [
                                    {
                                        "segment_id": "doc_new:cl_1",
                                        "doc_id": "doc_new",
                                        "clause_id": "cl_1",
                                        "rank": 1,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            context = {
                "config": {"generation": {"schema_version": "compliance_pack_v1"}},
                "run_dir": run_dir,
                "artifacts": {
                    "processing": {"deltas": str(deltas_path)},
                    "retrieval": {"retrieval_candidates": str(retrieval_path)},
                },
            }

            result = run_generation(context)
            draft_path = Path(result["compliance_pack_draft"])
            self.assertTrue(draft_path.exists())

            payload = json.loads(draft_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["schema_version"], "compliance_pack_v1")
            self.assertIn("summary", payload)
            self.assertIn("required_actions", payload)
            self.assertEqual(len(payload["claims"]), 1)
            self.assertEqual(payload["claims"][0]["claim_id"], "claim_001")
            self.assertTrue(payload["claims"][0]["citations"])

    def test_generation_handles_missing_upstream_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "artifacts" / "logs" / "runs" / "run_2"
            run_dir.mkdir(parents=True, exist_ok=True)

            context = {
                "config": {"generation": {"schema_version": "compliance_pack_v1"}},
                "run_dir": run_dir,
                "artifacts": {},
            }

            result = run_generation(context)
            payload = json.loads(Path(result["compliance_pack_draft"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["claims"][0]["change_type"], "none")
            self.assertGreaterEqual(len(payload["warnings"]), 1)


if __name__ == "__main__":
    unittest.main()
