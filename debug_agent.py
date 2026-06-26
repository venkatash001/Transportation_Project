import sys, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "app"))
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# How many total rows does a0s1tiz have?
all_rows = conn.execute(
    "SELECT vcc_id, login_id, win_id, full_name, l1_manager, l2_manager, "
    "team_name, schedule_date, start_ist, end_ist "
    "FROM roster WHERE login_id = 'a0s1tiz' "
    "ORDER BY schedule_date"
).fetchall()

print(f"Total rows for a0s1tiz: {len(all_rows)}")
print("\nSample rows:")
for r in all_rows[:5]:
    d = dict(r)
    print(f"  date={d['schedule_date']} | win={repr(d['win_id'])} | l1={repr(d['l1_manager'])} | shift={d['start_ist'][:16] if d['start_ist'] else 'N/A'}")

# Check if ANY row for this vcc_id has win or l1
vcc = all_rows[0]['vcc_id'] if all_rows else None
if vcc:
    print(f"\nvcc_id = {vcc}")
    has_win = conn.execute(
        "SELECT COUNT(*) FROM roster WHERE vcc_id=? AND win_id != ''", (vcc,)
    ).fetchone()[0]
    has_l1 = conn.execute(
        "SELECT COUNT(*) FROM roster WHERE vcc_id=? AND l1_manager != ''", (vcc,)
    ).fetchone()[0]
    print(f"Rows with WIN_NBR   : {has_win}")
    print(f"Rows with L1_Manager: {has_l1}")
else:
    print("User a0s1tiz NOT FOUND in SQLite at all!")

conn.close()
