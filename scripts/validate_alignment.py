from __future__ import annotations

"""validate_alignment.py - Verify RAG index alignment with actual source code files.

Checks:
1. Every file referenced in the index exists in the codebase.
2. The lines [start_line, end_line] in the source file match the chunk's content.
3. Chunks are up to date and not orphaned.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def normalize_code(code: str) -> str:
    # Remove carriage returns, normalize whitespace to compare content fairly
    return "\n".join(line.strip() for line in code.replace("\r", "").splitlines() if line.strip())


def check_alignment(index_path: Path) -> bool:
    if not index_path.is_file():
        fail(f"Index file not found at {index_path}")

    try:
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        fail(f"Failed to read index: {e}")

    chunks = data.get("chunks", [])
    if not chunks:
        print("Warning: Index contains no chunks to validate.", file=sys.stderr)
        return True

    misalignments = []
    missing_files = set()

    for chunk in chunks:
        cid = chunk.get("id")
        filepath = chunk.get("filepath")
        if not filepath:
            misalignments.append(f"Chunk {cid} missing 'filepath'")
            continue

        file_path = ROOT / filepath
        if not file_path.is_file():
            missing_files.add(filepath)
            misalignments.append(f"Chunk {cid} refers to non-existent file: {filepath}")
            continue

        start = chunk.get("start_line")
        end = chunk.get("end_line")
        content = chunk.get("content")

        if start is None or end is None or content is None:
            misalignments.append(f"Chunk {cid} in {filepath} missing start_line, end_line, or content")
            continue

        # Load original file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except Exception as e:
            misalignments.append(f"Failed to read file {filepath} for chunk {cid}: {e}")
            continue

        # Validate line range
        if start < 1 or end > len(lines) or start > end:
            misalignments.append(
                f"Chunk {cid} in {filepath} has invalid line range [{start}:{end}] for file with {len(lines)} lines"
            )
            continue

        # Extract lines
        source_segment = "\n".join(lines[start - 1 : end])

        # Compare normalized
        norm_source = normalize_code(source_segment)
        norm_chunk = normalize_code(content)

        if norm_source != norm_chunk:
            misalignments.append(
                f"Chunk {cid} ({chunk.get('name')}) in {filepath} (lines {start}-{end}) is out of sync with actual file content"
            )

    if misalignments:
        print(f"\nFound {len(misalignments)} misalignment issues in {index_path.name}:", file=sys.stderr)
        for issue in misalignments[:10]:
            print(f"  - {issue}", file=sys.stderr)
        if len(misalignments) > 10:
            print(f"  ... and {len(misalignments) - 10} more.", file=sys.stderr)
        return False

    print(f"All {len(chunks)} chunks in {index_path.name} are perfectly aligned with source files.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Check index alignment with source files")
    parser.add_argument("--index", type=str, help="Path to RAG index JSON file")
    args = parser.parse_args()

    if args.index:
        index_path = Path(args.index)
    else:
        index_path = ROOT / "rag" / "index.json"
        if not index_path.is_file():
            index_path = ROOT / "rag" / "mock_index.json"

    success = check_alignment(index_path)
    if not success:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
