from __future__ import annotations

import json
import math
import re
import uuid
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path

def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())

def get_char_ngrams(text: str, n: int = 3) -> Counter:
    text = text.lower()
    # strip whitespace/newlines to avoid matching layout
    text = "".join(text.split())
    ngrams = [text[i:i+n] for i in range(len(text) - n + 1)]
    return Counter(ngrams)

def cosine_similarity(c1: Counter, c2: Counter) -> float:
    intersection = set(c1.keys()) & set(c2.keys())
    numerator = sum(c1[x] * c2[x] for x in intersection)
    sum1 = sum(c1[x]**2 for x in c1.keys())
    sum2 = sum(c2[x]**2 for x in c2.keys())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return numerator / denominator

class HybridSearcher:
    def __init__(self, index_data: dict | str | Path):
        if isinstance(index_data, (str, Path)):
            with open(index_data, "r", encoding="utf-8") as f:
                self.index_data = json.load(f)
        else:
            self.index_data = index_data
        
        self.chunks = self.index_data.get("chunks", [])
        self.N = len(self.chunks)
        self._prepare_sparse()
        self._prepare_dense()
        self.last_spans: list[dict] = []
        self.current_trace_id: str | None = None

    def reset_trace(self) -> None:
        self.current_trace_id = None
        self.last_spans = []

    def _prepare_sparse(self) -> None:
        self.df = Counter()
        self.chunk_tfs = []
        
        for chunk in self.chunks:
            content = chunk.get("content", "")
            tokens = tokenize(content)
            token_counts = Counter(tokens)
            
            total_tokens = len(tokens)
            tf = {}
            for token, count in token_counts.items():
                tf[token] = count / total_tokens if total_tokens > 0 else 0.0
                self.df[token] += 1
            self.chunk_tfs.append(tf)
            
        self.idf = {}
        for token, df_val in self.df.items():
            self.idf[token] = math.log(1.0 + self.N / df_val)

    def _prepare_dense(self) -> None:
        self.chunk_ngrams = []
        for chunk in self.chunks:
            content = chunk.get("content", "")
            self.chunk_ngrams.append(get_char_ngrams(content))

    def sparse_search(self, query: str, k: int = 5) -> list[dict]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return [{**chunk, "score": 0.0} for chunk in self.chunks[:k]]
            
        scored_chunks = []
        for idx, chunk in enumerate(self.chunks):
            tf = self.chunk_tfs[idx]
            score = sum(tf.get(token, 0.0) * self.idf.get(token, 0.0) for token in query_tokens)
            scored_chunks.append((score, chunk))
            
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored_chunks[:k]:
            results.append({**chunk, "score": score})
        return results

    def dense_search(self, query: str, k: int = 5) -> list[dict]:
        query_ngrams = get_char_ngrams(query)
        if not query_ngrams:
            return [{**chunk, "score": 0.0} for chunk in self.chunks[:k]]
            
        scored_chunks = []
        for idx, chunk in enumerate(self.chunks):
            chunk_ng = self.chunk_ngrams[idx]
            score = cosine_similarity(query_ngrams, chunk_ng)
            scored_chunks.append((score, chunk))
            
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored_chunks[:k]:
            results.append({**chunk, "score": score})
        return results

    def hybrid_search(self, query: str, k: int = 5, alpha: float = 0.5, method: str = "linear") -> list[dict]:
        start_time = datetime.now(timezone.utc)
        if self.current_trace_id is None:
            self.current_trace_id = uuid.uuid4().hex
            
        if not self.chunks:
            return []
            
        if method == "linear":
            sparse_res = self.sparse_search(query, k=len(self.chunks))
            dense_res = self.dense_search(query, k=len(self.chunks))
            
            sparse_scores = {r["id"]: r["score"] for r in sparse_res}
            dense_scores = {r["id"]: r["score"] for r in dense_res}
            
            s_min = min(sparse_scores.values()) if sparse_scores else 0.0
            s_max = max(sparse_scores.values()) if sparse_scores else 0.0
            d_min = min(dense_scores.values()) if dense_scores else 0.0
            d_max = max(dense_scores.values()) if dense_scores else 0.0
            
            def norm(val, v_min, v_max):
                if v_max > v_min:
                    return (val - v_min) / (v_max - v_min)
                return 0.0
                
            combined = []
            for chunk in self.chunks:
                c_id = chunk["id"]
                s_score = norm(sparse_scores.get(c_id, 0.0), s_min, s_max)
                d_score = norm(dense_scores.get(c_id, 0.0), d_min, d_max)
                score = alpha * s_score + (1.0 - alpha) * d_score
                combined.append((score, chunk))
        elif method == "rrf":
            sparse_res = self.sparse_search(query, k=len(self.chunks))
            dense_res = self.dense_search(query, k=len(self.chunks))
            
            sparse_ranks = {r["id"]: i + 1 for i, r in enumerate(sparse_res)}
            dense_ranks = {r["id"]: i + 1 for i, r in enumerate(dense_res)}
            
            combined = []
            constant = 60.0
            for chunk in self.chunks:
                c_id = chunk["id"]
                s_rank = sparse_ranks.get(c_id)
                d_rank = dense_ranks.get(c_id)
                
                s_rrf = 1.0 / (constant + s_rank) if s_rank is not None else 0.0
                d_rrf = 1.0 / (constant + d_rank) if d_rank is not None else 0.0
                score = s_rrf + d_rrf
                combined.append((score, chunk))
        else:
            raise ValueError(f"Unknown fusion method: {method}")
            
        combined.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in combined[:k]:
            results.append({**chunk, "score": score})
            
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000.0
        span = {
            "span_id": uuid.uuid4().hex[:16],
            "trace_id": self.current_trace_id,
            "parent_span_id": "N/A",
            "name": "hybrid_search",
            "start_time": start_time.isoformat().replace("+00:00", "Z"),
            "end_time": end_time.isoformat().replace("+00:00", "Z"),
            "duration_ms": round(duration_ms, 4),
            "service_name": "rag",
            "status": "ok",
            "attributes": {
                "query": query,
                "k": k,
                "alpha": alpha,
                "method": method
            }
        }
        self.last_spans.append(span)
        return results

    def rerank(
        self,
        query: str,
        chunks: list[dict],
        k: int = 5,
        name_boost: float = 0.2,
        type_boosts: dict[str, float] | None = None
    ) -> list[dict]:
        start_time = datetime.now(timezone.utc)
        if self.current_trace_id is None:
            self.current_trace_id = uuid.uuid4().hex
            
        if type_boosts is None:
            type_boosts = {"class": 0.1, "function": 0.05}
            
        query_tokens = tokenize(query)
        boosted_chunks = []
        
        for chunk in chunks:
            base_score = chunk.get("score", 0.0)
            boost = 0.0
            
            chunk_name = chunk.get("name", "")
            if chunk_name:
                chunk_name_lower = chunk_name.lower()
                for token in query_tokens:
                    if len(token) >= 3 and token == chunk_name_lower:
                        boost += name_boost
                        break
                        
            chunk_type = chunk.get("type", "")
            boost += type_boosts.get(chunk_type, 0.0)
            
            new_score = base_score + boost
            boosted_chunks.append({**chunk, "score": new_score})
            
        boosted_chunks.sort(key=lambda x: x["score"], reverse=True)
        
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000.0
        
        parent_id = "N/A"
        if self.last_spans:
            for span in reversed(self.last_spans):
                if span["trace_id"] == self.current_trace_id and span["name"] == "hybrid_search":
                    parent_id = span["span_id"]
                    break
                    
        span = {
            "span_id": uuid.uuid4().hex[:16],
            "trace_id": self.current_trace_id,
            "parent_span_id": parent_id,
            "name": "rerank_chunks",
            "start_time": start_time.isoformat().replace("+00:00", "Z"),
            "end_time": end_time.isoformat().replace("+00:00", "Z"),
            "duration_ms": round(duration_ms, 4),
            "service_name": "rag",
            "status": "ok",
            "attributes": {
                "query": query,
                "k": k,
                "input_chunks_count": len(chunks)
            }
        }
        self.last_spans.append(span)
        return boosted_chunks[:k]
