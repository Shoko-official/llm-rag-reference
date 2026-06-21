import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.chunker import ASTChunker

class TestASTChunker(unittest.TestCase):
    def test_chunker_basic(self) -> None:
        source = """class MyClass:
    def method(self):
        pass

def my_function():
    return 42
"""
        chunker = ASTChunker("test.py", source)
        chunks = chunker.chunk()
        
        # We expect chunks: class MyClass, method, and my_function.
        types = [c["type"] for c in chunks]
        names = [c["name"] for c in chunks]
        
        self.assertIn("class", types)
        self.assertIn("function", types)
        self.assertIn("MyClass", names)
        self.assertIn("method", names)
        self.assertIn("my_function", names)

        # Check fields
        for chunk in chunks:
            self.assertTrue(chunk["id"].startswith("chunk_"))
            self.assertEqual(chunk["filepath"], "test.py")
            self.assertTrue(chunk["tokens"] > 0)
            self.assertTrue(len(chunk["content"]) > 0)

    def test_chunker_syntax_error(self) -> None:
        source = """def invalid_syntax(
"""
        chunker = ASTChunker("invalid.py", source)
        chunks = chunker.chunk()
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["type"], "module")
        self.assertEqual(chunks[0]["name"], "invalid.py")

    def test_chunker_no_classes_functions(self) -> None:
        source = """a = 1
b = 2
"""
        chunker = ASTChunker("no_nodes.py", source)
        chunks = chunker.chunk()
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["type"], "module")
        self.assertEqual(chunks[0]["name"], "no_nodes.py")

if __name__ == "__main__":
    unittest.main()
