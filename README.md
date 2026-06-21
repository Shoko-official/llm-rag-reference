# LLM RAG Reference

`llm-rag-reference` defines the RAG reference workspace for the
Modern LLM Systems 2026 / arXiv Report program.

This repository will organize retrieval-augmented generation pipelines, chunking, indexing, and vector store integrations.

It is not the research ledger, paper repository, evaluation harness, inference
benchmark, agent runtime, memory layer, or observability stack.

## Repository Role

This repository owns:

* RAG reference governance;
* RAG baseline implementation;
* AST-based chunking and hybrid search;
* RAG validation and CI once introduced;
* paper-facing RAG evaluation support when backed by approved evidence.

The central project board is:

* [Modern LLM Systems 2026 / arXiv Report](https://github.com/users/Shoko-official/projects/4)

## Current Scope

Milestone 0 is limited to governance.

Included:

* repository scope;
* roadmap;
* contribution rules;
* review rules.

Out of scope:

* RAG pipeline implementation;
* vector database setup;
* retrieval evaluation datasets;
* scientific claims;
* serving, agents, or memory implementation.

## Evidence Policy

Future RAG claims must reference approved research ledger material or stay
clearly marked as unresolved planning notes.

Unsupported claims must not be used as paper-ready RAG content.

## Figure Policy

Allowed source formats:

* Mermaid text diagrams for workflows, architecture maps, dependency graphs, and
  concept maps.
* Python-generated images for visualizations that are not practical in Mermaid.

Not allowed by default:

* web images;
* screenshots unless explicitly approved;
* hand-drawn images;
* Figma, Canva, or PowerPoint exports;
* manually authored complex SVGs;
* binary figures without clear source;
* orphan figures.

## License

This repository is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
