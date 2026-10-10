# DocuRAG Project Progress

## Milestones Summary

| Milestone | Status | Description | Notes |
|---|---|---|---|
| **M0** | **IN PROGRESS / VERIFYING** | Scaffolding, Schemas, Cache, Timing, Hermetic Fakes, Façade | Lead/Scaffold Worker (worker_m0_1) |
| **M1** | PLANNED | PDF & Image Ingestion, OCR, Vision | Blocked on M0 contract freeze |
| **M2** | PLANNED | Chunking & Table Preservation | Blocked on M1 |
| **M3** | PLANNED | Indexing & Embedding Engine | Blocked on M2 |
| **M4** | PLANNED | Hybrid Retrieval & Reranker | Blocked on M3 |
| **M5** | PLANNED | Grounded Generation, Citations & Verifier | Blocked on M4 |
| **CP1** | PLANNED | Checkpoint 1 Core Linear Pipeline Verify | Blocked on M5 |
| **M6** | PLANNED | CLI & Ingestion Tooling | Blocked on CP1 |
| **M7** | PLANNED | Django Web Application & UI | Blocked on CP1 |
| **M8** | PLANNED | Multi-Agent Runtime & FastMCP Servers | Blocked on CP1 |
| **M9** | PLANNED | Evaluation Harness & Benchmark Suite | Blocked on M7/M8 |

---

## Action Items Required from Human Owner
1. **API Keys**: Provide `GEMINI_API_KEY` in `.env` for live LLM generation and vision OCR fallbacks.
2. **Documents**: Provide evaluation PDFs in `data/raw/` for real domain ingestion benchmarking.
