# RAG Reference Registration and Verification Guidelines

This document details the procedures for registering, formatting, and updating references in the LLM RAG Reference pipeline.

## Overview

References represent published literature or document sources used to justify and back up claims in the research ledger, which are subsequently integrated into the taxonomy, decision matrix, and final report.

To ensure consistency across the entire ecosystem, references must:
1. Comply with the shared reference schema defined in `llm-systems-core/schemas/reference.json`.
2. Align perfectly with the sources and claims registered in `llm-systems-research-ledger`.
3. Align with taxonomy terms (`llm-architecture-taxonomy`) and decision criteria (`llm-decision-matrix`).

---

## 1. Registering Reference Definitions

Local references are registered in [references.json](file:///f:/Code/AI_ML/Article/Arxiv/llm-rag-reference/rag/references.json) as a JSON array of reference objects.

### Formatting Requirements

Each reference entry must conform to the following fields:

* **`citation_key`**: A unique alphanumeric key identifying the reference (e.g. `source-attention-2017`).
* **`ledger_source_id`**: The matching source file name in the research ledger (e.g. `source-placeholder-alpha-method-2026`). If there is no ledger source associated yet, use `"N/A"`.
* **`ledger_claim_id`**: The matching claim file name in the research ledger (e.g. `claim-alpha-neutral-performance`). If there is no ledger claim associated yet, use `"N/A"`.
* **`paper_section_target`**: The relative markdown file target in the final paper repository (e.g. `sections/introduction.md`). If not yet assigned, use `"N/A"`.
* **`readiness_state`**: The status of the reference. Must be one of:
  * `ready_for_bibliography`
  * `missing_citation_detail`
  * `missing_evidence`
  * `blocked`
* **`missing_citation_detail`** *(optional)*: Explanation of any missing details.

### Example Reference Object:

```json
{
  "citation_key": "source-attention-2017",
  "ledger_source_id": "source-placeholder-alpha-method-2026",
  "ledger_claim_id": "claim-alpha-neutral-performance",
  "paper_section_target": "sections/introduction.md",
  "readiness_state": "ready_for_bibliography"
}
```

---

## 2. Cross-Repository Citation Alignments

Our automated validation tools match reference citations across the following directories:
* **Taxonomy Glossary**: `taxonomy/glossary.md`
* **Decision Matrix Criteria**: `matrix/*.md`

Every `Claim ID` and `Source ID` declared in these markdown tables must exist as an active record in `llm-systems-research-ledger/claims/` and `llm-systems-research-ledger/sources/` respectively.

---

## 3. Running Validation

To run reference and citation validations:

```bash
# Runs local references schema check and cross-repo checks
python scripts/validate_references.py
```
