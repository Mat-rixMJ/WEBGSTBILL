import sqlite3, os

paths = [
    os.path.join(os.path.dirname(__file__), "webgst.db"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "webgst.db"),
]

for path in paths:
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"DB: {path} exists={exists} size={size}")
    if not exists:
        continue
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    for table in ["suppliers", "purchase_invoices", "purchase_items"]:
        try:
            cur.execute(f"select count(*) from {table}")
            count = cur.fetchone()[0]
            print(f"  {table}: {count}")
        except Exception as e:
            print(f"  {table}: ERROR {e}")
    conn.close()
