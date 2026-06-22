from __future__ import annotations

"""validate_references.py - Validate RAG references schema compliance and cross-repo integrity.

Checks:
1. Local RAG references (rag/references.json) comply with core reference schema.
2. Extracts Claim and Source associations from llm-architecture-taxonomy and llm-decision-matrix.
3. Matches extracted citations against research ledger sources and claims.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("Error: jsonschema is required.", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def parse_markdown_table(file_path: Path) -> list[dict]:
    if not file_path.is_file():
        return []

    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    headers = []
    rows = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line.startswith("|"):
            continue

        # Check if this is the header row
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if i + 1 < len(lines) and lines[i + 1].strip().startswith("|---"):
            headers = [h.lower().replace(" ", "_") for h in parts]
            continue

        if line.startswith("|---") or not headers:
            continue

        # This is a data row
        row_dict = {}
        for idx, part in enumerate(parts):
            if idx < len(headers):
                val = part.replace("`", "").strip()
                row_dict[headers[idx]] = val

        if row_dict and not row_dict.get(headers[0], "").startswith("---"):
            rows.append(row_dict)

    return rows


def validate_local_references(references_path: Path, schema_path: Path) -> None:
    if not references_path.is_file():
        fail(f"Local references file not found: {references_path}")
    if not schema_path.is_file():
        fail(f"Schema file not found: {schema_path}")

    try:
        with open(references_path, "r", encoding="utf-8") as f:
            references = json.load(f)
    except Exception as e:
        fail(f"Failed to read/parse local references: {e}")

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except Exception as e:
        fail(f"Failed to read/parse schema: {e}")

    print(f"Validating local reference entries in {references_path.name}...")
    for idx, ref in enumerate(references):
        try:
            validate(instance=ref, schema=schema)
        except ValidationError as e:
            fail(f"Reference validation error at index {idx}: {e.message}")

    print("Local references validation successful.")


def validate_cross_repo_citations(
    taxonomy_dir: Path, matrix_dir: Path, ledger_dir: Path
) -> None:
    print("Running cross-repository citation checks...")
    warnings = []
    
    # 1. Parse Taxonomy Glossary
    glossary_path = taxonomy_dir / "taxonomy" / "glossary.md"
    taxonomy_entries = parse_markdown_table(glossary_path)
    
    # 2. Parse Decision Matrix files
    matrix_entries = []
    if matrix_dir.is_dir():
        for path in (matrix_dir / "matrix").glob("*.md"):
            if path.name.lower() == "readme.md":
                continue
            matrix_entries.extend(parse_markdown_table(path))

    # Collect unique claims and sources referenced
    referenced_sources = set()
    referenced_claims = set()

    for entry in taxonomy_entries + matrix_entries:
        source_id = entry.get("source_id")
        claim_id = entry.get("claim_id")

        if source_id and source_id != "N/A":
            # Some entries might have comma-separated sources
            for sid in re.split(r"[,;]", source_id):
                sid = sid.strip()
                if sid:
                    referenced_sources.add(sid)

        if claim_id and claim_id != "N/A":
            for cid in re.split(r"[,;]", claim_id):
                cid = cid.strip()
                if cid:
                    referenced_claims.add(cid)

    # Allow lists for mock/placeholder values that are expected stubs
    mock_stubs = {
        "source-smith-2024", "source-jones-2025", "source-taylor-2026",
        "claim-001", "claim-002", "claim-003"
    }

    # 3. Match against Research Ledger
    if ledger_dir.is_dir():
        # Check sources
        for source_id in sorted(referenced_sources):
            if source_id in mock_stubs:
                continue
            source_file = ledger_dir / "sources" / f"{source_id}.md"
            if not source_file.is_file():
                warnings.append(f"Referenced source '{source_id}' does not exist in ledger repository")

        # Check claims
        for claim_id in sorted(referenced_claims):
            if claim_id in mock_stubs:
                continue
            claim_file = ledger_dir / "claims" / f"{claim_id}.md"
            if not claim_file.is_file():
                warnings.append(f"Referenced claim '{claim_id}' does not exist in ledger repository")
    else:
        print("Warning: Ledger directory not found. Skipping ledger matching.")

    if warnings:
        print("\n--- Cross-Repository Reference Warnings ---", file=sys.stderr)
        for w in warnings:
            print(f"  Warning: {w}", file=sys.stderr)
        print("-------------------------------------------\n", file=sys.stderr)
    else:
        print("Cross-repository citation checks completed with zero warnings.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate RAG references and cross-repo citations")
    parser.add_argument("--references", type=str, help="Path to RAG references JSON file")
    parser.add_argument("--schema", type=str, help="Path to reference schema JSON file")
    parser.add_argument("--taxonomy-dir", type=str, help="Path to taxonomy repository")
    parser.add_argument("--matrix-dir", type=str, help="Path to decision matrix repository")
    parser.add_argument("--ledger-dir", type=str, help="Path to research ledger repository")
    args = parser.parse_args()

    # Default paths relative to ROOT
    ref_path = Path(args.references) if args.references else ROOT / "rag" / "references.json"
    schema_path = Path(args.schema) if args.schema else ROOT.parent / "llm-systems-core" / "schemas" / "reference.json"
    
    tax_dir = Path(args.taxonomy_dir) if args.taxonomy_dir else ROOT.parent / "llm-architecture-taxonomy"
    mat_dir = Path(args.matrix_dir) if args.matrix_dir else ROOT.parent / "llm-decision-matrix"
    led_dir = Path(args.ledger_dir) if args.ledger_dir else ROOT.parent / "llm-systems-research-ledger"

    validate_local_references(ref_path, schema_path)
    validate_cross_repo_citations(tax_dir, mat_dir, led_dir)


if __name__ == "__main__":
    main()
