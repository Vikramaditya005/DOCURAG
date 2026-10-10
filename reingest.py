import os
import sys
import django

sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from api.models import Document
from docurag.pipeline import get_engine

engine = get_engine()
docs = Document.objects.all()

for doc in docs:
    file_path = doc.file.path
    if os.path.exists(file_path):
        print(f"Re-ingesting {doc.filename} with ID: {doc.id}")
        if hasattr(engine, 'store') and getattr(engine, 'store'):
            getattr(engine, 'store').remove_document(str(doc.id))
        
        from docurag.pipeline import ingest_file
        result = ingest_file(file_path, document_id=str(doc.id))
        
        doc.pages = result.get('pages')
        doc.chunk_counts = result.get('chunk_counts', {})
        doc.status = 'ready'
        doc.save()
        print("Done.")
    else:
        print(f"File {file_path} not found.")
