import collections, glob
from pathlib import Path
import docurag.ingest.coordinator as c

files = [
    "storage/uploads/LICENSE_AGREEMENT.pdf",
    "storage/uploads/Formal_pic.jpeg",
    glob.glob("storage/uploads/INFOSYS*")[0],
]

for f in files:
    p = Path(f)
    pages = list(c.iter_document_pages(p, document_id="dbg"))
    chunks = c.document_to_chunks(pages, "dbg")
    print("\n==", p.name)
    print("pages:", len(pages), "| chunks:", len(chunks))
    print("types:", dict(collections.Counter(ch.content_type for ch in chunks)))
    print("sample:", chunks[0].content[:200].replace("\n", " ") if chunks else "NO CHUNKS")