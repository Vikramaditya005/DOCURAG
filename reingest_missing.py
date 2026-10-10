import glob
from docurag import pipeline

JOBS = {
    "2": glob.glob("storage/uploads/INFOSYS*VRf*.pdf")[0],
    "5": "storage/uploads/Formal_pic.jpeg",
    "7": "storage/uploads/LICENSE_AGREEMENT.pdf",
}

for doc_id, path in JOBS.items():
    report = pipeline.ingest_file(path, document_id=doc_id)
    print(doc_id, path, "-> chunks:", report.get("chunks_indexed"))

store = pipeline.get_engine()["store"]
print("\nFinal store stats:")
for k, v in store.stats().items():
    print(" ", k, v)
