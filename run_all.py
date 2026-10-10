from docurag.pipeline import ingest_file, ask
import traceback

print("Ingesting...")
ingest_file("data/test_doc.txt")
print("Asking...")
try:
    ask("What is the capital of France?", use_agents=False)
except Exception as e:
    traceback.print_exc()
