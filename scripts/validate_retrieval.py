from __future__ import annotations

"""validate_retrieval.py - Validate RAG retrieval accuracy against expected targets.

This script executes search queries against the hybrid search pipeline and checks if
the expected document sources (chunks) are retrieved in the top results. It calculates
accuracy metrics like Recall@k and Mean Reciprocal Rank (MRR).
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.search import HybridSearcher

# Define evaluation cases. For each query, specify the expected chunk name and filepath.
EVAL_CASES = [
    {
        "query": "ASTChunker class",
        "expected_name": "ASTChunker",
        "expected_type": "class",
        "expected_filepath": "rag/chunker.py"
    },
    {
        "query": "estimate token count",
        "expected_name": "estimate_tokens",
        "expected_type": "function",
        "expected_filepath": "rag/chunker.py"
    },
    {
        "query": "HybridSearcher class constructor",
        "expected_name": "HybridSearcher",
        "expected_type": "class",
        "expected_filepath": "rag/search.py"
    },
    {
        "query": "tokenize text query lower case",
        "expected_name": "tokenize",
        "expected_type": "function",
        "expected_filepath": "rag/search.py"
    },
    {
        "query": "Reciprocal Rank Fusion hybrid",
        "expected_name": "hybrid_search",
        "expected_type": "function",
        "expected_filepath": "rag/search.py"
    },
    {
        "query": "cosine similarity calculation vectors",
        "expected_name": "cosine_similarity",
        "expected_type": "function",
        "expected_filepath": "rag/search.py"
    }
]

def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)

def run_evaluation(searcher: HybridSearcher, k: int = 5) -> tuple[float, float, list[dict]]:
    mrr_sum = 0.0
    recall_sum = 0.0
    details = []

    for case in EVAL_CASES:
        query = case["query"]
        expected_name = case["expected_name"]
        expected_filepath = case["expected_filepath"]

        # Run hybrid search and then rerank
        results = searcher.hybrid_search(query, k=k)
        results = searcher.rerank(query, results, k=k)

        # Find the rank of the expected target
        found_rank = None
        for rank, res in enumerate(results, start=1):
            if res.get("name") == expected_name and res.get("filepath") == expected_filepath:
                found_rank = rank
                break

        if found_rank is not None:
            mrr_val = 1.0 / found_rank
            recall_val = 1.0
        else:
            mrr_val = 0.0
            recall_val = 0.0

        mrr_sum += mrr_val
        recall_sum += recall_val

        details.append({
            "query": query,
            "expected_name": expected_name,
            "expected_filepath": expected_filepath,
            "found_rank": found_rank,
            "mrr": mrr_val,
            "recall": recall_val,
            "top_results": [{"id": r.get("id"), "name": r.get("name"), "score": r.get("score")} for r in results]
        })

    num_cases = len(EVAL_CASES)
    avg_mrr = mrr_sum / num_cases if num_cases > 0 else 0.0
    avg_recall = recall_sum / num_cases if num_cases > 0 else 0.0

    return avg_mrr, avg_recall, details

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate RAG retrieval accuracy")
    parser.add_argument("--index", type=str, help="Path to RAG index JSON file")
    parser.add_argument("--k", type=int, default=5, help="Top-K cutoff for retrieval evaluation")
    parser.add_argument("--min-mrr", type=float, default=0.7, help="Minimum required Mean Reciprocal Rank")
    parser.add_argument("--min-recall", type=float, default=0.8, help="Minimum required Recall@K")
    args = parser.parse_args()

    # Determine index path
    if args.index:
        index_path = Path(args.index)
    else:
        index_path = ROOT / "rag" / "index.json"
        if not index_path.is_file():
            index_path = ROOT / "rag" / "mock_index.json"

    if not index_path.is_file():
        fail(f"Index file not found at {index_path}. Run scripts/chunk_repo.py first.")

    try:
        searcher = HybridSearcher(index_path)
    except Exception as e:
        fail(f"Failed to load searcher from {index_path}: {e}")

    print(f"Loaded index from: {index_path}")
    print(f"Evaluating retrieval accuracy over {len(EVAL_CASES)} cases...")

    avg_mrr, avg_recall, details = run_evaluation(searcher, k=args.k)

    print("\n--- Evaluation Results ---")
    print(f"Recall@{args.k}: {avg_recall:.4f} (Required: >= {args.min_recall:.2f})")
    print(f"MRR:       {avg_mrr:.4f} (Required: >= {args.min_mrr:.2f})")
    print("--------------------------")

    failed = False
    if avg_recall < args.min_recall:
        print(f"Validation FAILED: Recall@{args.k} ({avg_recall:.4f}) is below threshold {args.min_recall:.2f}", file=sys.stderr)
        failed = True
    if avg_mrr < args.min_mrr:
        print(f"Validation FAILED: MRR ({avg_mrr:.4f}) is below threshold {args.min_mrr:.2f}", file=sys.stderr)
        failed = True

    if failed:
        print("\nFailed cases detail:")
        for detail in details:
            if detail["found_rank"] is None:
                print(f"  Query: '{detail['query']}'")
                print(f"    Expected: {detail['expected_name']} in {detail['expected_filepath']}")
                print("    Top retrieved:")
                for i, tr in enumerate(detail["top_results"], start=1):
                    print(f"      {i}. {tr['name']} (score: {tr['score']:.4f})")
        sys.exit(1)

    print("Retrieval validation successful! All accuracy metrics passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
