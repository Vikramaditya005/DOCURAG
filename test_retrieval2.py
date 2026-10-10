import os
import sys
import django

sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from docurag.pipeline import get_engine
from docurag.retrieve.hybrid import retrieve_for_documents
from api.models import Document

docs = Document.objects.all()
if docs:
    doc_id = str(docs[0].id)
    print(f"Testing ask with doc_id: {doc_id}")
    
    engine = get_engine()
    
    store = getattr(engine, 'store', None) or engine['store']
    embedder = getattr(engine, 'embedder', None) or engine['embedder']
    reranker = getattr(engine, 'reranker', None)
    
    evidence = retrieve_for_documents(
        query="what is INFOSYS",
        document_ids=[doc_id],
        store=store,
        embedder=embedder,
        reranker=reranker
    )
    
    print(f"Chunks retrieved: {len(evidence)}")
else:
    print("No documents found in DB.")
