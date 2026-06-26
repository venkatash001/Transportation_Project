"""
db.py - SQLite cache layer for the Transport Roster.
All BigQuery data is stored here between refreshes.
"""
import sqlite3
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables and indexes if they don't exist, and run column migrations."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS roster (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                vcc_id        TEXT NOT NULL,
                win_id        TEXT,
                login_id      TEXT,
                first_name    TEXT,
                last_name     TEXT,
                full_name     TEXT,
                team_name     TEXT,
                role          TEXT,
                bus_line      TEXT,
                l1_manager    TEXT,
                l2_manager    TEXT,
                schedule_date TEXT NOT NULL,
                start_ist     TEXT,
                end_ist       TEXT,
                shift_label   TEXT,
                shift_type    TEXT DEFAULT 'FULL',
                UNIQUE(vcc_id, schedule_date)
            );

            CREATE TABLE IF NOT EXISTS roster_overrides (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                vcc_id         TEXT NOT NULL,
                full_name      TEXT,
                schedule_date  TEXT NOT NULL,
                shift_label    TEXT NOT NULL,
                note           TEXT DEFAULT '',
                modified_by    TEXT DEFAULT 'admin',
                modified_at    TEXT NOT NULL,
                UNIQUE(vcc_id, schedule_date)
            );

            CREATE TABLE IF NOT EXISTS refresh_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                refreshed_at TEXT NOT NULL,
                status       TEXT NOT NULL,
                record_count INTEGER DEFAULT 0,
                message      TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_roster_date ON roster(schedule_date);
            CREATE INDEX IF NOT EXISTS idx_roster_team ON roster(team_name);
            CREATE INDEX IF NOT EXISTS idx_roster_vcc  ON roster(vcc_id);
            CREATE INDEX IF NOT EXISTS idx_ovr_vcc     ON roster_overrides(vcc_id);
            CREATE INDEX IF NOT EXISTS idx_ovr_date    ON roster_overrides(schedule_date);
        """)

        # --- Column migration: add shift_type if it doesn't exist yet ---
        existing = {row[1] for row in conn.execute("PRAGMA table_info(roster)").fetchall()}
        if "shift_type" not in existing:
            conn.execute("ALTER TABLE roster ADD COLUMN shift_type TEXT DEFAULT 'FULL'")
            conn.commit()
            logger.info("Migration applied: added shift_type column to roster table.")

    logger.info("Database initialised at %s", DB_PATH)


def upsert_roster(rows: list[dict]) -> int:
    """Bulk upsert roster rows. Returns count of rows written."""
    if not rows:
        return 0
    sql = """
        INSERT INTO roster
            (vcc_id, win_id, login_id, first_name, last_name, full_name,
             team_name, role, bus_line, l1_manager, l2_manager,
             schedule_date, start_ist, end_ist, shift_label, shift_type)
        VALUES
            (:vcc_id, :win_id, :login_id, :first_name, :last_name, :full_name,
             :team_name, :role, :bus_line, :l1_manager, :l2_manager,
             :schedule_date, :start_ist, :end_ist, :shift_label, :shift_type)
        ON CONFLICT(vcc_id, schedule_date) DO UPDATE SET
            login_id   = CASE WHEN excluded.login_id   != '' THEN excluded.login_id   ELSE roster.login_id   END,
            win_id     = CASE WHEN excluded.win_id     != '' THEN excluded.win_id     ELSE roster.win_id     END,
            first_name = CASE WHEN excluded.first_name != '' THEN excluded.first_name ELSE roster.first_name END,
            last_name  = CASE WHEN excluded.last_name  != '' THEN excluded.last_name  ELSE roster.last_name  END,
            full_name  = CASE WHEN excluded.full_name  != '' THEN excluded.full_name  ELSE roster.full_name  END,
            team_name  = CASE WHEN excluded.team_name  != '' THEN excluded.team_name  ELSE roster.team_name  END,
            role       = CASE WHEN excluded.role       != '' THEN excluded.role       ELSE roster.role       END,
            bus_line   = CASE WHEN excluded.bus_line   != '' THEN excluded.bus_line   ELSE roster.bus_line   END,
            l1_manager = CASE WHEN excluded.l1_manager != '' THEN excluded.l1_manager ELSE roster.l1_manager END,
            l2_manager = CASE WHEN excluded.l2_manager != '' THEN excluded.l2_manager ELSE roster.l2_manager END,
            start_ist    = excluded.start_ist,
            end_ist      = excluded.end_ist,
            shift_label  = excluded.shift_label,
            shift_type   = excluded.shift_type
    """
    with _connect() as conn:
        conn.executemany(sql, rows)
        conn.commit()
    return len(rows)


# -- Override CRUD ----------------------------------------------------------
def upsert_override(vcc_id: str, full_name: str, schedule_date: str,
                    shift_label: str, note: str = "") -> None:
    """Save or update a manual shift override."""
    with _connect() as conn:
        conn.execute("""
            INSERT INTO roster_overrides
                (vcc_id, full_name, schedule_date, shift_label, note, modified_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(vcc_id, schedule_date) DO UPDATE SET
                shift_label = excluded.shift_label,
                note        = excluded.note,
                modified_at = excluded.modified_at
        """, (vcc_id, full_name, schedule_date, shift_label, note,
              datetime.utcnow().isoformat()))
        conn.commit()


def delete_override(vcc_id: str, schedule_date: str) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM roster_overrides WHERE vcc_id=? AND schedule_date=?",
            (vcc_id, schedule_date),
        )
        conn.commit()


def get_overrides_for_range(start_date: str, end_date: str) -> dict[str, dict[str, dict]]:
    """Return {vcc_id: {date_str: {shift_label, note}}} for the given range."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT vcc_id, schedule_date, shift_label, note FROM roster_overrides "
            "WHERE schedule_date BETWEEN ? AND ?",
            (start_date, end_date),
        ).fetchall()
    out: dict[str, dict[str, dict]] = {}
    for r in rows:
        out.setdefault(r["vcc_id"], {})[r["schedule_date"]] = {
            "shift_label": r["shift_label"], "note": r["note"],
        }
    return out


# -- Refresh log ------------------------------------------------------------
def log_refresh(status: str, count: int = 0, message: str = "") -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO refresh_log(refreshed_at, status, record_count, message) "
            "VALUES(?,?,?,?)",
            (datetime.utcnow().isoformat(), status, count, message),
        )
        conn.commit()


def get_refresh_status() -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT refreshed_at, status, record_count, message "
            "FROM refresh_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        total = conn.execute("SELECT COUNT(*) AS c FROM roster").fetchone()["c"]
    if not row:
        return {"last_refresh": None, "status": "never", "record_count": 0, "total_records": total}
    return {
        "last_refresh": row["refreshed_at"], "status": row["status"],
        "record_count": row["record_count"], "total_records": total,
    }


def get_teams() -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT team_name FROM roster "
            "WHERE team_name IS NOT NULL AND team_name != '' ORDER BY team_name"
        ).fetchall()
    return [r["team_name"] for r in rows]


def get_l1_managers() -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT l1_manager FROM roster "
            "WHERE l1_manager IS NOT NULL AND l1_manager != '' ORDER BY l1_manager"
        ).fetchall()
    return [r["l1_manager"] for r in rows]


def get_agents_for_manager(l1_manager: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT vcc_id, win_id, login_id, full_name, team_name, role, l1_manager "
            "FROM roster WHERE l1_manager=? ORDER BY full_name",
            (l1_manager,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_agents() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT vcc_id, win_id, login_id, full_name, team_name, role, l1_manager "
            "FROM roster ORDER BY full_name"
        ).fetchall()
    return [dict(r) for r in rows]


def get_roster_for_range(start_date: str, end_date: str, team: str = "") -> list[dict]:
    sql = """
        SELECT vcc_id, win_id, login_id, first_name, last_name, full_name,
               team_name, role, bus_line, l1_manager, l2_manager,
               schedule_date, start_ist, end_ist, shift_label, shift_type
        FROM roster WHERE schedule_date BETWEEN ? AND ?
    """
    params: list = [start_date, end_date]
    if team:
        sql += " AND team_name = ?"
        params.append(team)
    sql += " ORDER BY full_name, schedule_date"
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]
