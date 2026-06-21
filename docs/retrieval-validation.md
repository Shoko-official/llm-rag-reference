# RAG Retrieval Validation Guidelines

This document details the validation strategies and metrics used to verify retrieval accuracy and data integrity in the LLM RAG Reference pipeline.

## Overview of Validation Pipelines

We maintain two primary validation layers:
1. **Retrieval Alignment Verification** (`scripts/validate_alignment.py`): Ensures the RAG index chunks exactly match the current state of source code files in the repository.
2. **Retrieval Accuracy Evaluation** (`scripts/validate_retrieval.py`): Performs automated querying of the hybrid search + reranking engine to measure standard retrieval metrics.

---

## 1. Alignment Verification

The alignment verification checks:
* **Orphan Detection**: Every file referenced in the index exists in the codebase.
* **Content Desynchronization**: Compares the cached chunk code snippet (`content`) against the current file lines at `[start_line : end_line]` after normalizing whitespaces and line endings.
* **Boundary Validation**: Checks that line ranges are valid within the size of the referenced source file.

To run manually:
```bash
python scripts/validate_alignment.py --index rag/index.json
```

---

## 2. Accuracy Evaluation

The accuracy validation utilizes a set of semantic and structural test queries to assess performance. 

### Metrics Calculated

* **Recall@K**: The percentage of test queries for which the expected relevant chunk is retrieved within the top `K` results.
  \[
  \text{Recall@K} = \frac{1}{|Q|} \sum_{q \in Q} \mathbb{I}(\text{rank}_q \le K)
  \]
* **Mean Reciprocal Rank (MRR)**: Measures where the first relevant chunk appears in the search results list.
  \[
  \text{MRR} = \frac{1}{|Q|} \sum_{q \in Q} \frac{1}{\text{rank}_q}
  \]
  If a chunk is not retrieved in the top results, its reciprocal rank is $0$.

### Thresholds
Our CI pipeline enforces the following minimum standards (configured via command-line arguments):
* **Recall@5**: $\ge 0.80$
* **MRR**: $\ge 0.70$

To run accuracy tests manually:
```bash
python scripts/validate_retrieval.py --index rag/index.json --k 5 --min-mrr 0.7 --min-recall 0.8
```

---

## 3. Automated Check Execution (Cron)

We execute these checks periodically via GitHub Actions defined in `.github/workflows/cron_index_validation.yml`. 
* **Frequency**: Triggered weekly (Sundays at midnight).
* **Scope**: Validates schema conformity, content alignment, and retrieval metrics.
