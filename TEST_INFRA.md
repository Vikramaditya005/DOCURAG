# DocuRAG Test Infrastructure (`TEST_INFRA.md`)

## 1. Overview & Testing Philosophy

DocuRAG employs a **Dual-Track Testing Architecture** separating opaque-box end-to-end (E2E) verification (Track A) from internal unit milestone implementations (Track B).

```
                      ┌──────────────────────────────────────────┐
                      │        Frozen Public Contracts          │
                      │             (CONTRACTS.md)               │
                      └────────────────────┬─────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
       ┌────────────────────────┐                    ┌────────────────────────┐
       │   Track A: E2E Tests   │                    │ Track B: Unit / M0-M9  │
       │     (`tests/e2e/`)     │                    │       (`tests/`)       │
       │  - Opaque-box contracts│                    │  - Module components   │
       │  - Zero private access │                    │  - Algorithm specifics │
       │  - User-facing entry   │                    │  - Class internals     │
       └────────────┬───────────┘                    └────────────┬───────────┘
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           ▼
                      ┌──────────────────────────────────────────┐
                      │ Hermetic Test Engine (`DOCURAG_FAKES=1`) │
                      │  - Deterministic FakeEmbedder (384-dim)  │
                      │  - Deterministic FakeReranker (Jaccard)  │
                      │  - Deterministic FakeLLM (Structured)    │
                      │  - Pure Python Synthetic Byte Fixtures   │
                      │  - Execution time: < 60s on CPU          │
                      └──────────────────────────────────────────┘
```

### Core Principles
1. **Opaque-Box Verification**: E2E tests interact exclusively with public facades defined in `CONTRACTS.md` (`docurag.pipeline.ask`, `_ask_linear`, `ingest_file`, `ingest_directory`, and Pydantic response models). Tests make zero assumptions about internal helper classes or implementation private methods.
2. **Hermetic & Deterministic Isolation**: Under `$env:DOCURAG_FAKES="1"`, test execution requires **zero GPU hardware**, **zero external network access**, and **zero proprietary API keys** (e.g. Gemini). All embeddings, reranking scores, and LLM text generation operate via deterministic CPU fakes.
3. **Progressive Testability**: Tests validate contracts incrementally. They verify structural conformance, invariants, and fallback guarantees regardless of whether the backend engine is running on lightweight hermetic fakes or fully integrated neural models.
4. **Zero-Binary Repository Policy**: Test documents (PDFs, images, tables) are never committed as static binary blobs. They are synthesized in pure Python at test runtime using byte-level RFC/PDF generators.

---

## 2. Test Hierarchy (Tiers 1–4)

The E2E test suite resides under `tests/e2e/` and is partitioned into four distinct validation tiers:

| Tier | Test Module | Purpose | Scope & Entrypoints |
|---|---|---|---|
| **Tier 1** | `tests/e2e/test_tier1_features.py` | **Feature Coverage** | Core functional entrypoints (`ask()`, `_ask_linear()`, `ingest_file()`, `ingest_directory()`). Validates schema contracts, linear vs. agentic modes, source attribution, and timing metadata. |
| **Tier 2** | `tests/e2e/test_tier2_boundaries.py` | **Boundaries & Corner Cases** | Edge cases and adversarial inputs: empty queries, whitespace, single-word inputs, massive token sequences, corrupt PDF bytes, missing files, Unicode/emojis, and injection strings. |
| **Tier 3** | `tests/e2e/test_tier3_interactions.py` | **Cross-Feature Interactions** | Multi-step lifecycle workflows: file ingestion followed by query retrieval, multi-document ingestion, collection partitioning, agent mode switching, and verifier retry loops. |
| **Tier 4** | `tests/e2e/test_tier4_scenarios.py` | **Real-World Scenarios** | Complex end-to-end user workflows: financial table lookup, scientific document Q&A, multi-document comparative synthesis, and unanswerable query refusal with confidence capping. |

---

## 3. Synthetic Fixtures & Byte Generators

To guarantee portability across diverse execution environments (local CPU, CI runners, Google Colab), all test fixtures are generated programmatically:

### 3.1 Pure Python Minimal PDF Generator
`generate_minimal_pdf_bytes(text: str = ...) -> bytes`
- Assembles a fully valid PDF-1.4 file with `/Catalog`, `/Pages`, `/Page`, Helvetica `/Font`, `/Contents` stream, and xref table.
- Requires zero external C libraries or binaries.

### 3.2 Pure Python Minimal PNG Generator
`generate_minimal_png_bytes(width: int = 10, height: int = 10, rgb: tuple = ...) -> bytes`
- Synthesizes RFC 2083 compliant PNG files with standard 8-byte signature, `IHDR`, `IDAT` (via standard library `zlib.compress`), and `IEND` chunk.
- Calculates 32-bit CRC checksums natively.

### 3.3 Dynamic Test Corpus (`synthetic_corpus`)
Provides on-demand test files in `pytest` temporary directories (`tmp_path`):
- `text`: Structured PDF with section headers and prose paragraphs.
- `table`: PDF containing Markdown-formatted multi-column tabular data.
- `chart`: PDF with embedded synthetic PNG raster diagrams.
- `scanned`: Low-density (<50 characters) image-only PDF triggering OCR branches.
- `image`: Standalone PNG file for image-based document ingestion.

---

## 4. Hermetic Test Doubles (`DOCURAG_FAKES=1`)

When `$env:DOCURAG_FAKES="1"` (or `Settings.DOCURAG_FAKES=True`), the system activates hermetic test doubles:

| Double | Implementation Class | Behavioral Contract |
|---|---|---|
| **Embedder** | `FakeEmbedder` | Computes deterministic 384-dimensional unit vectors using SHA-256 projections. Normalized to $L_2 = 1.0$. Preserves 2D matrix shape `(0, 384)` on empty input batches. |
| **Reranker** | `FakeReranker` | Cross-encoder substitute calculating token Jaccard similarity between query and candidate text. Returns normalized floats in $[0.1, 1.0]$. |
| **LLM** | `FakeLLM` | Deterministic prompt classifier and structured JSON synthesizer. Responds to grounded QA prompts, figure descriptions, router intent classifications, and verifier claim checks. |

---

## 5. Execution Matrix & Commands

### Running E2E Test Tiers (PowerShell on Windows)
```powershell
# Set hermetic fake environment
$env:DOCURAG_FAKES="1"

# Run all E2E tiers with verbosity
pytest tests/e2e -v

# Run individual tiers
pytest tests/e2e/test_tier1_features.py -v
pytest tests/e2e/test_tier2_boundaries.py -v
pytest tests/e2e/test_tier3_interactions.py -v
pytest tests/e2e/test_tier4_scenarios.py -v

# Run with execution timing summary (<60s CPU target)
pytest tests/e2e --durations=10
```

### Running E2E Test Tiers (Bash on Linux/macOS)
```bash
DOCURAG_FAKES=1 pytest tests/e2e -v
```

---

## 6. Invariant & Contract Checklist

All tests enforce these invariants derived from `CONTRACTS.md`:
- [x] **Schema Roundtrip**: `AskResult` returned by public APIs serializes to JSON and deserializes back into identical Pydantic objects.
- [x] **Source Attribution**: For every evidence cited in `answer` (e.g. `[E1]`), there exists a matching `Source` and `Evidence` item with identical document attribution.
- [x] **Confidence Calibration**:
  - `score >= 0.75` maps to label `"High"`
  - `0.4 <= score < 0.75` maps to label `"Medium"`
  - `score < 0.4` maps to label `"Low"`
  - Unanswerable queries cap confidence at $\le 0.20$.
- [x] **Monotonic Timing**: `total_ms >= max(retrieval_ms, generation_ms, rerank_ms, verification_ms)` and all stage latencies $\ge 0$.
- [x] **Agent Trace Fidelity**: In agentic mode (`use_agents=True`), `agent_trace` contains ordered `TraceStep` records with non-empty `agent` and `action` fields. In linear mode (`use_agents=False`), agent trace is empty or contains linear stages.
- [x] **Fault Containment**: Corrupted document inputs, missing files, or empty queries do not crash the host process with unhandled exceptions.
