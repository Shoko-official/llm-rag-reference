from __future__ import annotations

import ast
import hashlib
from pathlib import Path

def estimate_tokens(text: str) -> int:
    # A simple token estimator: words + punctuation approximation
    return len(text.split()) + (len(text) - len(text.replace(" ", ""))) // 2

class ASTChunker:
    def __init__(self, filepath: str, source_code: str):
        self.filepath = filepath
        self.source_code = source_code
        self.lines = source_code.splitlines()

    def get_node_source(self, start_line: int, end_line: int) -> str:
        # 1-based indexing for lines
        segment = self.lines[start_line - 1 : end_line]
        return "\n".join(segment)

    def generate_chunk_id(self, node_type: str, name: str, start_line: int) -> str:
        # Create a stable, unique ID
        norm_path = self.filepath.replace("\\", "/")
        raw_id = f"{norm_path}:{node_type}:{name}:{start_line}"
        sha = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:8]
        return f"chunk_{sha}_{name}"

    def chunk(self) -> list[dict]:
        try:
            tree = ast.parse(self.source_code)
        except SyntaxError:
            # Fallback to whole file as a module chunk if parsing fails
            return [self.make_fallback_chunk()]

        chunks = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node_type = "function"
                name = node.name
            elif isinstance(node, ast.ClassDef):
                node_type = "class"
                name = node.name
            else:
                continue

            # Ensure lineno attributes are present
            start_line = getattr(node, "lineno", None)
            end_line = getattr(node, "end_lineno", None)
            if start_line is None or end_line is None:
                continue

            content = self.get_node_source(start_line, end_line)
            chunk_id = self.generate_chunk_id(node_type, name, start_line)
            tokens = estimate_tokens(content)

            chunks.append({
                "id": chunk_id,
                "filepath": self.filepath,
                "type": node_type,
                "name": name,
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
                "tokens": tokens
            })

        if not chunks:
            # If no functions or classes, return the whole file
            return [self.make_fallback_chunk()]

        return chunks

    def make_fallback_chunk(self) -> dict:
        tokens = estimate_tokens(self.source_code)
        norm_path = self.filepath.replace("\\", "/")
        sha = hashlib.sha256(f"{norm_path}:module".encode("utf-8")).hexdigest()[:8]
        return {
            "id": f"chunk_{sha}_module",
            "filepath": self.filepath,
            "type": "module",
            "name": Path(self.filepath).name,
            "start_line": 1,
            "end_line": len(self.lines) if self.lines else 1,
            "content": self.source_code,
            "tokens": tokens
        }
