"""
main.py - FastAPI application entry point for CES IND Transport Roster.
Handles: app lifecycle, APScheduler (2-hr GCP refresh), auth, root + API routes.
"""
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler

from config import HOST, PORT, REFRESH_INTERVAL_HOURS, APP_DIR
from db import init_db, get_refresh_status, get_teams, get_l1_managers, get_l2_managers, get_locations
from refresh import run_refresh
from master import auto_load_master_if_empty
from auth import check_credentials, set_session, clear_session, is_admin, get_role
from routes.roster  import router as roster_router
from routes.summary import router as summary_router
from routes.export  import router as export_router
from routes.admin   import router as admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    status = get_refresh_status()
    logger.info("DB has %d records on startup.", status["total_records"])
    master_result = auto_load_master_if_empty()
    if master_result.get("skipped"):
        logger.info("Master data: %d agents already loaded.", master_result["total"])
    else:
        logger.info("Master data auto-loaded: %d agents.", master_result.get("total", 0))
    scheduler.add_job(run_refresh, trigger="interval",
                      hours=REFRESH_INTERVAL_HOURS, id="gcp_refresh", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — GCP refresh every %dh", REFRESH_INTERVAL_HOURS)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="CES IND Transport Roster", version="1.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

app.include_router(roster_router)
app.include_router(summary_router)
app.include_router(export_router)
app.include_router(admin_router)


# ---------------------------------------------------------------------------
# Main index
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    status       = get_refresh_status()
    teams        = get_teams()
    locations    = get_locations()
    l1_managers  = get_l1_managers()
    l2_managers  = get_l2_managers()
    last_refresh = status["last_refresh"]
    if last_refresh:
        try:
            last_refresh = datetime.fromisoformat(last_refresh).strftime("%d %b %Y, %I:%M %p UTC")
        except Exception:
            pass
    return templates.TemplateResponse("index.html", {
        "request":       request,
        "status":        status,
        "last_refresh":  last_refresh,
        "teams":         teams,
        "locations":     locations,
        "l1_managers":   l1_managers,
        "l2_managers":   l2_managers,
        "total_records": status["total_records"],
        "is_admin":      is_admin(request),
        "role":          get_role(request),
    })


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    if is_admin(request):
        return RedirectResponse(next)
    return templates.TemplateResponse("login.html", {"request": request, "next": next, "error": ""})


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str     = Form("/"),
):
    if check_credentials(username, password):
        response = RedirectResponse(next, status_code=303)
        set_session(response, role="admin")
        return response
    return templates.TemplateResponse("login.html", {
        "request": request, "next": next,
        "error": "Invalid username or password.",
    })


@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse("/")
    clear_session(response)
    return response


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
@app.post("/api/refresh")
async def manual_refresh(request: Request):
    if not is_admin(request):
        return JSONResponse({"success": False, "message": "Admin access required."}, status_code=403)
    result = run_refresh()
    return JSONResponse(content=result)


@app.get("/api/status")
async def refresh_status():
    return JSONResponse(content=get_refresh_status())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
