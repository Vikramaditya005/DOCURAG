from docurag import pipeline

JOBS = {
    "5": "storage/uploads/Formal_pic.jpeg",
    "6": "storage/uploads/MLS_Assignment_01.pdf",
}

for doc_id, path in JOBS.items():
    report = pipeline.ingest_file(path, document_id=doc_id)
    print(doc_id, "-> chunks:", report.get("chunks_indexed"))

store = pipeline.get_engine()["store"]
for i in store.doc_map.get("5", []):
    c = store.get(i)
    print("\nDOC 5 CHUNK:", c.content_type, "|", c.content[:600])
