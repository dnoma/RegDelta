import json
import tempfile
import unittest
from pathlib import Path

from regdelta.stages.retrieval import run_retrieval


class RetrievalStageTests(unittest.TestCase):
    def test_builds_index_and_returns_ranked_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            run_dir = repo_root / "artifacts" / "logs" / "runs" / "test_run"
            run_dir.mkdir(parents=True, exist_ok=True)

            segments_path = run_dir / "processing" / "normalized_segments.json"
            segments_path.parent.mkdir(parents=True, exist_ok=True)
            segments_payload = {
                "status": "ok",
                "segments": [
                    {
                        "segment_id": "doc_a:cl_1",
                        "doc_id": "doc_a",
                        "clause_id": "cl_1",
                        "text": "Keep records and maintain logs.",
                    },
                    {
                        "segment_id": "doc_b:cl_1",
                        "doc_id": "doc_b",
                        "clause_id": "cl_1",
                        "text": "Submit compliance report within 15 days deadline.",
                    },
                    {
                        "segment_id": "doc_c:cl_1",
                        "doc_id": "doc_c",
                        "clause_id": "cl_1",
                        "text": "Notify regulator about incidents.",
                    },
                ],
            }
            segments_path.write_text(json.dumps(segments_payload, ensure_ascii=False), encoding="utf-8")

            context = {
                "config": {
                    "retrieval": {
                        "top_k": 2,
                        "rerank_top_k": 1,
                        "queries": [{"query_id": "q_1", "query_text": "report deadline"}],
                    }
                },
                "repo_root": repo_root,
                "run_dir": run_dir,
                "artifacts": {"processing": {"normalized_segments": str(segments_path)}},
            }

            result = run_retrieval(context)

            candidates_payload = json.loads(
                Path(result["retrieval_candidates"]).read_text(encoding="utf-8")
            )
            self.assertEqual(candidates_payload["status"], "ok")
            self.assertEqual(candidates_payload["query_count"], 1)
            top_candidate = candidates_payload["candidates"][0]["candidates"][0]
            self.assertEqual(top_candidate["doc_id"], "doc_b")

            index_payload = json.loads(Path(result["evidence_index"]).read_text(encoding="utf-8"))
            self.assertEqual(index_payload["status"], "ok")
            self.assertEqual(index_payload["index"]["segment_count"], 3)
            self.assertGreater(index_payload["index"]["vocabulary_size"], 0)


if __name__ == "__main__":
    unittest.main()
