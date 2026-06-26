"""
backfill_meta.py
Backfills WIN_NBR and L1/L2 manager data for rows in the existing SQLite DB
where those fields are blank, using data from other rows of the SAME vcc_id.

Priority: rows where l1_manager is non-empty are used first (user's requirement).
Run once after updating gcp.py, before the next BQ refresh.
"""
import sys, sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "app"))
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# Fetch all distinct vcc_ids
vcc_ids = [r[0] for r in conn.execute(
    "SELECT DISTINCT vcc_id FROM roster WHERE vcc_id IS NOT NULL AND vcc_id != ''"
).fetchall()]

print(f"Processing {len(vcc_ids)} unique agents...")

updated = 0
for vcc in vcc_ids:
    rows = conn.execute(
        """SELECT win_id, login_id, full_name, team_name, role,
                  bus_line, l1_manager, l2_manager
           FROM roster
           WHERE vcc_id = ?
           ORDER BY
               CASE WHEN l1_manager IS NOT NULL AND l1_manager != '' THEN 0 ELSE 1 END,
               CASE WHEN win_id     IS NOT NULL AND win_id     != '' THEN 0 ELSE 1 END
        """,
        (vcc,)
    ).fetchall()

    if not rows:
        continue

    # Build best values per field
    best: dict[str, str] = {
        "win_id": "", "login_id": "", "full_name": "",
        "team_name": "", "role": "", "bus_line": "",
        "l1_manager": "", "l2_manager": "",
    }
    for r in rows:
        for field in best:
            if not best[field] and r[field]:
                best[field] = r[field]
        if all(best.values()):
            break

    # Update ALL rows for this vcc_id with the resolved best values
    conn.execute(
        """UPDATE roster SET
               win_id     = ?,
               login_id   = ?,
               full_name  = ?,
               team_name  = ?,
               role       = ?,
               bus_line   = ?,
               l1_manager = ?,
               l2_manager = ?
           WHERE vcc_id = ?
        """,
        (best["win_id"], best["login_id"], best["full_name"],
         best["team_name"], best["role"], best["bus_line"],
         best["l1_manager"], best["l2_manager"], vcc)
    )
    updated += 1

conn.commit()
conn.close()

print(f"Done! Backfilled metadata for {updated} agents.")
print("WIN_NBR and L1_Manager gaps resolved from sibling rows.")
