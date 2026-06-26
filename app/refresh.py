"""
refresh.py - Orchestrates the GCP -> SQLite refresh cycle.
Imported by both the APScheduler job and the /api/refresh endpoint.
Single responsibility: pull data, store it, log the result.
"""
import logging
from db import upsert_roster, log_refresh

logger = logging.getLogger(__name__)


def run_refresh() -> dict:
    """
    Fetch latest data from BigQuery and upsert into SQLite.

    Returns:
        {"success": bool, "count": int, "message": str}
    """
    try:
        from gcp import fetch_from_gcp  # noqa: PLC0415
        rows = fetch_from_gcp()
        if not rows:
            log_refresh("warning", 0, "BigQuery returned 0 rows")
            return {"success": True, "count": 0, "message": "BigQuery returned 0 rows"}
        count = upsert_roster(rows)
        log_refresh("success", count, f"Upserted {count} rows from BigQuery")
        logger.info("Refresh complete: %d rows upserted", count)
        return {"success": True, "count": count, "message": f"Refreshed {count} records"}
    except Exception as exc:
        msg = str(exc)
        logger.error("Refresh failed: %s", msg)
        log_refresh("error", 0, msg)
        return {"success": False, "count": 0, "message": _friendly_error(msg)}


_AUTH_HINTS = {
    "DefaultCredentialsError": "auth",
    "Could not automatically determine credentials": "auth",
    "Application Default Credentials": "auth",
    "google-cloud-bigquery is not installed": "install",
    "403": "permission",
    "404": "notfound",
    "Forbidden": "permission",
}

_MESSAGES = {
    "auth": (
        "GCP credentials not configured. "
        "Fix: Open GCP_Auth_Setup.md in the project folder for step-by-step instructions."
    ),
    "install": (
        "google-cloud-bigquery not installed. "
        "Re-run Run Me.bat to install all dependencies."
    ),
    "permission": (
        "Access denied on BigQuery table. "
        "Check that your service account has BigQuery Data Viewer + Job User roles."
    ),
    "notfound": (
        "BigQuery table or dataset not found. "
        "Check the project ID and dataset in config.py."
    ),
}


def _friendly_error(raw: str) -> str:
    for key, category in _AUTH_HINTS.items():
        if key in raw:
            return _MESSAGES[category]
    return raw
