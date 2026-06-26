# CES IND Transport Roster - Session Log

---

## Project Overview

| Field          | Value |
|----------------|-------|
| **Project**    | CES IND Transport Roster |
| **Type**       | Web Application |
| **Owner**      | Venkat (V0M06TT) |
| **SharePoint** | `C:\Users\V0M06TT\OneDrive - Walmart Inc\Shared Documents - CareOps_Centralized_Report\999. GCP\28.Transportation_Roster_Project` |
| **GitHub**     | https://github.com/venkatash001/Transportation_Project |
| **Started**    | 2026-06-26 |
| **Agent**      | Kratos (code-puppy-4e37f8) |
| **Server**     | http://127.0.0.1:8501 |
| **Venv**       | `%LOCALAPPDATA%\transport_roster_venv` (Python 3.13.5) |
| **Launcher**   | Double-click `Run Me.bat` |

---

## Tech Stack (Confirmed)

| Layer          | Technology |
|----------------|------------|
| Backend        | Python 3.13 + FastAPI + APScheduler |
| Frontend       | HTMX + Tailwind CSS (CDN) |
| Database       | SQLite (local cache -- `data/roster.db`) |
| Data Source    | Google BigQuery (`wmt-cc-datasphere-prod`) |
| Exports        | openpyxl (Excel), fpdf2 (PDF), csv stdlib |
| Auth           | Google Application Default Credentials or Service Account Key |
| Version Control| Git 2.45.2 + GitHub (venkatash001/Transportation_Project) |

---

## Session History

| # | Date | Summary | Agent |
|---|------|---------|-------|
| 1 | 2026-06-26 | Project kickoff. Verified SharePoint folder + GitHub access. Session log created. | Kratos |
| 1b | 2026-06-26 | Git v2.45.2 installed and verified. GitHub remote confirmed (main branch, commit a20bd180). | Kratos |
| 2 | 2026-06-26 | Full web application built (20 files). Server launched at port 8501. All imports verified OK. | Kratos |
| 3 | 2026-06-26 | Fixed missing google-cloud-bigquery install. Fixed gcp.py bug (missing job line). Added GCP auth setup guide + in-app warning banner. Pending: corrections and enhancements from Venkat. | Kratos |

---

## Session 1 - Repository Access Check

### SharePoint Folder
- **Status:** Accessible -- folder existed, was empty on first check
- **Synced via:** OneDrive for Business

### GitHub Repository
- **URL:** https://github.com/venkatash001/Transportation_Project
- **Status:** Accessible (HTTP 200 confirmed). Has existing `main` branch (commit `a20bd180`).

### Git Installation
- **Status:** Installed (v2.45.2.windows.1)
- **Path:** `C:\Users\V0M06TT\AppData\Local\Programs\Git\cmd\git.exe`
- **Note:** Code Puppy shell sessions need PATH refresh -- use PowerShell with explicit PATH reload.

---

## Session 2 - Full Application Build

### Core Concept
Matrix-style web view of associate shift schedules pulled from GCP BigQuery.
- Rows: User ID (VCC ID) | WIN ID | Full Name
- Columns: One per date, showing shift start-end in IST (e.g. "07:00 AM - 04:00 PM") or "OFF"
- Data source: `agent_schedule_query.sql` against `wmt-cc-datasphere-prod`

### Excel Template Reference
`Sample Roster.xlsx` -- Sheet: Chargeback (68 rows x 37 cols)
- Row 1: Day names (Thu, Fri, Sat...)
- Row 2: Headers (S.No, User ID, Win Nbr, First Name, Last Name, Name, Role, LOB, L1 Sup, L2 Sup) + date columns
- Data cells: "07:00 AM - 04:00 PM" for scheduled, "OFF" for day off

### File Inventory

| File | Size | Purpose |
|------|------|---------|
| `Run Me.bat` | 2.1 KB | One-click runner -- venv setup, install, launch, open browser |
| `requirements.txt` | 158 B | Python dependencies |
| `.gitignore` | -- | Excludes venv, db, .env, __pycache__ |
| `GCP_Auth_Setup.md` | -- | Step-by-step GCP credentials guide |
| `SESSION_LOG.md` | this file | Session log |
| `Sample Roster.xlsx` | 30.6 KB | Reference template (not committed to git) |
| `query/agent_schedule_query.sql` | 4.8 KB | GCP BigQuery SQL (local copy) |
| `app/main.py` | 3.5 KB | FastAPI entry + APScheduler 2h auto-refresh |
| `app/config.py` | 1.1 KB | Paths, port 8501, 30-day future / 90-day historical windows |
| `app/db.py` | 5.6 KB | SQLite CRUD -- init, upsert, query, refresh log |
| `app/gcp.py` | 4.1 KB | BigQuery fetch, IST time formatting, date injection |
| `app/matrix.py` | 3.2 KB | Flat rows -> matrix + daily summary builder |
| `app/refresh.py` | 1.2 KB | GCP -> SQLite orchestrator (scheduler + manual trigger) |
| `app/routes/roster.py` | 2.1 KB | /roster/future and /roster/historical endpoints |
| `app/routes/summary.py` | 1.5 KB | /summary endpoint |
| `app/routes/export.py` | 10.4 KB | /export/csv, /export/excel, /export/pdf endpoints |
| `app/templates/index.html` | 9.1 KB | Main UI: header, tabs, team filter, export buttons, GCP banner |
| `app/templates/partials/roster_table.html` | 4.8 KB | Matrix table (HTMX swap target) |
| `app/templates/partials/summary_table.html` | 5.3 KB | Daily summary table (HTMX swap target) |
| `app/static/style.css` | 1.3 KB | Sticky columns, scrollbar, HTMX spinner |
| `data/roster.db` | 32 KB | SQLite cache (auto-created, gitignored) |

### Features Implemented
- [x] 3-tab UI: Future Schedule (next 30 days) / Historical (last 90 days) / Summary
- [x] Matrix view: sticky identity cols (User ID, WIN, Name) + scrollable date cols
- [x] Date cells: IST shift times in green or "OFF" in gray
- [x] Team filter dropdown (dynamic from DB)
- [x] Client-side search (name / ID / WIN -- no server round-trip)
- [x] Export: CSV, Excel (Walmart-styled, freeze panes, colour coded), PDF (landscape, paginated 14 cols/page)
- [x] Manual "Refresh from GCP" button in header
- [x] APScheduler: auto-refresh every 2 hours
- [x] Last sync timestamp in header
- [x] Empty-state view with prompt to refresh
- [x] GCP auth warning banner (shows when DB is empty)
- [x] Walmart brand colours: Blue #0053E2, Spark Yellow #FFC220
- [x] WCAG 2.2 AA contrast ratios

---

## Session 3 - Bug Fixes and GCP Auth Setup

### Bug Fixed: gcp.py missing job line
During an inline edit, `job = client.query(sql)` was accidentally removed
while `results = job.result()` was still present -- causing a NameError.
Fixed and verified clean import.

### Package Added: google-cloud-bigquery
Was excluded from initial install. Added via uv pip install.
Version: 3.42.1 (installed with all Google auth dependencies).

### Package Added: google-auth-oauthlib
Added for future OAuth browser-flow support.

### GCP Auth -- Current Status
- Google Cloud SDK (gcloud): NOT installed on this machine
- Application Default Credentials file: NOT present
- `gcp_service_account.json` in project root: NOT present yet
- **Status: Blocked -- data cannot be fetched until one of the above is resolved**

### GCP Auth -- Resolution Path (for Venkat)

**Option A (recommended): Service Account Key**
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=wmt-cc-datasphere-prod
2. Pick a service account with BigQuery Data Viewer + Job User roles
3. Keys tab -> Add Key -> JSON -> download
4. Rename to `gcp_service_account.json` and drop in project root (next to Run Me.bat)
5. Click "Refresh from GCP" -- done

**Option B: gcloud CLI**
1. Download from browser: https://cloud.google.com/sdk/docs/install-sdk#windows
2. Install and run: `gcloud auth application-default login`
3. Restart app and refresh

See `GCP_Auth_Setup.md` in project root for the full guide.

### Changes Made This Session
- `app/gcp.py` -- fixed missing `job` line, added `import os`, added service account key auto-detect from project root
- `app/refresh.py` -- added friendly error messages for auth failures, BQ permission errors etc.
- `app/templates/index.html` -- added amber warning banner when DB is empty with step-by-step auth instructions
- `GCP_Auth_Setup.md` -- created full setup guide
- `Run Me.bat` -- fixed Python version pin (removed `--python 3.11`, uses system Python 3.13.5)
- `requirements.txt` -- google-auth-oauthlib added

---

## Open Items / Known Issues

| # | Issue | Status | Notes |
|---|-------|--------|-------|
| 1 | GCP credentials not configured | OPEN | Service account key or gcloud needed -- see GCP_Auth_Setup.md |
| 2 | Corrections and enhancements pending | RESOLVED | Auth, Override Editor, Ad-Hoc Roster, SQL fix all implemented |
| 3 | GitHub push not done yet | OPEN | Needs gcloud or PAT for git push |
| 4 | SQL duration filter returned 0 rows | RESOLVED | Removed WHERE filter, moved deduplication to Python (keep longest duration per agent/date) |
| 5 | SQLite missing shift_type column | RESOLVED | Added ALTER TABLE migration in init_db() -- auto-runs on startup |
| 6 | BQ project ID warning | RESOLVED | Project passed explicitly to bigquery.Client(project=GCP_PROJECT) |
| 7 | Override page 500 error | RESOLVED | Caused by missing shift_type column (item 5) -- fixed by migration |

---

## Decisions Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-06-26 | All project files in SharePoint OneDrive folder | Central storage + team access |
| 2026-06-26 | GitHub: venkatash001/Transportation_Project | Version control + rollback |
| 2026-06-26 | Session Log in SharePoint root | Persistent across sessions |
| 2026-06-26 | Tech stack: FastAPI + HTMX + Tailwind + SQLite | Default Walmart stack, no build step |
| 2026-06-26 | Venv in %LOCALAPPDATA% not OneDrive | Avoids OneDrive sync + hardlink issues |
| 2026-06-26 | SQLite as local cache | Fast reads, no external DB needed, BQ is source of truth |
| 2026-06-26 | Service account key auto-detected from project root | Zero-config for future users |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main page (index.html) |
| GET | `/roster/future?team=` | Future schedule matrix partial |
| GET | `/roster/historical?team=` | Historical matrix partial |
| GET | `/summary?team=&scope=future|historical` | Summary partial |
| GET | `/export/csv?scope=&team=` | Download CSV |
| GET | `/export/excel?scope=&team=` | Download Excel |
| GET | `/export/pdf?scope=&team=` | Download PDF |
| POST | `/api/refresh` | Trigger manual GCP refresh |
| GET | `/api/status` | Get last refresh status |

---

*Last updated: 2026-06-26 | Session 3 end | Updated by: Kratos (code-puppy-4e37f8)*
*Next session: Corrections and enhancements from Venkat*
