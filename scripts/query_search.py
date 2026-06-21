from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.search import HybridSearcher

def main() -> None:
    parser = argparse.ArgumentParser(description="Query search pipeline for RAG Reference")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--index", type=str, help="Path to RAG index JSON file")
    parser.add_argument("--mode", type=str, choices=["sparse", "dense", "hybrid"], default="hybrid", help="Search mode")
    parser.add_argument("--method", type=str, choices=["linear", "rrf"], default="linear", help="Hybrid fusion method")
    parser.add_argument("--k", type=int, default=5, help="Number of results to retrieve")
    parser.add_argument("--alpha", type=float, default=0.5, help="Alpha weight for linear hybrid search")
    parser.add_argument("--no-rerank", action="store_true", help="Disable the reranker stage")
    parser.add_argument("--output", type=str, choices=["json", "table"], default="json", help="Output format")

    args = parser.parse_args()

    # Determine index path
    if args.index:
        index_path = Path(args.index)
    else:
        index_path = ROOT / "rag" / "index.json"
        if not index_path.is_file():
            index_path = ROOT / "rag" / "mock_index.json"

    if not index_path.is_file():
        print(f"Error: Index file not found at {index_path}", file=sys.stderr)
        sys.exit(1)

    try:
        searcher = HybridSearcher(index_path)
    except Exception as e:
        print(f"Error: Failed to load/parse index file {index_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Perform search based on mode
    if args.mode == "sparse":
        results = searcher.sparse_search(args.query, k=args.k)
    elif args.mode == "dense":
        results = searcher.dense_search(args.query, k=args.k)
    else:
        results = searcher.hybrid_search(args.query, k=args.k, alpha=args.alpha, method=args.method)

    # Rerank unless disabled
    if not args.no_rerank:
        results = searcher.rerank(args.query, results, k=args.k)

    # Format output
    if args.output == "json":
        print(json.dumps(results, indent=2))
    elif args.output == "table":
        if not results:
            print("No results found.")
            return
        
        headers = ["Rank", "ID", "Score", "Type", "Name", "Filepath"]
        # Print header
        header_row = " | ".join(headers)
        separator = " | ".join(["---"] * len(headers))
        print(f"| {header_row} |")
        print(f"| {separator} |")
        for i, res in enumerate(results):
            rank = i + 1
            cid = res.get("id", "")
            score = f"{res.get('score', 0.0):.4f}"
            ctype = res.get("type", "")
            name = res.get("name", "") or "-"
            filepath = res.get("filepath", "")
            print(f"| {rank} | {cid} | {score} | {ctype} | {name} | {filepath} |")

if __name__ == "__main__":
    main()
