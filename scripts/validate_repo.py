from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "ROADMAP.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/rag_task.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/ci.yml",
    "docs/README.md",
    "figures/README.md",
    "rag/README.md",
    "rag/chunker.py",
    "rag/index.json",
    "rag/mock_index.json",
    "rag/schemas/chunk.json",
    "rag/schemas/index.json",
    "scripts/validate_repo.py",
    "scripts/validate_rag.py",
    "scripts/generate_mock_data.py",
    "scripts/chunk_repo.py",
    "tests/README.md",
    "tests/test_schemas.py",
    "tests/test_chunker.py",
    "tests/test_cli.py",
]

REQUIRED_DIRECTORIES = [
    ".github",
    ".github/ISSUE_TEMPLATE",
    ".github/workflows",
    "docs",
    "figures",
    "rag",
    "scripts",
    "tests",
]

SECRET_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"AKIA[0-9A-Z]{16}",
        r"gho_[A-Za-z0-9_]+",
        r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
        r"(?i)\b(password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
    ]
]

FOUNDATION_MARKERS = {
    "README.md": [
        "# LLM RAG Reference",
        "## Repository Role",
        "## Current Scope",
        "## Evidence Policy",
        "## Figure Policy",
    ],
    "ROADMAP.md": [
        "# Roadmap",
        "## Milestone 0: Project Governance",
        "## Acceptance Criteria",
        "## Later Milestones",
    ],
}


def fail(message: str) -> None:
    raise SystemExit(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def iter_text_files() -> list[Path]:
    excluded_parts = {".git", "__pycache__"}
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if excluded_parts.intersection(path.parts):
            continue
        if path.suffix.lower() in {".md", ".yml", ".yaml", ".py", ""}:
            files.append(path)
    return files


def validate_required_paths() -> None:
    missing_files = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    missing_dirs = [path for path in REQUIRED_DIRECTORIES if not (ROOT / path).is_dir()]
    if missing_files or missing_dirs:
        details = []
        if missing_files:
            details.append("missing files: " + ", ".join(missing_files))
        if missing_dirs:
            details.append("missing directories: " + ", ".join(missing_dirs))
        fail("; ".join(details))


def validate_foundation_markers() -> None:
    for relative_path, markers in FOUNDATION_MARKERS.items():
        text = read_text(ROOT / relative_path)
        missing_markers = [marker for marker in markers if marker not in text]
        if missing_markers:
            fail(
                f"{relative_path} is missing expected marker(s): "
                + ", ".join(missing_markers)
            )


def lint_text() -> None:
    for path in iter_text_files():
        text = read_text(path)
        relative = path.relative_to(ROOT)
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"possible secret in {relative}: {pattern.pattern}")


def run_validate() -> None:
    validate_required_paths()
    validate_foundation_markers()
    # Validate RAG index files
    import subprocess
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_rag.py")], capture_output=True, text=True)
    if res.returncode != 0:
        fail(f"RAG validation failed:\n{res.stderr}\n{res.stdout}")


def run_lint() -> None:
    lint_text()


def run_test() -> None:
    run_validate()
    run_lint()
    # Discover and run any tests under tests/
    import unittest
    suite = unittest.defaultTestLoader.discover(start_dir=str(ROOT / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        fail("Unit tests failed")


def main(argv: list[str]) -> int:
    if len(argv) == 1:
        command = "test"
    elif len(argv) == 2 and argv[1] in {"validate", "lint", "test"}:
        command = argv[1]
    else:
        print("usage: validate_repo.py {validate|lint|test}", file=sys.stderr)
        return 2

    if command == "validate":
        run_validate()
    elif command == "lint":
        run_lint()
    else:
        run_test()

    print(f"{command} ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
