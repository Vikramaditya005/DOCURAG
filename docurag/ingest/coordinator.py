"""Format-agnostic ingestion coordinator for M1."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from docurag.ingest.pdf_loader import load_image, load_pdf
from docurag.ingest.text import load_docx, load_txt
from docurag.schemas import PageData, Chunk
from docurag.index.store import ChunkStore
from docurag.index.embedder import Embedder
from docurag.config import get_settings

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt", ".docx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

def generate_document_id(path: str | Path) -> str:
    """Generate a deterministic document ID from file content when available."""
    path_obj = Path(path)
    try:
        digest = hashlib.sha256(path_obj.read_bytes()).hexdigest()[:16]
    except Exception:
        digest = hashlib.sha256(str(path_obj).encode("utf-8")).hexdigest()[:16]
    stem = "".join(ch.lower() if ch.isalnum() else "_" for ch in path_obj.stem).strip("_") or "document"
    return f"doc_{stem}_{digest}"

def iter_document_pages(path: str | Path, document_id: Optional[str] = None) -> Iterable[PageData]:
    """Route a supported document to the appropriate page loader."""
    path_obj = Path(path)
    doc_id = document_id or generate_document_id(path_obj)
    suffix = path_obj.suffix.lower()
    if suffix == ".pdf":
        yield from load_pdf(path_obj, doc_id)
    elif suffix in IMAGE_EXTENSIONS:
        yield from load_image(path_obj, doc_id)
    elif suffix == ".txt":
        yield from load_txt(path_obj, doc_id)
    elif suffix == ".docx":
        yield from load_docx(path_obj, doc_id)
    else:
        raise ValueError(f"Unsupported document extension: {suffix}")

def document_to_chunks(pages: List[PageData], doc_id: str) -> List[Chunk]:
    """Convert page data into indexable chunks."""
    chunks = []
    for page in pages:
        # 1. Main text chunk
        if page.text.strip():
            chunks.append(Chunk(
                chunk_id=f"{doc_id}_p{page.page}_t",
                document_id=doc_id,
                source=f"page {page.page}",
                page=page.page,
                content_type="text",
                content=page.text,
                token_count=len(page.text) // 4 # rough estimate
            ))
        
        # 2. Table chunks
        for i, table in enumerate(page.tables_md):
            chunks.append(Chunk(
                chunk_id=f"{doc_id}_p{page.page}_tbl{i}",
                document_id=doc_id,
                source=f"page {page.page}",
                page=page.page,
                content_type="table",
                content=table,
                token_count=len(table) // 4
            ))
            
        # 3. Figure chunks
        for i, fig in enumerate(page.figures):
            content = f"Figure: {fig.caption}. Description: {fig.description or 'No description'}"
            chunks.append(Chunk(
                chunk_id=f"{doc_id}_p{page.page}_fig{i}",
                document_id=doc_id,
                source=f"page {page.page}",
                page=page.page,
                content_type="image",
                content=content,
                token_count=len(content) // 4
            ))
    return chunks

def ingest_document(path: str | Path, collection_id: str = "default", document_id: Optional[str] = None) -> Dict[str, object]:
    """Ingest a single document and return a lightweight report."""
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Document not found: {path_obj}")
    if path_obj.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported document extension: {path_obj.suffix}")

    if document_id is None:
        document_id = generate_document_id(path_obj)
    pages = list(iter_document_pages(path_obj, document_id=document_id))
    
    # ACTUAL INDEXING
    settings = get_settings()
    embedder = Embedder(model_name=settings.EMBED_MODEL)
    store = ChunkStore(embedder=embedder, persistence_path=settings.DOCURAG_STORAGE + "/index")
    store.load()

    chunks = document_to_chunks(pages, document_id)
    store.remove_document(document_id)
    store.add_document(document_id, chunks)
    store.save()

    chunks_estimate = len(chunks)
    return {
        "document_id": document_id,
        "filename": path_obj.name,
        "collection_id": collection_id,
        "status": "ready",
        "pages": len(pages),
        "chunks_indexed": chunks_estimate,
        "pages_data": pages,
    }

def _iter_supported_files(dir_path: Path, recursive: bool) -> Iterable[Path]:
    walker = dir_path.rglob("*") if recursive else dir_path.glob("*")
    for path in walker:
        if not path.is_file():
            continue
        if path.name.startswith(".") or path.name.startswith("~$"):
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path

def ingest_directory(
    dir_path: str | Path,
    collection_id: str = "default",
    recursive: bool = True,
) -> Dict[str, object]:
    """Ingest all supported files in a directory, continuing after per-file errors."""
    root = Path(dir_path)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    reports: List[Dict[str, object]] = []
    errors: List[Dict[str, str]] = []
    for file_path in _iter_supported_files(root, recursive=recursive):
        try:
            reports.append(ingest_document(file_path, collection_id=collection_id))
        except Exception as exc:
            logger.warning("Failed to ingest %s: %s", file_path, exc)
            errors.append({"file": str(file_path), "error": str(exc)})

    total_chunks = sum(int(report.get("chunks_indexed", 0)) for report in reports)
    status = "empty" if not reports and not errors else "ready"
    return {
        "collection_id": collection_id,
        "directory": str(root),
        "files_ingested": len(reports),
        "total_chunks": total_chunks,
        "status": status,
        "documents": reports,
        "errors": errors,
    }
