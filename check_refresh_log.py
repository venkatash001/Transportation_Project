import sys, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "app"))
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# Last 5 refresh attempts
logs = conn.execute(
    "SELECT refreshed_at, status, record_count, message FROM refresh_log ORDER BY id DESC LIMIT 5"
).fetchall()
print("=== Last 5 Refresh Attempts ===")
for r in logs:
    print(f"  {r['refreshed_at']} | {r['status']:8s} | {r['record_count']:6d} rows | {r['message'] or ''}")

# Check if a0s1tiz data improved at all
print()
a = conn.execute(
    "SELECT login_id, win_id, l1_manager FROM roster WHERE login_id='a0s1tiz' LIMIT 1"
).fetchone()
print(f"a0s1tiz  -> win={repr(a['win_id'])}  l1={repr(a['l1_manager'])}")

conn.close()
