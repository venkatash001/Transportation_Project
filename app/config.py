"""
config.py - Centralised settings for CES IND Transport Roster app.
"""
import os
import hashlib
from pathlib import Path

# -- Paths ------------------------------------------------------------------
APP_DIR    = Path(__file__).parent          # .../app/
ROOT_DIR   = APP_DIR.parent                 # .../28.Transportation_Roster_Project/
DATA_DIR   = ROOT_DIR / "data"
QUERY_DIR  = ROOT_DIR / "query"
DB_PATH    = DATA_DIR / "roster.db"
QUERY_FILE = QUERY_DIR / "agent_schedule_query.sql"

# -- Server -----------------------------------------------------------------
# 0.0.0.0 = accessible from ALL machines on the same Walmart network
# Change back to 127.0.0.1 to restrict to this machine only
HOST = "0.0.0.0"
PORT = 8501

# -- Scheduling -------------------------------------------------------------
REFRESH_INTERVAL_HOURS = 2

# -- GCP --------------------------------------------------------------------
GCP_PROJECT             = os.getenv("GCP_PROJECT", "wmt-cc-datasphere-prod")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# -- Date windows -----------------------------------------------------------
FUTURE_DAYS     = 30   # days ahead shown in "Future Schedule" tab
HISTORICAL_DAYS = 90   # days back shown in "Historical" tab

# -- Auth -------------------------------------------------------------------
SESSION_SECRET       = os.getenv("ROSTER_SECRET", "ces-ind-transport-roster-2026-secret")
ADMIN_USERNAME       = "CESINDANALYST"
# SHA-256 of "Walmart@00100" — change by setting ROSTER_ADMIN_PASS env var
_raw_pass            = os.getenv("ROSTER_ADMIN_PASS", "Walmart@00100")
ADMIN_PASSWORD_HASH  = hashlib.sha256(_raw_pass.encode()).hexdigest()
SESSION_COOKIE_NAME  = "roster_sess"
SESSION_MAX_AGE_SECS = 8 * 3600   # 8 hours
