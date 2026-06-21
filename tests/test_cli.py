import json
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class TestChunkerCLI(unittest.TestCase):
    def test_cli_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create a mock python file in the temp directory
            code_file = tmp_path / "dummy.py"
            code_file.write_text("def test_func():\n    return 1\n", encoding="utf-8")
            
            output_file = tmp_path / "index.json"
            
            # Run chunk_repo.py via subprocess
            cli_path = ROOT / "scripts" / "chunk_repo.py"
            res = subprocess.run([
                sys.executable,
                str(cli_path),
                "--dir", str(tmp_path),
                "--repo", "test/repo",
                "--commit", "abc12345",
                "--output", str(output_file)
            ], capture_output=True, text=True)
            
            self.assertEqual(res.returncode, 0, f"CLI failed: {res.stderr}\n{res.stdout}")
            self.assertTrue(output_file.is_file())
            
            # Load index and validate it against the schema
            with open(output_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
                
            schema_path = ROOT / "rag" / "schemas" / "index.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
                
            validate(instance=index_data, schema=schema)
            self.assertEqual(index_data["repository"], "test/repo")
            self.assertEqual(index_data["commit"], "abc12345")
            self.assertEqual(len(index_data["chunks"]), 1)
            self.assertEqual(index_data["chunks"][0]["name"], "test_func")

if __name__ == "__main__":
    unittest.main()
