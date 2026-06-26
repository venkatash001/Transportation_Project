"""
manual_fix.py
Direct SQLite patch for agents where we know the correct WIN and L1 data
but BQ refresh keeps returning 0 rows.

Add any agent you want to manually correct to KNOWN_FIXES below.
Format: login_id -> {win_id, l1_manager, l2_manager (optional)}
"""
import sys, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "app"))
from config import DB_PATH

# ── Add known corrections here ────────────────────────────────────────────────
KNOWN_FIXES = {
    "a0s1tiz": {
        "win_id":     "234049562",
        "l1_manager": "MOHAMMED SHARIEF",
    },
}
# ─────────────────────────────────────────────────────────────────────────────

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

for login_id, fixes in KNOWN_FIXES.items():
    rows = conn.execute(
        "SELECT COUNT(*) as c FROM roster WHERE login_id = ?", (login_id,)
    ).fetchone()["c"]

    if rows == 0:
        print(f"SKIP  {login_id} — not found in DB")
        continue

    sets  = ", ".join(f"{col} = ?" for col in fixes)
    vals  = list(fixes.values()) + [login_id]
    conn.execute(f"UPDATE roster SET {sets} WHERE login_id = ?", vals)
    print(f"FIXED {login_id} ({rows} rows) -> {fixes}")

conn.commit()
conn.close()
print("\nDone. Restart the app or refresh the browser to see changes.")
