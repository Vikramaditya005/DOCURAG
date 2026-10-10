from docurag.pipeline import get_engine
from docurag.retrieve.hybrid import retrieve

engine = get_engine()
evidence = retrieve("what are the questions from the pdf ?", engine["store"], engine["embedder"])
for e in evidence:
    print(f"[{e.eid}] Score: {e.score:.2f} | {e.chunk.content[:100]}...")
