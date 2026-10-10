import glob
from docurag import pipeline

JOBS = {
    "2": glob.glob("storage/uploads/INFOSYS*VRf*.pdf")[0],
    "5": "storage/uploads/Formal_pic.jpeg",
    "6": "storage/uploads/MLS_Assignment_01.pdf",
    "7": "storage/uploads/LICENSE_AGREEMENT.pdf",
}

for doc_id, path in JOBS.items():
    report = pipeline.ingest_file(path, document_id=doc_id)
    print(doc_id, "-> chunks:", report.get("chunks_indexed"))
