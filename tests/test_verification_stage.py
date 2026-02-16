import json
import tempfile
import unittest
from pathlib import Path

from regdelta.stages.verification import run_verification


class VerificationStageFeatureTests(unittest.TestCase):
    def test_verification_marks_supported_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "artifacts" / "logs" / "runs" / "verify_1"
            run_dir.mkdir(parents=True, exist_ok=True)

            generation_dir = run_dir / "generation"
            generation_dir.mkdir(parents=True, exist_ok=True)
            draft_path = generation_dir / "compliance_pack_draft.json"
            draft_path.write_text(
                json.dumps(
                    {
                        "claims": [
                            {
                                "claim_id": "claim_001",
                                "statement": "reporting deadline changed to 15 days",
                                "citations": [],
                            }
                        ]
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
                        "candidates": [
                            {
                                "query_id": "q_1",
                                "candidates": [
                                    {
                                        "segment_id": "doc_1:cl_1",
                                        "doc_id": "doc_1",
                                        "clause_id": "cl_1",
                                        "text": "The reporting deadline changed to 15 days for filing.",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            context = {
                "config": {
                    "verification": {
                        "claim_confidence_threshold": 0.6,
                        "abstain_when_unsupported": True,
                    }
                },
                "run_dir": run_dir,
                "artifacts": {
                    "generation": {"compliance_pack_draft": str(draft_path)},
                    "retrieval": {"retrieval_candidates": str(retrieval_path)},
                },
            }

            result = run_verification(context)
            verified_payload = json.loads(Path(result["verified_pack"]).read_text(encoding="utf-8"))
            self.assertEqual(verified_payload["status"], "ok")
            self.assertEqual(verified_payload["claims"][0]["verdict"], "supported")
            self.assertFalse(verified_payload["claims"][0]["abstained"])

    def test_verification_abstains_on_unsupported_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "artifacts" / "logs" / "runs" / "verify_2"
            run_dir.mkdir(parents=True, exist_ok=True)

            generation_dir = run_dir / "generation"
            generation_dir.mkdir(parents=True, exist_ok=True)
            draft_path = generation_dir / "compliance_pack_draft.json"
            draft_path.write_text(
                json.dumps(
                    {
                        "claims": [
                            {
                                "claim_id": "claim_002",
                                "statement": "tax rate reduced to zero percent",
                                "citations": [],
                            }
                        ]
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
                        "candidates": [
                            {
                                "query_id": "q_2",
                                "candidates": [
                                    {
                                        "segment_id": "doc_2:cl_1",
                                        "doc_id": "doc_2",
                                        "clause_id": "cl_1",
                                        "text": "Inspection reporting procedures were clarified.",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            context = {
                "config": {
                    "verification": {
                        "claim_confidence_threshold": 0.7,
                        "abstain_when_unsupported": True,
                    }
                },
                "run_dir": run_dir,
                "artifacts": {
                    "generation": {"compliance_pack_draft": str(draft_path)},
                    "retrieval": {"retrieval_candidates": str(retrieval_path)},
                },
            }

            result = run_verification(context)
            report_payload = json.loads(
                Path(result["abstention_report"]).read_text(encoding="utf-8")
            )
            self.assertEqual(report_payload["total_claims"], 1)
            self.assertEqual(report_payload["abstained"], 1)
            self.assertEqual(report_payload["abstained_claim_ids"], ["claim_002"])


if __name__ == "__main__":
    unittest.main()
