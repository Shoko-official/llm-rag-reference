import json
import sys
import unittest
from pathlib import Path
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parents[1]

class TestRAGSchemas(unittest.TestCase):
    def setUp(self) -> None:
        self.schemas_dir = ROOT / "rag" / "schemas"

        with open(self.schemas_dir / "index.json", "r", encoding="utf-8") as f:
            self.index_schema = json.load(f)

        with open(self.schemas_dir / "chunk.json", "r", encoding="utf-8") as f:
            self.chunk_schema = json.load(f)

    def test_valid_mock_index(self) -> None:
        mock_path = ROOT / "rag" / "mock_index.json"
        self.assertTrue(mock_path.is_file())
        with open(mock_path, "r", encoding="utf-8") as f:
            mock_data = json.load(f)
        validate(instance=mock_data, schema=self.index_schema)

    def test_invalid_index_missing_required(self) -> None:
        invalid_index = {
            "repository": "Shoko-official/llm-rag-reference",
            # commit missing
            "chunks": []
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_index, schema=self.index_schema)

    def test_invalid_index_extra_field(self) -> None:
        invalid_index = {
            "repository": "Shoko-official/llm-rag-reference",
            "commit": "ec2fa6a9d9c8de04ef6f24b00babb12ec1e23363",
            "chunks": [],
            "extra_field": "not allowed"
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_index, schema=self.index_schema)

    def test_valid_chunk(self) -> None:
        valid_chunk = {
            "id": "chunk_001",
            "filepath": "main.py",
            "type": "function",
            "content": "def test():\n    pass"
        }
        validate(instance=valid_chunk, schema=self.chunk_schema)

    def test_invalid_chunk_type(self) -> None:
        invalid_chunk = {
            "id": "chunk_001",
            "filepath": "main.py",
            "type": "unsupported_type",
            "content": "def test():\n    pass"
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_chunk, schema=self.chunk_schema)

if __name__ == "__main__":
    unittest.main()
