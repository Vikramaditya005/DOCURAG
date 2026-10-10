from docurag.pipeline import get_engine
import json, collections

engine = get_engine()
store = engine["store"]

print("Store Stats:", json.dumps(store.stats(), indent=2, default=str))
print("\ndoc_map:")
for k, v in store.doc_map.items():
    print(" ", repr(k), "->", v if not isinstance(v, (list, dict)) else f"{type(v).__name__}(len={len(v)})")

# Find out what the store actually exposes, so we can count chunks per doc
print("\nStore attributes:", [a for a in dir(store) if not a.startswith("_")])

# Try common chunk containers; adjust once you see the attribute list above
for name in ("chunks", "metadata", "metas", "records", "items"):
    data = getattr(store, name, None)
    if isinstance(data, (list, tuple)) and data:
        print(f"\nSample entry from store.{name}:", data[0])
        counts = collections.Counter()
        for c in data:
            d = c if isinstance(c, dict) else getattr(c, "__dict__", {})
            counts[str(d.get("doc_id") or d.get("document_id") or d.get("source") or "UNKNOWN")] += 1
        print("Chunks per document:", dict(counts))
        break