# RAG Retrieval Observability and Telemetry

This document outlines the distributed tracing and span instrumentation configured in the RAG retrieval pipeline.

## Instrumentation Overview

The RAG retrieval pipeline is instrumented with distributed tracing to measure latency, track performance characteristics, and debug query pipeline execution. All emitted spans conform to the core `span.json` schema.

The RAG search operations are categorized under the `rag` service name.

## Tracing Spans

### 1. `hybrid_search`

This span traces the execution of the initial hybrid search stage, which combines results from sparse BM25 and dense character N-gram searches.

- **Name**: `hybrid_search`
- **Service Name**: `rag`
- **Attributes**:
  - `query`: The text query executed.
  - `k`: Top-K threshold retrieved from sparse/dense search.
  - `alpha`: Dense vs sparse fusion weight.
  - `method`: Hybrid fusion method used (e.g. `linear`, `rrf`).

### 2. `rerank_chunks`

This span traces the subsequent reranking phase where retrieved document chunks are boosted and resorted based on name/type matching.

- **Name**: `rerank_chunks`
- **Service Name**: `rag`
- **Parent Span ID**: Linked to the preceding `hybrid_search` span ID (context propagation).
- **Attributes**:
  - `query`: The text query used for semantic boost.
  - `k`: Final top-K results returned.
  - `input_chunks_count`: The number of chunks fed into the reranker.

## Validation

Tracing outputs are stored in `rag/traces.json` and validated by `scripts/validate_rag.py` against the core telemetry schema definition in `llm-systems-core`.
