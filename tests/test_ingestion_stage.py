import json
import tempfile
import unittest
from pathlib import Path

from regdelta.stages.ingestion import run_ingestion


class IngestionStageTests(unittest.TestCase):
    def test_ingests_jsonl_documents_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            source_dir = repo_root / "data" / "raw"
            source_dir.mkdir(parents=True, exist_ok=True)

            source_path = source_dir / "documents.jsonl"
            source_path.write_text(
                "\n".join(
                    [
                        json.dumps({"doc_id": "doc_a", "text": "Article 1. Keep records."}),
                        json.dumps({"doc_id": "doc_b", "text": "Article 2. Report changes."}),
                        json.dumps({"doc_id": "doc_a", "text": "Article 1. Keep audited records."}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            run_dir = repo_root / "artifacts" / "logs" / "runs" / "test_run"
            run_dir.mkdir(parents=True, exist_ok=True)

            context = {
                "config": {
                    "ingestion": {
                        "sources": [
                            {
                                "name": "fixture_docs",
                                "type": "jsonl",
                                "enabled": True,
                                "path": "data/raw/documents.jsonl",
                            }
                        ]
                    }
                },
                "repo_root": repo_root,
                "run_dir": run_dir,
                "artifacts": {},
            }

            result = run_ingestion(context)

            manifest_path = Path(result["raw_manifest"])
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["document_count"], 2)
            self.assertEqual(manifest["duplicate_doc_ids"], 1)

            documents_path = Path(result["documents"])
            self.assertTrue(documents_path.exists())
            docs = [json.loads(line) for line in documents_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([doc["doc_id"] for doc in docs], ["doc_a", "doc_b"])
            self.assertEqual(docs[0]["text"], "Article 1. Keep audited records.")
            self.assertTrue(all(doc["checksum"] for doc in docs))


if __name__ == "__main__":
    unittest.main()
