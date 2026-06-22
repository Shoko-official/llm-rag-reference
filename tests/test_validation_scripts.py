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

class TestValidationScripts(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory(dir=str(ROOT))
        self.tmp_path = Path(self.tmpdir.name)

        # Create a mock file referenced in alignment
        self.src_file = self.tmp_path / "mock_module.py"
        self.src_content = "def hello_world():\n    print('hello')\n    return 42\n"
        self.src_file.write_text(self.src_content, encoding="utf-8")

        # Create mock index matching file perfectly
        self.mock_index = {
            "repository": "test/repo",
            "commit": "testcommit",
            "chunks": [
                {
                    "id": "chunk_hello",
                    "filepath": str(self.src_file.relative_to(ROOT)).replace("\\", "/"),
                    "type": "function",
                    "name": "hello_world",
                    "start_line": 1,
                    "end_line": 3,
                    "content": self.src_content,
                    "tokens": 15
                }
            ]
        }
        self.index_file = self.tmp_path / "index.json"
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.mock_index, f, indent=2)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_validate_alignment_success(self) -> None:
        # Check alignment succeeds
        align_script = ROOT / "scripts" / "validate_alignment.py"
        res = subprocess.run([
            sys.executable,
            str(align_script),
            "--index", str(self.index_file)
        ], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Alignment failed: {res.stderr}\n{res.stdout}")
        self.assertIn("perfectly aligned", res.stdout)

    def test_validate_alignment_failure_missing_file(self) -> None:
        # Delete source file and check it fails
        os.remove(self.src_file)
        align_script = ROOT / "scripts" / "validate_alignment.py"
        res = subprocess.run([
            sys.executable,
            str(align_script),
            "--index", str(self.index_file)
        ], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("refers to non-existent file", res.stderr)

    def test_validate_alignment_failure_desync(self) -> None:
        # Modify source file content to cause misalignment
        self.src_file.write_text("def hello_world():\n    print('bye')\n    return 0\n", encoding="utf-8")
        align_script = ROOT / "scripts" / "validate_alignment.py"
        res = subprocess.run([
            sys.executable,
            str(align_script),
            "--index", str(self.index_file)
        ], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("out of sync", res.stderr)

    def test_validate_retrieval_runs(self) -> None:
        # Retrieval validation requires a real index that matches evaluation queries
        # Let's run it against the main index or mock_index
        retrieval_script = ROOT / "scripts" / "validate_retrieval.py"
        
        # Test runs on repository index
        res = subprocess.run([
            sys.executable,
            str(retrieval_script),
            "--min-mrr", "0.0",
            "--min-recall", "0.0"
        ], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Retrieval script failed: {res.stderr}\n{res.stdout}")
        self.assertIn("Evaluation Results", res.stdout)

if __name__ == "__main__":
    unittest.main()
