import json
import tempfile
import unittest
from pathlib import Path

from regdelta.stages.packaging import run_packaging


class PackagingStageTests(unittest.TestCase):
    def test_packaging_exports_json_md_and_audit_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "artifacts" / "logs" / "runs" / "pack_1"
            run_dir.mkdir(parents=True, exist_ok=True)

            verification_dir = run_dir / "verification"
            verification_dir.mkdir(parents=True, exist_ok=True)

            verified_path = verification_dir / "verified_pack.json"
            verified_path.write_text(
                json.dumps(
                    {
                        "status": "ok",
                        "claims": [
                            {
                                "claim_id": "claim_001",
                                "statement": "deadline changed",
                                "verdict": "unsupported",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            abstention_path = verification_dir / "abstention_report.json"
            abstention_path.write_text(
                json.dumps({"total_claims": 1, "abstained": 1}),
                encoding="utf-8",
            )

            context = {
                "config": {"packaging": {"output_formats": ["json", "md"]}},
                "run_dir": run_dir,
                "artifacts": {
                    "verification": {
                        "verified_pack": str(verified_path),
                        "abstention_report": str(abstention_path),
                    }
                },
            }

            result = run_packaging(context)
            json_payload = json.loads(
                Path(result["compliance_pack_json"]).read_text(encoding="utf-8")
            )
            self.assertEqual(json_payload["status"], "ok")
            self.assertEqual(json_payload["abstention_report"]["abstained"], 1)
            self.assertTrue(json_payload["required_actions"])

            md_text = Path(result["compliance_pack_md"]).read_text(encoding="utf-8")
            self.assertIn("# Compliance Pack", md_text)
            self.assertIn("claim_001", md_text)

            audit_payload = json.loads(
                Path(result["audit_bundle_manifest"]).read_text(encoding="utf-8")
            )
            self.assertEqual(audit_payload["status"], "ok")
            self.assertIn("compliance_pack_json", audit_payload["artifacts"])

    def test_packaging_handles_missing_verification_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "artifacts" / "logs" / "runs" / "pack_2"
            run_dir.mkdir(parents=True, exist_ok=True)

            context = {
                "config": {"packaging": {"output_formats": ["json", "md"]}},
                "run_dir": run_dir,
                "artifacts": {"verification": {}},
            }

            result = run_packaging(context)
            json_payload = json.loads(
                Path(result["compliance_pack_json"]).read_text(encoding="utf-8")
            )
            self.assertEqual(json_payload["status"], "ok")
            self.assertGreaterEqual(len(json_payload["warnings"]), 1)


if __name__ == "__main__":
    unittest.main()
