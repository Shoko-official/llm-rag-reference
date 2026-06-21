# Contributing

Work in this repository must stay small, reviewable, and tied to an issue.

## Branches

Use short branch names tied to the issue:

```text
docs/rag/<issue-id>-short-name
feat/rag/<issue-id>-short-name
fix/rag/<issue-id>-short-name
```

Do not work directly on `main`.

## Pull Requests

Each pull request must:

* link to an issue;
* stay small and focused;
* describe scope and out-of-scope work;
* list changed files;
* list validation commands and results;
* avoid unrelated refactors;
* avoid secrets and private data.

Use `Closes #<issue>` only when the pull request fully completes the issue.
Use `Refs #<issue>` or `Part of #<issue>` for partial work.

## Review Rules

Review should check:

* scope matches the linked issue;
* no RAG reference content appears before the right milestone;
* claims are evidence-backed or clearly marked unresolved;
* figures follow the project figure policy;
* validation commands pass.

## Evidence Rules

Do not introduce RAG reference claims as final content unless they are backed by
approved research ledger material.

Planning notes are allowed only when clearly marked as not paper-ready.

## Figure Rules

Figures must be either:

* Mermaid source files; or
* Python-generated images from an approved workflow.

Do not add external images, screenshots, hand-drawn diagrams, or binary figures
without a dedicated issue.

## Local Checks

After validation is introduced, run:

```bash
make validate
make lint
make test
```
