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


def fetch_from_gcp() -> list[dict]:
    """
    Execute the BigQuery schedule query and return normalised row dicts.
    Strategy: fetch all activity rows, then keep only the LONGEST-duration
    row per (vcc_id, schedule_date) — that is always the "Open" activity.
    Short activities (breaks, lunch, meetings) are discarded.
    Minimum duration threshold: 120 minutes (2 hours) to exclude very short entries.
    """
    try:
        from google.cloud import bigquery  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-bigquery is not installed. "
            "Run the installer batch or: pip install google-cloud-bigquery"
        ) from exc

    today  = date.today()
    start  = today - timedelta(days=HISTORICAL_DAYS)
    end    = today + timedelta(days=FUTURE_DAYS + 5)

    sql    = _inject_dates(_load_query(), start, end)
    logger.info("Submitting BQ query: %s to %s", start.isoformat(), end.isoformat())

    # Auto-detect service account key dropped in project root folder
    key_file = ROOT_DIR / "gcp_service_account.json"
    if key_file.exists() and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_file)
        logger.info("Using service account key: %s", key_file)

    client  = bigquery.Client(project=GCP_PROJECT)
    job     = client.query(sql)
    results = job.result()

    # --- Collect all rows, keep longest-duration per (vcc_id, schedule_date) ---
    # duration_map: {(vcc_id, date_str): (duration_min, row_dict)}
    duration_map: dict[tuple, tuple] = {}

    MIN_DURATION_MINUTES = 120  # exclude breaks/meetings shorter than 2 hours

    for r in results:
        raw      = dict(r)
        dur      = int(raw.get("SCHED_ACTV_DUR_MIN_QTY") or 0)
        if dur < MIN_DURATION_MINUTES:
            continue  # skip breaks, meetings, lunches

        start_ist  = str(raw.get("Schedule_StartTime_IST") or "")
        end_ist    = str(raw.get("Schedule_EndTime_IST")   or "")
        sched_date = start_ist[:10] if len(start_ist) >= 10 else ""
        vcc        = str(raw.get("VCC_ID") or "")

        if not vcc or not sched_date:
            continue

        key = (vcc, sched_date)
        if key not in duration_map or dur > duration_map[key][0]:
            fn = (raw.get("FIRST_NM") or "").strip()
            ln = (raw.get("LAST_NM")  or "").strip()
            full_name = f"{fn} {ln}".strip() or (raw.get("AGNT_PROFL_NM") or "")

            # Classify shift type by duration
            if dur >= 480:
                shift_type = "FULL"
            elif dur >= 240:
                shift_type = "HALF"
            else:
                shift_type = "FULL"  # treat unknowns as FULL

            duration_map[key] = (dur, {
                "vcc_id":        vcc,
                "win_id":        str(raw.get("WIN_NBR")           or ""),
                "login_id":      str(raw.get("LOGIN_ID")          or ""),
                "first_name":    fn,
                "last_name":     ln,
                "full_name":     full_name,
                "team_name":     str(raw.get("Team_Name")         or ""),
                "role":          str(raw.get("AGNT_PROFL_NM")     or ""),
                "bus_line":      str(raw.get("BUS_LINE_NM")       or ""),
                "l1_manager":    str(raw.get("LVL1_MGR_LOGIN_NM") or ""),
                "l2_manager":    str(raw.get("LVL2_MGR_LOGIN_NM") or ""),
                "schedule_date": sched_date,
                "start_ist":     start_ist,
                "end_ist":       end_ist,
                "shift_label":   _build_shift_label(start_ist, end_ist),
                "shift_type":    shift_type,
            })

    rows = [v[1] for v in duration_map.values()]
    logger.info("Fetched %d raw BQ rows, kept %d after deduplication", len(duration_map), len(rows))
    return rows
