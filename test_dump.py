import sys, os, django
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from docurag.pipeline import get_engine
from docurag.retrieve.hybrid import retrieve_for_documents

engine = get_engine()
store = getattr(engine, 'store', None) or engine['store']
embedder = getattr(engine, 'embedder', None) or engine['embedder']
reranker = getattr(engine, 'reranker', None)

evidence = retrieve_for_documents(
    query="test",
    document_ids=["1"],
    store=store,
    embedder=embedder,
    reranker=reranker,
    final_k=1
)

for e in evidence:
    dumped = e.model_dump() if hasattr(e, 'model_dump') else e
    print(dumped.keys() if isinstance(dumped, dict) else dumped)
    import json
    print(json.dumps(dumped, default=str))
