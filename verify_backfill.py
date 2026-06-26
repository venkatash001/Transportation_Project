import sys, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "app"))
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# Check a0s1tiz specifically
rows = conn.execute(
    "SELECT vcc_id, login_id, win_id, full_name, l1_manager, l2_manager, team_name, schedule_date "
    "FROM roster WHERE login_id = 'a0s1tiz' ORDER BY schedule_date LIMIT 5"
).fetchall()
print("=== a0s1tiz ===")
for r in rows:
    print(dict(r))

# Overall stats: how many still have blank win_id or l1_manager
total    = conn.execute("SELECT COUNT(*) FROM roster").fetchone()[0]
no_win   = conn.execute("SELECT COUNT(*) FROM roster WHERE win_id IS NULL OR win_id = ''").fetchone()[0]
no_l1    = conn.execute("SELECT COUNT(*) FROM roster WHERE l1_manager IS NULL OR l1_manager = ''").fetchone()[0]
agents   = conn.execute("SELECT COUNT(DISTINCT vcc_id) FROM roster").fetchone()[0]
agt_nol1 = conn.execute("SELECT COUNT(DISTINCT vcc_id) FROM roster WHERE l1_manager IS NULL OR l1_manager = ''").fetchone()[0]
agt_nowin= conn.execute("SELECT COUNT(DISTINCT vcc_id) FROM roster WHERE win_id IS NULL OR win_id = ''").fetchone()[0]

print(f"\n=== Stats ===")
print(f"Total rows      : {total:,}")
print(f"Rows blank WIN  : {no_win:,}  ({no_win*100//total}%)")
print(f"Rows blank L1   : {no_l1:,}  ({no_l1*100//total}%)")
print(f"Total agents    : {agents}")
print(f"Agents blank WIN: {agt_nowin}")
print(f"Agents blank L1 : {agt_nol1}")
conn.close()
