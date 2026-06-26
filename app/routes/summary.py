"""
routes/summary.py - Daily summary stats tab endpoint.
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
from matrix import build_summary, date_range

router    = APIRouter()
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


@router.get("/summary", response_class=HTMLResponse)
async def summary_view(
    request: Request,
    team: str  = Query(""),
    scope: str = Query("future"),
):
    today = date.today()
    if scope == "historical":
        start = today - timedelta(days=HISTORICAL_DAYS)
        end   = today - timedelta(days=1)
    else:
        start = today
        end   = today + timedelta(days=FUTURE_DAYS)

    dates     = date_range(start, end)
    rows      = get_roster_for_range(start.isoformat(), end.isoformat(), team)
    overrides = get_overrides_for_range(start.isoformat(), end.isoformat())
    summary   = build_summary(rows, dates, overrides)

    return templates.TemplateResponse("partials/summary_table.html", {
        "request":       request,
        "summary":       summary,
        "teams":         get_teams(),
        "selected_team": team,
        "scope":         scope,
    })
