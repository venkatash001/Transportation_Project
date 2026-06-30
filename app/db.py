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
            CREATE TABLE IF NOT EXISTS agent_master (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                login_id     TEXT NOT NULL COLLATE NOCASE,
                win_id       TEXT DEFAULT '',
                first_name   TEXT DEFAULT '',
                last_name    TEXT DEFAULT '',
                full_name    TEXT DEFAULT '',
                role         TEXT DEFAULT '',
                status       TEXT DEFAULT '',
                lob          TEXT DEFAULT '',
                location     TEXT DEFAULT '',
                l1_manager   TEXT DEFAULT '',
                l2_manager   TEXT DEFAULT '',
                ops_manager  TEXT DEFAULT '',
                source_file  TEXT DEFAULT '',
                loaded_at    TEXT DEFAULT '',
                UNIQUE(login_id)
            );
            CREATE INDEX IF NOT EXISTS idx_master_login ON agent_master(login_id COLLATE NOCASE);

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

            CREATE INDEX IF NOT EXISTS idx_roster_date  ON roster(schedule_date);
            CREATE INDEX IF NOT EXISTS idx_roster_team  ON roster(team_name);
            CREATE INDEX IF NOT EXISTS idx_roster_vcc   ON roster(vcc_id);
            CREATE INDEX IF NOT EXISTS idx_roster_login ON roster(login_id);
            CREATE INDEX IF NOT EXISTS idx_ovr_vcc      ON roster_overrides(vcc_id);
            CREATE INDEX IF NOT EXISTS idx_ovr_date     ON roster_overrides(schedule_date);
        """)

        # --- Column migration: add shift_type if it doesn't exist yet ---
        existing = {row[1] for row in conn.execute("PRAGMA table_info(roster)").fetchall()}
        if "shift_type" not in existing:
            conn.execute("ALTER TABLE roster ADD COLUMN shift_type TEXT DEFAULT 'FULL'")
            conn.commit()
            logger.info("Migration applied: added shift_type column to roster table.")

    logger.info("Database initialised at %s", DB_PATH)


# -- Agent Master -----------------------------------------------------------
def upsert_master(rows: list[dict]) -> int:
    """Bulk upsert agent master records. Returns count written."""
    if not rows:
        return 0
    sql = """
        INSERT INTO agent_master
            (login_id, win_id, first_name, last_name, full_name,
             role, status, lob, location, l1_manager, l2_manager,
             ops_manager, source_file, loaded_at)
        VALUES
            (:login_id, :win_id, :first_name, :last_name, :full_name,
             :role, :status, :lob, :location, :l1_manager, :l2_manager,
             :ops_manager, :source_file, :loaded_at)
        ON CONFLICT(login_id) DO UPDATE SET
            win_id      = excluded.win_id,
            first_name  = excluded.first_name,
            last_name   = excluded.last_name,
            full_name   = excluded.full_name,
            role        = excluded.role,
            status      = excluded.status,
            lob         = excluded.lob,
            location    = excluded.location,
            l1_manager  = excluded.l1_manager,
            l2_manager  = excluded.l2_manager,
            ops_manager = excluded.ops_manager,
            source_file = excluded.source_file,
            loaded_at   = excluded.loaded_at
    """
    with _connect() as conn:
        conn.executemany(sql, rows)
        conn.commit()
    return len(rows)


def get_master_stats() -> dict:
    """Return row counts and source file info for agent_master."""
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM agent_master").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM agent_master WHERE LOWER(status)='active'"
        ).fetchone()[0]
        lob_count = conn.execute(
            "SELECT COUNT(DISTINCT lob) FROM agent_master WHERE lob != ''"
        ).fetchone()[0]
        sources = conn.execute(
            "SELECT source_file, COUNT(*) as cnt, MAX(loaded_at) as last_loaded "
            "FROM agent_master GROUP BY source_file ORDER BY source_file"
        ).fetchall()
        last_loaded = conn.execute(
            "SELECT MAX(loaded_at) FROM agent_master"
        ).fetchone()[0]
    return {
        "total": total,
        "active": active,
        "lob_count": lob_count,
        "sources": [dict(r) for r in sources],
        "last_loaded": last_loaded,
    }


def get_master_teams() -> list[str]:
    """Return distinct LOBs from agent_master (clean Excel names)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT lob FROM agent_master "
            "WHERE lob IS NOT NULL AND lob != '' ORDER BY lob"
        ).fetchall()
    return [r[0] for r in rows]


def get_locations() -> list[str]:
    """Return distinct source_file values from agent_master (e.g. MAA, BLR)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT source_file FROM agent_master "
            "WHERE source_file IS NOT NULL AND source_file != '' ORDER BY source_file"
        ).fetchall()
    return [r[0] for r in rows]


def get_l2_managers() -> list[str]:
    """Distinct L2 managers from agent_master (fast, no 83k join)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT l2_manager FROM agent_master "
            "WHERE l2_manager IS NOT NULL AND l2_manager != '' ORDER BY l2_manager"
        ).fetchall()
    return [r[0] for r in rows]


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
    """Return team/LOB list. Prefers clean master LOBs when available."""
    master = get_master_teams()
    if master:
        return master
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT team_name FROM roster "
            "WHERE team_name IS NOT NULL AND team_name != '' ORDER BY team_name"
        ).fetchall()
    return [r["team_name"] for r in rows]


def get_l1_managers() -> list[str]:
    """Distinct L1 managers from agent_master (fast, no 83k join)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT l1_manager FROM agent_master "
            "WHERE l1_manager IS NOT NULL AND l1_manager != '' ORDER BY l1_manager"
        ).fetchall()
    return [r[0] for r in rows]


def get_agents_for_manager(l1_manager: str) -> list[dict]:
    """Fast agent list from agent_master (1,619 rows). vcc_id resolved via subquery."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT
                COALESCE(sub.vcc_id, m.login_id) AS vcc_id,
                m.login_id,
                m.win_id,
                m.full_name,
                m.lob   AS team_name,
                m.role,
                m.l1_manager
            FROM agent_master m
            LEFT JOIN (
                SELECT login_id, MIN(vcc_id) AS vcc_id
                FROM roster WHERE login_id != ''
                GROUP BY login_id
            ) sub ON m.login_id = sub.login_id COLLATE NOCASE
            WHERE m.l1_manager = ? AND m.full_name != ''
            ORDER BY m.full_name
            """,
            (l1_manager,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_agents() -> list[dict]:
    """Fast agent list from agent_master (1,619 rows). vcc_id resolved via subquery."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT
                COALESCE(sub.vcc_id, m.login_id) AS vcc_id,
                m.login_id,
                m.win_id,
                m.full_name,
                m.lob   AS team_name,
                m.role,
                m.l1_manager
            FROM agent_master m
            LEFT JOIN (
                SELECT login_id, MIN(vcc_id) AS vcc_id
                FROM roster WHERE login_id != ''
                GROUP BY login_id
            ) sub ON m.login_id = sub.login_id COLLATE NOCASE
            WHERE m.full_name != ''
            ORDER BY m.full_name
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_master_lookup() -> dict[str, dict]:
    """Load agent_master into a dict keyed by lowercase login_id.
    Trivially fast: 1,619 rows, no join needed."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT login_id, win_id, full_name, lob, role, "
            "l1_manager, l2_manager, ops_manager, source_file "
            "FROM agent_master"
        ).fetchall()
    return {(r["login_id"] or "").lower(): dict(r) for r in rows}


_SORT_KEYS: dict[str, tuple] = {
    "name_asc":  ("full_name",  "schedule_date"),
    "name_desc": ("full_name",  "schedule_date"),
    "team_asc":  ("team_name",  "full_name", "schedule_date"),
    "l1_asc":    ("l1_manager", "full_name", "schedule_date"),
    "win_asc":   ("win_id",     "full_name", "schedule_date"),
}


def get_roster_for_range(
    start_date: str, end_date: str,
    team: str = "", location: str = "",
    l1: str = "", l2: str = "",
    sort_by: str = "name_asc",
) -> list[dict]:
    """Fetch roster rows enriched with master data.

    Strategy: simple date-indexed roster scan (fast) + O(n) Python dict
    lookup against agent_master (1,619 rows). No SQL JOIN = no index hell.
    """
    master = get_master_lookup()  # {login_id_lower: {fields}} - 1,619 rows

    with _connect() as conn:
        raw = conn.execute(
            """
            SELECT vcc_id, login_id, win_id, full_name, team_name, role,
                   bus_line, l1_manager, l2_manager,
                   schedule_date, start_ist, end_ist, shift_label, shift_type
            FROM roster
            WHERE schedule_date BETWEEN ? AND ?
              AND login_id IS NOT NULL AND login_id != ''
            """,
            (start_date, end_date),
        ).fetchall()

    enriched: list[dict] = []
    for r in raw:
        login = (r["login_id"] or "").lower().strip()
        m     = master.get(login, {})
        record = {
            "vcc_id":        r["vcc_id"],
            "login_id":      r["login_id"],
            "bus_line":      r["bus_line"],
            "schedule_date": r["schedule_date"],
            "start_ist":     r["start_ist"],
            "end_ist":       r["end_ist"],
            "shift_label":   r["shift_label"],
            "shift_type":    r["shift_type"],
            # Excel master wins over BQ where available
            "win_id":     m.get("win_id")     or r["win_id"]     or "",
            "full_name":  m.get("full_name")  or r["full_name"]  or "",
            "team_name":  m.get("lob")        or r["team_name"]  or "",
            "role":       m.get("role")        or r["role"]       or "",
            "l1_manager": m.get("l1_manager") or r["l1_manager"] or "",
            "l2_manager": m.get("l2_manager") or r["l2_manager"] or "",
            "location":   m.get("source_file") or "",
        }
        enriched.append(record)

    # Filter in Python (cheap after the indexed DB fetch)
    if team:
        enriched = [r for r in enriched if r["team_name"] == team]
    if location:
        enriched = [r for r in enriched if r["location"] == location]
    if l1:
        enriched = [r for r in enriched if r["l1_manager"] == l1]
    if l2:
        enriched = [r for r in enriched if r["l2_manager"] == l2]

    # Sort
    sort_fields = _SORT_KEYS.get(sort_by, _SORT_KEYS["name_asc"])
    reverse     = sort_by == "name_desc"

    def _sort_key(r: dict) -> tuple:
        parts = []
        for f in sort_fields:
            v = r.get(f, "")
            if f == "win_id":
                parts.append(int(v) if str(v).isdigit() else 0)
            else:
                parts.append((v or "").lower())
        return tuple(parts)

    enriched.sort(key=_sort_key, reverse=reverse)
    return enriched
