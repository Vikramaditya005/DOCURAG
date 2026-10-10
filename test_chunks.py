import os, sys, django
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from docurag.pipeline import get_engine
engine = get_engine()
store = getattr(engine, 'store', None) or engine['store']
print("Total Chunks in FAISS:", len(store.chunks))
print("Documents in map:", store.doc_map.keys())
if store.chunks:
    print("Sample Chunk doc_id:", store.chunks[0].document_id)
