from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.chunker import ASTChunker

def get_git_commit(dir_path: Path) -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=dir_path)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown-commit"

def chunk_directory(dir_path: Path, repo_name: str, commit: str) -> dict:
    all_chunks = []
    
    # Recursively find all .py files, excluding .git, __pycache__, and tests/schemas/etc.
    for py_file in dir_path.rglob("*.py"):
        # Exclude common dirs
        parts = py_file.relative_to(dir_path).parts
        if any(p in parts for p in (".git", "__pycache__", "tests", "scripts", ".agents", "build", "dist")):
            continue
            
        rel_path = str(py_file.relative_to(dir_path)).replace("\\", "/")
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Failed to read {py_file}: {e}", file=sys.stderr)
            continue
            
        chunker = ASTChunker(rel_path, content)
        all_chunks.extend(chunker.chunk())
        
    return {
        "repository": repo_name,
        "commit": commit,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "chunks": all_chunks
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="AST Chunker CLI Driver")
    parser.add_argument("--dir", type=str, default=str(ROOT), help="Directory to scan for Python files")
    parser.add_argument("--repo", type=str, default="Shoko-official/llm-rag-reference", help="Repository name")
    parser.add_argument("--commit", type=str, help="Repository commit hash")
    parser.add_argument("--output", type=str, help="Output JSON index path")
    
    args = parser.parse_args()
    
    dir_path = Path(args.dir).resolve()
    commit = args.commit if args.commit else get_git_commit(dir_path)
    
    index_data = chunk_directory(dir_path, args.repo, commit)
    
    output_path = Path(args.output) if args.output else ROOT / "rag" / "index.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)
        
    try:
        # Use Path to output relative to ROOT
        rel_out = output_path.relative_to(ROOT)
    except ValueError:
        rel_out = output_path
    print(f"AST Chunker completed. Saved {len(index_data['chunks'])} chunks to {rel_out}")

if __name__ == "__main__":
    main()
