import json, collections, inspect, os
import docurag.pipeline as p

print("== chunks.jsonl on disk ==")
counts = collections.Counter()
with open("storage/index/chunks.jsonl", encoding="utf-8") as f:
    for line in f:
        counts[str(json.loads(line).get("document_id"))] += 1
print(dict(counts))
print("metadata.json:", open("storage/index/metadata.json", encoding="utf-8").read()[:600])
for name in os.listdir("storage/index"):
    path = os.path.join("storage/index", name)
    print(name, os.path.getsize(path), "bytes")

print("\n== docurag.pipeline functions ==")
for name, fn in inspect.getmembers(p, inspect.isfunction):
    if fn.__module__ == p.__name__:
        print(name, inspect.signature(fn))