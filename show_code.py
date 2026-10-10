import inspect
import docurag.pipeline as p

for name in ("get_engine", "ingest_file", "ask", "_ask_linear"):
    print("\n" + "=" * 30, name, "=" * 30)
    print(inspect.getsource(getattr(p, name)))

store = p.get_engine()["store"]
for meth in ("add_document", "save", "load", "remove_document"):
    print("\n" + "=" * 30, "store." + meth, "=" * 30)
    print(inspect.getsource(getattr(type(store), meth)))