from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parents[1]

def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)

def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"File not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        fail(f"Failed to parse JSON from {path}: {e}")

def validate_index_file(index_path: Path, schema_path: Path) -> None:
    schema = load_json(schema_path)
    data = load_json(index_path)
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        fail(f"Index validation error for {index_path.name}: {e.message}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate RAG index files against schemas")
    parser.add_argument("--index", type=str, help="Path to a RAG index JSON file to validate")
    parser.add_argument("--schema", type=str, help="Path to the RAG index JSON schema")
    
    args = parser.parse_args()
    
    schema_path = Path(args.schema) if args.schema else ROOT / "rag" / "schemas" / "index.json"
    
    if args.index:
        validate_index_file(Path(args.index), schema_path)
        print(f"Successfully validated index file: {args.index}")
    else:
        # Find all JSON files in rag/ excluding schemas/ and references.json
        rag_dir = ROOT / "rag"
        found = False
        for path in rag_dir.rglob("*.json"):
            if "schemas" in path.parts or path.name == "references.json":
                continue
            validate_index_file(path, schema_path)
            print(f"Successfully validated index file: {path.relative_to(ROOT)}")
            found = True
        if not found:
            print("No RAG index files found to validate.")

if __name__ == "__main__":
    main()
