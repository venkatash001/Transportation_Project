import sys, sqlite3
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "app"))
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

today = date.today()
start = today.isoformat()
end   = (today + timedelta(days=30)).isoformat()

# Matrix is sorted by full_name — get distinct agents in that order
agents = conn.execute("""
    SELECT DISTINCT vcc_id, login_id, win_id, full_name, l1_manager, l2_manager, team_name
    FROM roster
    WHERE schedule_date BETWEEN ? AND ?
    ORDER BY full_name
""", (start, end)).fetchall()

print(f"Total agents in future roster: {len(agents)}")
print()

# Row 620 (1-indexed in the UI)
if len(agents) >= 620:
    a = dict(agents[619])   # 0-indexed
    print("=== Row 620 ===")
    for k, v in a.items():
        print(f"  {k:15s}: {repr(v)}")
else:
    print(f"Only {len(agents)} agents — row 620 doesn't exist in future view")
    print("Checking historical view instead...")
    start2 = (today - timedelta(days=90)).isoformat()
    agents2 = conn.execute("""
        SELECT DISTINCT vcc_id, login_id, win_id, full_name, l1_manager, l2_manager, team_name
        FROM roster
        WHERE schedule_date BETWEEN ? AND ?
        ORDER BY full_name
    """, (start2, end)).fetchall()
    print(f"Total agents in historical+future: {len(agents2)}")
    if len(agents2) >= 620:
        a = dict(agents2[619])
        print("=== Row 620 (historical+future) ===")
        for k, v in a.items():
            print(f"  {k:15s}: {repr(v)}")

# Also show rows around 618-622 for context
print("\n=== Rows 618-622 for context ===")
sample = agents[617:622] if len(agents) >= 622 else agents[-5:]
for i, row in enumerate(sample, start=618):
    r = dict(row)
    print(f"  [{i}] {r['full_name'][:30]:30s} | win={repr(r['win_id'])[:15]} | l1={repr(r['l1_manager'])[:30]}")

conn.close()
