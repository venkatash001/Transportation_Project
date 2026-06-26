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
| **Server**     | http://0.0.0.0:8501 (team access: http://10.93.60.49:8501) |
| **Venv**       | `%LOCALAPPDATA%\transport_roster_venv` (Python 3.13.5) |
| **Launcher**   | Double-click `Run Me.bat` or desktop shortcut |

---

## Tech Stack (Confirmed)

| Layer          | Technology |
|----------------|------------|
| Backend        | Python 3.13 + FastAPI + APScheduler |
| Frontend       | HTMX + Tailwind CSS (CDN) |
| Database       | SQLite (local cache -- `data/roster.db`) |
| Data Source    | Google BigQuery (`wmt-cc-datasphere-prod`) |
| Exports        | openpyxl (Excel), fpdf2 (PDF), csv stdlib |
| Auth           | HMAC cookie sessions (Viewer default / Admin login) |
| Version Control| Git 2.45.2 + GitHub (venkatash001/Transportation_Project) |
| Icon           | Pillow-generated branded .ico (7 sizes, 16px-256px) |

---

## Session History

| # | Date | Summary | Commit | Agent |
|---|------|---------|--------|-------|
| 1 | 2026-06-26 | Project kickoff. Verified SharePoint folder + GitHub access. Session log created. | -- | Kratos |
| 2 | 2026-06-26 | Full web application built (20 files). Server launched at port 8501. All imports verified OK. 81,288 BQ records loaded. | 34149c5 | Kratos |
| 3 | 2026-06-26 | Fixed gcp.py bug, added GCP auth guide, installed google-cloud-bigquery. | 34149c5 | Kratos |
| 4 | 2026-06-26 | 4 enhancements: SQL Open-activity filter, Admin/Viewer auth, Override Editor, Ad-Hoc Roster generator. | 34149c5 | Kratos |
| 5 | 2026-06-26 | Column mapping fix: LOGIN_ID as User ID, WIN_NBR as WIN ID, correct Full Name, L1/L2 Manager, Team. | 699016d | Kratos |
| 6 | 2026-06-26 | Access setup: HOST changed to 0.0.0.0. All 26 files pushed to GitHub. Desktop shortcut + branded icon created. | 699016d | Kratos |
| 7 | 2026-06-26 | AI Launchpad business justification written + saved as text file. | 0fdf993 | Kratos |
| 8 | 2026-06-26 | WIN_NBR / L1_Manager gaps: two-pass BQ metadata strategy implemented in gcp.py. backfill_meta.py ran on 1033 agents. | 0fdf993 | Kratos |
| 9 | 2026-06-26 | Root cause diagnosed: TRIM(INT64) SQL error + upsert overwriting good values. Fixed SQL CTE, fixed upsert CASE logic, manual_fix.py for known corrections. | 6656321 | Kratos |
| 10 | 2026-06-26 | Next approach agreed: Excel master file upload via Admin UI to populate agent_master table. Deferred to Monday. All saved. | 85191f1+ | Kratos |

---

## Features Implemented (Complete List)

### Core Roster View
- [x] 3-tab UI: Future Schedule (next 30 days) / Historical (last 90 days) / Summary
- [x] Matrix view: sticky identity columns (Login ID, WIN, Name) + scrollable date columns
- [x] Date cells: IST shift times in green (Full day), blue (Half day), or OFF in gray
- [x] Team filter dropdown (dynamic from DB)
- [x] Client-side search by name / login ID / team
- [x] Half-day shift badge `(H)` indicator
- [x] Admin override cells highlighted amber with dot indicator

### Exports
- [x] CSV download (all data, current scope + team filter)
- [x] Excel download (Walmart-styled, freeze panes, colour-coded, override cells amber)
- [x] PDF download (landscape, paginated 14 columns per page)

### Admin Features
- [x] Admin login: `CESINDANALYST / Walmart@00100`
- [x] Viewer role: default, no login required
- [x] Override Editor (`/admin/overrides`): click any cell, pick from shift presets or custom time, add note
- [x] Ad-Hoc Roster (`/admin/adhoc`): select associates, date range, shift, week-off days, preview, export
- [x] Manual GCP Refresh button (Admin only)
- [x] Logout endpoint

### Data Pipeline
- [x] BigQuery SQL with AGNT_BEST CTE (deduplicates CS_AGNT, L1_MGR-populated rows prioritised)
- [x] Two-pass Python fetch: metadata from ALL rows per VCC_ID, schedule from longest-duration row per date
- [x] SQLite upsert: CASE WHEN logic -- blank incoming value never overwrites existing good value
- [x] APScheduler: auto-refresh every 2 hours
- [x] Refresh log table (status, record count, timestamp per run)
- [x] `manual_fix.py`: direct SQLite patch for known metadata corrections
- [x] `backfill_meta.py`: scans existing DB rows to fill gaps from sibling rows

### Infrastructure
- [x] Desktop shortcut: `CES IND Transport Roster.lnk` on OneDrive Desktop
- [x] Branded icon: `transport_roster.ico` (Walmart blue + yellow spark, 7 sizes)
- [x] `create_icon.py`: regenerate icon anytime
- [x] `Run Me.bat`: one-click start (venv, install, launch, browser open)
- [x] HOST = 0.0.0.0: accessible from any machine on Walmart network at http://10.93.60.49:8501
- [x] AI Launchpad business justification: `AI_Launchpad_Business_Justification.txt`

---

## Current File Inventory

```
28.Transportation_Roster_Project/
|-- Run Me.bat                          One-click launcher
|-- SESSION_LOG.md                      This file
|-- GCP_Auth_Setup.md                   GCP credentials guide
|-- AI_Launchpad_Business_Justification.txt
|-- requirements.txt                    Python dependencies
|-- .gitignore
|-- transport_roster.ico                Branded app icon (7 sizes)
|-- create_icon.py                      Icon generator (Pillow)
|-- backfill_meta.py                    Backfill WIN/L1 from sibling DB rows
|-- manual_fix.py                       Direct SQLite patch for known corrections
|-- verify_backfill.py                  Verify backfill results
|-- debug_agent.py                      Debug specific agent in DB
|-- find_row620.py                      Find agent at matrix row N
|-- check_refresh_log.py               Check BQ refresh history
|-- inspect_excels.py                   Inspect Excel file column structures
|-- Sample Roster.xlsx                  Reference template (Excel format)
|-- query/
|   |-- agent_schedule_query.sql        BigQuery SQL (AGNT_BEST CTE)
|-- app/
|   |-- main.py                         FastAPI entry + APScheduler
|   |-- config.py                       Paths, port, windows, credentials
|   |-- db.py                           SQLite CRUD (init, upsert, query)
|   |-- gcp.py                          BigQuery fetch + two-pass metadata
|   |-- matrix.py                       Matrix + summary builder
|   |-- refresh.py                      GCP->SQLite orchestrator
|   |-- auth.py                         HMAC session auth
|   |-- routes/
|   |   |-- __init__.py
|   |   |-- roster.py                   /roster/future, /roster/historical
|   |   |-- summary.py                  /summary
|   |   |-- export.py                   /export/csv, /export/excel, /export/pdf
|   |   |-- admin.py                    /admin/overrides, /admin/adhoc
|   |-- templates/
|   |   |-- index.html                  Main UI
|   |   |-- login.html                  Admin login page
|   |   |-- partials/
|   |   |   |-- roster_table.html       Matrix table partial
|   |   |   |-- summary_table.html      Summary partial
|   |   |-- admin/
|   |       |-- overrides.html          Override Editor page
|   |       |-- adhoc.html              Ad-Hoc Roster page
|   |-- static/
|       |-- style.css                   Sticky columns, scrollbar, HTMX spinner
|-- data/
    |-- roster.db                       SQLite cache (gitignored, auto-created)
```

---

## Open Items / Next Steps (Monday)

| # | Issue | Status | Plan |
|---|-------|--------|------|
| 1 | WIN_NBR / L1_Manager still blank for many agents | IN PROGRESS | Excel master file approach -- build Admin Upload UI to load an Excel with correct metadata into a new `agent_master` table. Excel data takes priority over BQ for all metadata fields. |
| 2 | `SCHED_ACTV_DUR_MIN_QTY` is NULL in BQ source | KNOWN | Column is NULL in the table -- using max-duration deduplication still works correctly. No action needed. |
| 3 | Manual fixes get wiped on BQ refresh | RESOLVED | Upsert now uses CASE WHEN -- blank incoming values never overwrite existing good values. |
| 4 | More agents with incorrect Role and Team | NEXT | Will be fixed by the Excel master file approach (Item 1). |
| 5 | AI Launchpad hosting | PLANNED | Use launchpad sub-agent to deploy. Dockerfile needed. Cloud SQL for DB. |
| 6 | Excel master file upload UI | NEXT | Admin UI: upload Excel -> parse -> populate `agent_master` table -> overrides BQ metadata on render. |
| 7 | GCP credentials (for production) | OPEN | Service account key OR gcloud ADC needed. See GCP_Auth_Setup.md. |

---

## BQ Refresh Diagnostics

| Symptom | Root Cause | Fix Applied |
|---------|-----------|-------------|
| 0 rows returned | `TRIM(WIN_NBR)` on INT64 column crashed BQ | Changed to `WIN_NBR > 0` in CTE |
| 0 rows qualified | `SCHED_ACTV_DUR_MIN_QTY` is NULL for all rows | Dropped MIN_DURATION_MINUTES filter to 0 |
| Manual fix wiped on refresh | Upsert used `excluded.field` unconditionally | Changed to CASE WHEN -- blank never overwrites non-blank |
| WIN/L1 blank even after two-pass | CS_AGNT has multiple rows per agent; NULL-WIN group had more BQ rows and "won" | AGNT_BEST CTE deduplicates CS_AGNT to 1 row per VCC_AGNT_ID before join |

---

## Known Correct Agent Data (manual_fix.py KNOWN_FIXES)

| Login ID | WIN Number | L1 Manager | Notes |
|----------|-----------|------------|-------|
| a0s1tiz | 234049562 | MOHAMMED SHARIEF | Verified by Venkat 2026-06-26 |

*Add more here as discovered. Run `manual_fix.py` to apply.*

---

## Column Mapping (BQ -> App)

| App Column | BQ Field | Notes |
|------------|----------|-------|
| User ID (display) | `LOGIN_ID` from CS_AGNT | e.g. a0s1tiz |
| WIN ID | `WIN_NBR` from CS_AGNT | INT64, e.g. 234049562 |
| Full Name | `FIRST_NM + ' ' + LAST_NM` | Concat from CS_AGNT |
| Team | `SITE_NM` from CS_AGNT_SCHED | |
| Role | `AGNT_PROFL_NM` from CS_AGNT | |
| L1 Manager | `LVL1_MGR_LOGIN_NM` from CS_AGNT | |
| L2 Manager | `LVL2_MGR_LOGIN_NM` from CS_AGNT | |
| Shift Label | `Schedule_StartTime_IST - Schedule_EndTime_IST` | Formatted to 12h IST |
| Internal Key | `VCC_ID` (AGNT_ACCT_ID) | Used for DB uniqueness, not displayed |

---

## Admin Credentials

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Admin | CESINDANALYST | Walmart@00100 | Full: refresh, override, ad-hoc |
| Viewer | (no login) | (no login) | View + download only |

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Public | Main page |
| GET | `/roster/future?team=` | Public | Future schedule matrix |
| GET | `/roster/historical?team=` | Public | Historical matrix |
| GET | `/summary?team=&scope=` | Public | Summary tab |
| GET | `/export/csv?scope=&team=` | Public | Download CSV |
| GET | `/export/excel?scope=&team=` | Public | Download Excel |
| GET | `/export/pdf?scope=&team=` | Public | Download PDF |
| GET | `/login` | Public | Admin login page |
| POST | `/login` | Public | Login form submit |
| GET | `/logout` | Public | Clear session |
| POST | `/api/refresh` | Admin | Trigger BQ refresh |
| GET | `/api/status` | Public | Last refresh status |
| GET | `/admin/overrides?l1=` | Admin | Override Editor |
| POST | `/api/admin/override` | Admin | Save override |
| POST | `/api/admin/override/delete` | Admin | Remove override |
| GET | `/admin/adhoc` | Admin | Ad-Hoc Roster page |
| POST | `/admin/adhoc/preview` | Admin | Preview ad-hoc matrix |
| GET | `/admin/adhoc/export` | Admin | Download ad-hoc roster |

---

## Decisions Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-06-26 | All project files in SharePoint OneDrive folder | Central storage + team access |
| 2026-06-26 | GitHub: venkatash001/Transportation_Project | Version control + rollback |
| 2026-06-26 | Tech stack: FastAPI + HTMX + Tailwind + SQLite | Default Walmart stack, no build step |
| 2026-06-26 | Venv in %LOCALAPPDATA% not OneDrive | Avoids OneDrive sync + hardlink issues |
| 2026-06-26 | SQLite as local cache, BQ as source of truth | Fast reads, simple setup |
| 2026-06-26 | HOST = 0.0.0.0 | Team access via IP on Walmart network |
| 2026-06-26 | HMAC cookie auth (no SSO yet) | Simple, no external dependency; upgrade to SSO on Launchpad |
| 2026-06-26 | Upsert CASE WHEN for metadata fields | Protects manually-corrected values from being wiped by blank BQ data |
| 2026-06-26 | Excel master file approach for metadata | BQ CS_AGNT has data quality issues (multiple rows per agent, NULL fields); clean Excel is source of truth |
| 2026-06-26 | Admin UI file upload (not hardcoded path) | Works both locally AND on Launchpad (no local path dependency) |

---

*Last updated: 2026-06-26 | Session 10 end | Updated by: Kratos (code-puppy-4e37f8)*
*Next session: Monday -- Excel master file upload UI + agent_master table*
