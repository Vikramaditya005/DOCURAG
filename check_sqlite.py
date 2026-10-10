import sqlite3

conn = sqlite3.connect("backend/db.sqlite3")
cursor = conn.cursor()
cursor.execute("SELECT id, filename, status FROM api_document;")
docs = cursor.fetchall()
print(f"Total Documents: {len(docs)}")
for doc in docs:
    cursor.execute("SELECT count(*) FROM api_chunk WHERE document_id=?", (doc[0],))
    chunks = cursor.fetchone()[0]
    print(f" - {doc[1]}: {chunks} chunks (Status: {doc[2]})")
