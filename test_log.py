import sys, os, django
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from api.models import QueryLog

log = QueryLog.objects.last()
print(f"Sources type: {type(log.sources)}")
print(f"Sources length: {len(log.sources) if log.sources else 0}")
if log.sources:
    print(f"First source type: {type(log.sources[0])}")
    print(f"First source keys: {log.sources[0].keys() if isinstance(log.sources[0], dict) else log.sources[0]}")
