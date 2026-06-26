"""
gcp.py - BigQuery data fetch for the Transport Roster.
Loads the SQL from query/agent_schedule_query.sql,
injects a dynamic date range, and normalises results.
"""
import os
import logging
import re
from datetime import date, timedelta

from config import QUERY_FILE, FUTURE_DAYS, HISTORICAL_DAYS, GCP_PROJECT, ROOT_DIR

logger = logging.getLogger(__name__)

_SHIFT_OFF = "OFF"


def _fmt_time(ts: str | None) -> str:
    """
    Convert '2026-06-26 07:00:00' -> '07:00 AM' (12-hour clock).
    Returns empty string on bad input.
    """
    if not ts:
        return ""
    try:
        time_part = ts.split(" ")[1]
        h_str, m_str, _ = time_part.split(":")
        h = int(h_str)
        suffix = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        return f"{h12:02d}:{m_str} {suffix}"
    except Exception:
        return ts


def _build_shift_label(start_ist: str, end_ist: str) -> str:
    s = _fmt_time(start_ist)
    e = _fmt_time(end_ist)
    return f"{s} - {e}" if (s and e) else _SHIFT_OFF


def _load_query() -> str:
    if not QUERY_FILE.exists():
        raise FileNotFoundError(f"SQL file not found: {QUERY_FILE}")
    return QUERY_FILE.read_text(encoding="utf-8")


def _inject_dates(sql: str, start: date, end: date) -> str:
    """Replace the hardcoded date BETWEEN clause with dynamic dates."""
    pattern = (
        r"S\.SCHED_ACTV_START_DT_UTC\s+BETWEEN\s+'[^']+'\s+AND\s+\S+"
    )
    replacement = (
        f"S.SCHED_ACTV_START_DT_UTC BETWEEN '{start.isoformat()}' "
        f"AND '{end.isoformat()}'"
    )
    new_sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
    if new_sql == sql:
        logger.warning("Date injection regex did not match — query unchanged.")
    return new_sql


def _best_meta(rows_for_vcc: list[dict]) -> dict:
    """
    Build the richest possible metadata profile for one VCC_ID by scanning
    ALL its rows across every date.

    Priority rules (applied per-field):
      1. Rows where LVL1_MGR_LOGIN_NM is non-empty are tried FIRST for every
         field — so manager-populated rows anchor the profile.
      2. If a field is still blank after those rows, fall back to any remaining
         row that has it (e.g. WIN_NBR that appears on only one date's row).
      3. Each field is filled exactly once — first non-empty value wins.
    """
    # Separate rows: L1-populated first, then the rest
    with_l1    = [r for r in rows_for_vcc if (r.get("LVL1_MGR_LOGIN_NM") or "").strip()]
    without_l1 = [r for r in rows_for_vcc if not (r.get("LVL1_MGR_LOGIN_NM") or "").strip()]
    priority   = with_l1 + without_l1

    meta: dict[str, str] = {
        "win_id": "", "login_id": "", "first_name": "", "last_name": "",
        "full_name": "", "team_name": "", "role": "",
        "bus_line": "", "l1_manager": "", "l2_manager": "",
    }

    for r in priority:
        def _s(col: str) -> str:
            return str(r.get(col) or "").strip()

        if not meta["win_id"]:      meta["win_id"]     = _s("WIN_NBR")
        if not meta["login_id"]:    meta["login_id"]   = _s("LOGIN_ID")
        if not meta["l1_manager"]:  meta["l1_manager"] = _s("LVL1_MGR_LOGIN_NM")
        if not meta["l2_manager"]:  meta["l2_manager"] = _s("LVL2_MGR_LOGIN_NM")
        if not meta["team_name"]:   meta["team_name"]  = _s("Team_Name")
        if not meta["role"]:        meta["role"]       = _s("AGNT_PROFL_NM")
        if not meta["bus_line"]:    meta["bus_line"]   = _s("BUS_LINE_NM")
        if not meta["full_name"]:
            fn   = _s("FIRST_NM")
            ln   = _s("LAST_NM")
            full = f"{fn} {ln}".strip()
            if full:
                meta["first_name"] = fn
                meta["last_name"]  = ln
                meta["full_name"]  = full

        # Early-exit once every field is filled
        if all(meta.values()):
            break

    return meta


def fetch_from_gcp() -> list[dict]:
    """
    Execute the BigQuery schedule query and return normalised row dicts.

    Two-pass strategy
    -----------------
    Pass 1 — metadata sweep:
        For every VCC_ID, scan ALL rows across ALL dates to build the richest
        possible agent profile.  Rows where LVL1_MGR_LOGIN_NM is non-empty
        are used first for every field; remaining rows fill any gaps
        (e.g. WIN_NBR that only appears on one particular date's row).

    Pass 2 — schedule sweep:
        Keep only the LONGEST-duration row per (vcc_id, schedule_date) for
        shift start/end times.  Duration >= 120 min to exclude breaks/meetings.

    Merge:
        Stamp the best metadata from Pass 1 onto every schedule entry from
        Pass 2, so WIN_NBR and L1_MGR are always populated when available.
    """
    try:
        from google.cloud import bigquery  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-bigquery is not installed. "
            "Run the installer batch or: pip install google-cloud-bigquery"
        ) from exc

    today = date.today()
    start = today - timedelta(days=HISTORICAL_DAYS)
    end   = today + timedelta(days=FUTURE_DAYS + 5)

    sql = _inject_dates(_load_query(), start, end)
    logger.info("Submitting BQ query: %s to %s", start.isoformat(), end.isoformat())

    key_file = ROOT_DIR / "gcp_service_account.json"
    if key_file.exists() and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_file)
        logger.info("Using service account key: %s", key_file)

    client  = bigquery.Client(project=GCP_PROJECT)
    job     = client.query(sql)
    results = job.result()

    MIN_DURATION_MINUTES = 120

    # ── Collect every qualifying raw row ────────────────────────────────────
    # Each entry: (vcc, sched_date, duration_min, start_ist, end_ist, raw_dict)
    qualifying: list[tuple] = []
    vcc_raw: dict[str, list[dict]] = {}      # all raw rows grouped by vcc_id

    for r in results:
        raw = dict(r)
        dur = int(raw.get("SCHED_ACTV_DUR_MIN_QTY") or 0)
        vcc = str(raw.get("VCC_ID") or "").strip()
        if not vcc:
            continue

        # Always collect for metadata pass (even short rows have manager data)
        vcc_raw.setdefault(vcc, []).append(raw)

        if dur < MIN_DURATION_MINUTES:
            continue   # exclude from schedule pass only

        start_ist  = str(raw.get("Schedule_StartTime_IST") or "")
        end_ist    = str(raw.get("Schedule_EndTime_IST")   or "")
        sched_date = start_ist[:10] if len(start_ist) >= 10 else ""
        if not sched_date:
            continue

        qualifying.append((vcc, sched_date, dur, start_ist, end_ist, raw))

    logger.info("BQ returned %d total rows; %d qualify (dur >= %d min) across %d agents",
                sum(len(v) for v in vcc_raw.values()),
                len(qualifying), MIN_DURATION_MINUTES, len(vcc_raw))

    # ── Pass 1: build best metadata per VCC_ID ──────────────────────────────
    meta_map: dict[str, dict] = {
        vcc: _best_meta(raw_rows)
        for vcc, raw_rows in vcc_raw.items()
    }

    # Log how many agents now have WIN and L1 filled
    filled_win = sum(1 for m in meta_map.values() if m["win_id"])
    filled_l1  = sum(1 for m in meta_map.values() if m["l1_manager"])
    logger.info("Metadata pass: %d/%d agents have WIN_NBR; %d/%d have L1_Manager",
                filled_win, len(meta_map), filled_l1, len(meta_map))

    # ── Pass 2: longest-duration schedule row per (vcc, date) ───────────────
    # schedule_map: {(vcc, date): (dur, start_ist, end_ist)}
    schedule_map: dict[tuple, tuple] = {}
    for vcc, sched_date, dur, start_ist, end_ist, _ in qualifying:
        key = (vcc, sched_date)
        if key not in schedule_map or dur > schedule_map[key][0]:
            schedule_map[key] = (dur, start_ist, end_ist)

    # ── Merge and build final rows ───────────────────────────────────────────
    rows: list[dict] = []
    for (vcc, sched_date), (dur, start_ist, end_ist) in schedule_map.items():
        meta       = meta_map.get(vcc, {})
        shift_type = "HALF" if 240 <= dur < 480 else "FULL"

        rows.append({
            "vcc_id":        vcc,
            "win_id":        meta.get("win_id",    ""),
            "login_id":      meta.get("login_id",  ""),
            "first_name":    meta.get("first_name",""),
            "last_name":     meta.get("last_name", ""),
            "full_name":     meta.get("full_name", ""),
            "team_name":     meta.get("team_name", ""),
            "role":          meta.get("role",      ""),
            "bus_line":      meta.get("bus_line",  ""),
            "l1_manager":    meta.get("l1_manager",""),
            "l2_manager":    meta.get("l2_manager",""),
            "schedule_date": sched_date,
            "start_ist":     start_ist,
            "end_ist":       end_ist,
            "shift_label":   _build_shift_label(start_ist, end_ist),
            "shift_type":    shift_type,
        })

    logger.info("Final output: %d schedule rows across %d agents",
                len(rows), len({r['vcc_id'] for r in rows}))
    return rows
