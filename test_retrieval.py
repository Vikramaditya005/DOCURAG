import os
import sys
import django

sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from docurag.pipeline import ask
from api.models import Document

docs = Document.objects.all()
if docs:
    doc_id = str(docs[0].id)
    print(f"Testing ask with doc_id: {doc_id}")
    
    result = ask("what is INFOSYS", use_agents=False, document_ids=[doc_id])
    
    print("Answerable:", result.answerable)
    print("Answer:", result.answer)
else:
    print("No documents found in DB.")
