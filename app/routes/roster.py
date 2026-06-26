"""
routes/roster.py - Future Schedule and Historical roster tab endpoints.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import FUTURE_DAYS, HISTORICAL_DAYS, APP_DIR
from db import get_roster_for_range, get_teams, get_overrides_for_range
from matrix import build_matrix, date_range
from auth import is_admin

router    = APIRouter()
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def _render_roster(request: Request, start: date, end: date, team: str, tab: str, empty_msg: str):
    dates    = date_range(start, end)
    rows     = get_roster_for_range(start.isoformat(), end.isoformat(), team)
    overrides = get_overrides_for_range(start.isoformat(), end.isoformat())
    agents, dates = build_matrix(rows, dates, overrides)
    return templates.TemplateResponse("partials/roster_table.html", {
        "request":       request,
        "agents":        agents,
        "dates":         dates,
        "teams":         get_teams(),
        "selected_team": team,
        "tab":           tab,
        "empty_message": empty_msg,
        "is_admin":      is_admin(request),
    })


@router.get("/roster/future", response_class=HTMLResponse)
async def future_roster(request: Request, team: str = Query("")):
    today = date.today()
    return _render_roster(request, today, today + timedelta(days=FUTURE_DAYS),
                          team, "future",
                          "No future schedules found. Admin: click Refresh from GCP.")


@router.get("/roster/historical", response_class=HTMLResponse)
async def historical_roster(request: Request, team: str = Query("")):
    today = date.today()
    return _render_roster(request, today - timedelta(days=HISTORICAL_DAYS),
                          today - timedelta(days=1), team, "historical",
                          "No historical data found. Admin: click Refresh from GCP.")
