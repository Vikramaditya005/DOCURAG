# 📘 DocuRAG User & Deployment Guide

DocuRAG is a production-grade Multimodal RAG engine. This guide covers installation, data ingestion, and system verification.

---

## 🛠️ 1. Installation & Setup

### Prerequisites
- **Python**: 3.10+
- **API Key**: A Google Gemini API Key

### Step-by-Step Setup
1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   GEMINI_MODEL=gemini-1.5-flash
   DOCURAG_STORAGE=./storage
   ```

3. **Initialize Storage**
   Ensure the storage directories exist:
   ```bash
   mkdir -p storage/index storage/pages storage/figs storage/cache
   ```

---

## 📥 2. Data Ingestion

Before querying, you must index your documents.

### Method A: Bulk CLI Ingestion (Recommended for Setup)
Use the provided script to index all documents in your raw data folder:
```bash
python scripts/ingest_dir.py data/raw/
```
*This process performs multimodal extraction, layout-aware chunking, and hybrid indexing (FAISS + BM25).*

### Method B: Web UI Ingestion
1. Start the server (see Section 3).
2. Navigate to the **Library Page** (`/`).
3. Drag and drop your PDFs or Images.
4. Watch the status badge change from `Processing` $\rightarrow$ `Ready`.

---

## 🌐 3. Launching the Application

### Running the Django Web Interface
```bash
cd backend
python manage.py migrate
python manage.py runserver
```
- **URL**: `http://127.0.0.1:8000`
- **Library**: `/` (Manage documents)
- **Ask**: `/ask/` (Query the AI)
- **History**: `/history/` (Review past queries)

---

## 🧪 4. Testing & Verification

### Test 1: The "Smoke" Test (Core Pipeline)
Verify the engine is working without the UI:
```bash
python -m docurag.pipeline "What is the main purpose of DocuRAG?"
```
**Expected Result**: A JSON response containing a grounded answer, a "High" confidence label, and at least one source citation.

### Test 2: Multimodal Verification
Upload a document containing a **Table** or **Chart**. Ask a specific numeric question:
- *Example*: "What was the revenue in Q3 according to the bar chart?"
- **Check**: Ensure the system returns a `content_type: "image"` or `"table"` chunk and that the answer is numerically accurate.

### Test 3: The "Refusal" Test (Anti-Hallucination)
Ask a question completely unrelated to your uploaded documents.
- **Expected Result**: `answerable: false` and a "Low" confidence score.

---

## 📈 5. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `FileNotFoundError` | Missing storage dirs | Run `mkdir -p storage/{index,pages,figs,cache}` |
| `API Key Error` | `.env` not loaded | Check that `.env` is in the root and key is correct |
| `Memory Error` | Large PDFs | Use the `S_S` (Small-Small) embedder config in `config.py` |
| `JSON Decode Error` | Gemini output glitch | The system automatically retries once; check logs for details |
