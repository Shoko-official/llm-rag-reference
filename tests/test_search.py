from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.search import HybridSearcher

class TestHybridSearcher(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_index = {
            "repository": "test/repo",
            "commit": "testcommit",
            "chunks": [
                {
                    "id": "chunk_1",
                    "filepath": "module_a.py",
                    "type": "class",
                    "name": "AttentionMechanism",
                    "start_line": 1,
                    "end_line": 10,
                    "content": "class AttentionMechanism:\n    def compute(self, q, k, v):\n        return q * k * v",
                    "tokens": 20
                },
                {
                    "id": "chunk_2",
                    "filepath": "module_b.py",
                    "type": "function",
                    "name": "dot_product",
                    "start_line": 5,
                    "end_line": 8,
                    "content": "def dot_product(a, b):\n    return sum(x*y for x,y in zip(a,b))",
                    "tokens": 15
                },
                {
                    "id": "chunk_3",
                    "filepath": "module_c.py",
                    "type": "module",
                    "name": "module_c.py",
                    "start_line": 1,
                    "end_line": 5,
                    "content": "# Simple configuration variables\nDEFAULT_DIMENSION = 512\nUSE_BIAS = True",
                    "tokens": 10
                }
            ]
        }
        self.searcher = HybridSearcher(self.mock_index)

    def test_sparse_search(self) -> None:
        # Searching for 'AttentionMechanism' should match chunk_1 due to content
        res = self.searcher.sparse_search("AttentionMechanism", k=3)
        self.assertEqual(res[0]["id"], "chunk_1")
        self.assertGreater(res[0]["score"], 0.0)

        # Searching for nonexistent term should have 0.0 score
        res_none = self.searcher.sparse_search("nonexistentword", k=1)
        self.assertEqual(res_none[0]["score"], 0.0)

    def test_dense_search(self) -> None:
        # Dense character n-gram match on 'config' should map to 'configuration' in chunk_3
        res = self.searcher.dense_search("config", k=3)
        self.assertEqual(res[0]["id"], "chunk_3")
        self.assertGreater(res[0]["score"], 0.0)

    def test_hybrid_search_linear(self) -> None:
        # Hybrid search linear fusion with alpha=0.5
        res = self.searcher.hybrid_search("dot_product", k=3, alpha=0.5, method="linear")
        self.assertEqual(res[0]["id"], "chunk_2")
        self.assertGreater(res[0]["score"], 0.0)

    def test_hybrid_search_rrf(self) -> None:
        # Hybrid search Reciprocal Rank Fusion
        res = self.searcher.hybrid_search("Attention", k=3, method="rrf")
        self.assertEqual(res[0]["id"], "chunk_1")
        # RRF score should be greater than 0
        self.assertGreater(res[0]["score"], 0.0)

    def test_rerank(self) -> None:
        # Perform a search and apply reranker
        initial_results = [
            {"id": "chunk_2", "filepath": "module_b.py", "type": "function", "name": "dot_product", "score": 0.1},
            {"id": "chunk_1", "filepath": "module_a.py", "type": "class", "name": "AttentionMechanism", "score": 0.1}
        ]
        
        # Exact query match to name 'dot_product' should boost chunk_2
        boosted = self.searcher.rerank("dot_product", initial_results, name_boost=0.5)
        self.assertEqual(boosted[0]["id"], "chunk_2")
        # Verify score is base_score + name_boost + type_boost (function type has boost)
        self.assertAlmostEqual(boosted[0]["score"], 0.1 + 0.5 + 0.05)

        # Class type boost (0.1) should beat function type boost (0.05) when scores are equal and no name matches
        boosted_types = self.searcher.rerank("somequery", initial_results)
        self.assertEqual(boosted_types[0]["id"], "chunk_1") # class chunk_1 gets 0.1 + 0.1 = 0.2, function chunk_2 gets 0.1 + 0.05 = 0.15

    def test_cli_execution(self) -> None:
        # Write mock index to temp file to query it
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as tmp:
            json.dump(self.mock_index, tmp)
            tmp_path = tmp.name

        try:
            cli_path = ROOT / "scripts" / "query_search.py"
            
            # Test json output
            res = subprocess.run([
                sys.executable,
                str(cli_path),
                "--index", tmp_path,
                "--query", "AttentionMechanism",
                "--output", "json"
            ], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"CLI output error: {res.stderr}")
            data = json.loads(res.stdout)
            self.assertEqual(data[0]["id"], "chunk_1")

            # Test table output
            res_table = subprocess.run([
                sys.executable,
                str(cli_path),
                "--index", tmp_path,
                "--query", "dot_product",
                "--output", "table"
            ], capture_output=True, text=True)
            self.assertEqual(res_table.returncode, 0, f"CLI table output error: {res_table.stderr}")
            self.assertIn("Rank | ID | Score | Type | Name | Filepath", res_table.stdout)
            self.assertIn("chunk_2", res_table.stdout)
        finally:
            import os
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    def test_telemetry_spans(self) -> None:
        self.searcher.reset_trace()
        self.assertEqual(len(self.searcher.last_spans), 0)
        
        results = self.searcher.hybrid_search("Attention", k=2)
        results = self.searcher.rerank("Attention", results, k=2)
        
        spans = self.searcher.last_spans
        self.assertEqual(len(spans), 2)
        
        hybrid_span = next(s for s in spans if s["name"] == "hybrid_search")
        rerank_span = next(s for s in spans if s["name"] == "rerank_chunks")
        
        # Verify required telemetry fields
        for span in (hybrid_span, rerank_span):
            self.assertIn("span_id", span)
            self.assertIn("trace_id", span)
            self.assertIn("start_time", span)
            self.assertIn("end_time", span)
            self.assertIn("duration_ms", span)
            self.assertEqual(span["service_name"], "rag")
            self.assertEqual(span["status"], "ok")
            
        # Context propagation
        self.assertEqual(hybrid_span["trace_id"], rerank_span["trace_id"])
        self.assertEqual(rerank_span["parent_span_id"], hybrid_span["span_id"])
        self.assertEqual(hybrid_span["parent_span_id"], "N/A")

if __name__ == "__main__":
    unittest.main()
