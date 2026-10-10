import sys
import os
sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

from docurag.pipeline import get_engine
import docurag.config
print(docurag.config.get_settings(reload=True).DOCURAG_FAKES)
engine = get_engine()
store = engine["store"]
print("Vector Index Docs:", len(store.vector_index.doc_store.docs) if store.vector_index else 0)
print("BM25 Index Docs:", len(store.bm25_index.doc_store.docs) if store.bm25_index else 0)
