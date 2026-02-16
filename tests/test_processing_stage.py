import json
import tempfile
import unittest
from pathlib import Path

from regdelta.stages.processing import run_processing


class ProcessingStageTests(unittest.TestCase):
    def test_segments_clauses_and_extracts_version_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            run_dir = repo_root / "artifacts" / "logs" / "runs" / "test_run"
            run_dir.mkdir(parents=True, exist_ok=True)

            documents_path = run_dir / "ingestion" / "documents.jsonl"
            documents_path.parent.mkdir(parents=True, exist_ok=True)
            documents = [
                {
                    "doc_id": "doc_old",
                    "text": "Article 1 Keep records.\nArticle 2 Submit report within 30 days.",
                },
                {
                    "doc_id": "doc_new",
                    "replaces_doc_id": "doc_old",
                    "text": (
                        "Article 1 Keep records.\n"
                        "Article 2 Submit report within 15 days.\n"
                        "Article 3 Notify regulator within 5 days."
                    ),
                },
            ]
            documents_path.write_text(
                "".join(json.dumps(doc, ensure_ascii=False) + "\n" for doc in documents),
                encoding="utf-8",
            )

            context = {
                "config": {"processing": {"segmentation_granularity": "clause"}},
                "repo_root": repo_root,
                "run_dir": run_dir,
                "artifacts": {"ingestion": {"documents": str(documents_path)}},
            }

            result = run_processing(context)

            segments_payload = json.loads(Path(result["normalized_segments"]).read_text(encoding="utf-8"))
            self.assertEqual(segments_payload["status"], "ok")
            self.assertEqual(segments_payload["segment_count"], 5)

            deltas_payload = json.loads(Path(result["deltas"]).read_text(encoding="utf-8"))
            self.assertEqual(deltas_payload["status"], "ok")
            self.assertEqual(deltas_payload["delta_count"], 2)
            delta_types = {delta["change_type"] for delta in deltas_payload["deltas"]}
            self.assertEqual(delta_types, {"amended", "added"})


if __name__ == "__main__":
    unittest.main()
