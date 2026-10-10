import os, sys, django

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)                          # for `docurag` and `backend.*`
sys.path.insert(0, os.path.join(ROOT, "backend")) # for `api` (as listed in INSTALLED_APPS)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
django.setup()

from api.models import Document

print("Django documents:")
for d in Document.objects.all():
    print({k: v for k, v in d.__dict__.items() if not k.startswith("_")})

from docurag.pipeline import get_engine
store = get_engine()["store"]
print("\nstore path:", store.persistence_path)
print("store doc ids:", list(store.doc_map.keys()))