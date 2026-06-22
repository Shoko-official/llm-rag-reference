from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class TestReferences(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory(dir=str(ROOT))
        self.tmp_path = Path(self.tmpdir.name)

        # Create mock core reference schema
        self.schema_file = self.tmp_path / "reference.json"
        self.schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "citation_key": {"type": "string"},
                "ledger_source_id": {"type": "string"},
                "ledger_claim_id": {"type": "string"},
                "paper_section_target": {"type": "string"},
                "readiness_state": {"type": "string"}
            },
            "required": ["citation_key", "ledger_source_id", "readiness_state"],
            "additionalProperties": False
        }
        with open(self.schema_file, "w", encoding="utf-8") as f:
            json.dump(self.schema_data, f, indent=2)

        # Create mock references.json
        self.refs_file = self.tmp_path / "references.json"
        self.refs_data = [
            {
                "citation_key": "source-test-2026",
                "ledger_source_id": "source-test-source",
                "ledger_claim_id": "claim-test-claim",
                "paper_section_target": "sections/test.md",
                "readiness_state": "ready_for_bibliography"
            }
        ]
        with open(self.refs_file, "w", encoding="utf-8") as f:
            json.dump(self.refs_data, f, indent=2)

        # Create mock taxonomy directory
        self.tax_dir = self.tmp_path / "taxonomy_repo"
        self.tax_glossary_dir = self.tax_dir / "taxonomy"
        self.tax_glossary_dir.mkdir(parents=True, exist_ok=True)
        self.tax_glossary = self.tax_glossary_dir / "glossary.md"
        self.tax_glossary.write_text(
            "| Term | Layer | State | Claim ID | Source ID | Definition |\n"
            "|---|---|---|---|---|---|\n"
            "| test_term | Model Layer | `ready` | claim-test-claim | source-test-source | test |\n",
            encoding="utf-8"
        )

        # Create mock decision matrix directory
        self.mat_dir = self.tmp_path / "matrix_repo"
        self.mat_matrix_dir = self.mat_dir / "matrix"
        self.mat_matrix_dir.mkdir(parents=True, exist_ok=True)
        self.mat_file = self.mat_matrix_dir / "matrix_test.md"
        self.mat_file.write_text(
            "| Criterion Item | Taxonomy Term | Readiness State | Claim ID | Source ID | Evidence Gap |\n"
            "|---|---|---|---|---|---|\n"
            "| test_criterion | test_term | `ready` | claim-test-claim | source-test-source | None |\n",
            encoding="utf-8"
        )

        # Create mock research ledger directory
        self.ledger_dir = self.tmp_path / "ledger_repo"
        self.ledger_sources_dir = self.ledger_dir / "sources"
        self.ledger_sources_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_claims_dir = self.ledger_dir / "claims"
        self.ledger_claims_dir.mkdir(parents=True, exist_ok=True)

        # Create the actual source and claim files
        (self.ledger_sources_dir / "source-test-source.md").write_text("source details", encoding="utf-8")
        (self.ledger_claims_dir / "claim-test-claim.md").write_text("claim details", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_validation_script_success(self) -> None:
        script_path = ROOT / "scripts" / "validate_references.py"
        res = subprocess.run([
            sys.executable,
            str(script_path),
            "--references", str(self.refs_file),
            "--schema", str(self.schema_file),
            "--taxonomy-dir", str(self.tax_dir),
            "--matrix-dir", str(self.mat_dir),
            "--ledger-dir", str(self.ledger_dir)
        ], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"References validation failed: {res.stderr}\n{res.stdout}")
        self.assertIn("Local references validation successful", res.stdout)

    def test_validation_script_schema_failure(self) -> None:
        # Cause schema failure by removing required ledger_source_id
        invalid_refs = [{"citation_key": "source-test-2026", "readiness_state": "ready"}]
        with open(self.refs_file, "w", encoding="utf-8") as f:
            json.dump(invalid_refs, f, indent=2)

        script_path = ROOT / "scripts" / "validate_references.py"
        res = subprocess.run([
            sys.executable,
            str(script_path),
            "--references", str(self.refs_file),
            "--schema", str(self.schema_file),
            "--taxonomy-dir", str(self.tax_dir),
            "--matrix-dir", str(self.mat_dir),
            "--ledger-dir", str(self.ledger_dir)
        ], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Reference validation error", res.stderr)

    def test_validation_script_missing_source_warning(self) -> None:
        # Remove the source file to trigger cross-repo citation warning
        os.remove(self.ledger_sources_dir / "source-test-source.md")

        script_path = ROOT / "scripts" / "validate_references.py"
        res = subprocess.run([
            sys.executable,
            str(script_path),
            "--references", str(self.refs_file),
            "--schema", str(self.schema_file),
            "--taxonomy-dir", str(self.tax_dir),
            "--matrix-dir", str(self.mat_dir),
            "--ledger-dir", str(self.ledger_dir)
        ], capture_output=True, text=True)
        # Should still exit 0 (since it is a warning for cross-repo matching) but print warning in stderr
        self.assertEqual(res.returncode, 0)
        self.assertIn("Referenced source 'source-test-source' does not exist in ledger repository", res.stderr)

if __name__ == "__main__":
    unittest.main()
