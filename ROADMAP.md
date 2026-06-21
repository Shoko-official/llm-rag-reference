# Roadmap

This roadmap starts with governance only. RAG content starts after
Milestone 0 is complete and the repository has validation and CI.

## Milestone 0: Project Governance

Goal: establish a small, reviewable operating model for the RAG reference repository.

### Issues

1. [#1 Create RAG reference governance documentation](https://github.com/Shoko-official/llm-rag-reference/issues/1)
2. [#2 Add issue and PR templates](https://github.com/Shoko-official/llm-rag-reference/issues/2)
3. [#3 Add minimal validation, CI, and folder structure](https://github.com/Shoko-official/llm-rag-reference/issues/3)

### Execution Order

1. Complete issue #1 before templates or validation.
2. Complete issue #2 before content changes.
3. Complete issue #3 before RAG reference content.

No RAG reference content should be added during Milestone 0.

## Acceptance Criteria

Milestone 0 is complete when:

* repository role is documented;
* roadmap exists;
* contribution and review rules exist;
* issue and PR templates exist;
* minimal validation commands exist;
* minimal CI exists;
* initial folders exist;
* no RAG reference content has been added.

## Later Milestones

Expected sequence:

1. Define a minimal RAG index and chunking schema.
2. Implement AST-based chunking baseline.
3. Add hybrid search and reranker integration.
4. Implement retrieval validation checking.
5. Create validation for RAG reference files.
6. Connect RAG retrieval results to evaluation harness datasets.

Any change to RAG reference structure, chunking methods, or evidence rules must happen in a
dedicated issue.
