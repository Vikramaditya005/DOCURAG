import os
import sys
import django

sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from api.models import Document, Chunk

docs = Document.objects.all()
print(f"Total Documents: {docs.count()}")
for doc in docs:
    chunks = Chunk.objects.filter(document=doc).count()
    print(f" - {doc.filename}: {chunks} chunks (Status: {doc.status})")
