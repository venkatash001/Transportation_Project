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
| 11 | 2026-06-29 | Pre-flight check on restart. Server confirmed running (PID 23056). DB: 81,288 rows / 1,033 agents. BQ refresh last ran 2026-06-26. All packages OK. Excel master upload confirmed as Monday priority. | b98f23e | Kratos |
| 12 | 2026-06-30 | **agent_master feature shipped.** HeadCount Excel (MAA + BLR) parsed and loaded as source of truth. 1,619 agents in agent_master. All roster queries LEFT JOINed to master. COALESCE: Excel wins over BQ for WIN ID, Name, LOB, Role, L1/L2 Manager. Admin UI at /admin/master. Yellow "Master Data" nav button added. | 0abbdf6 | Kratos |
| 13 | 2026-06-30 | Session recap + memory recall. Confirmed last commit (0abbdf6) and full project state. Session log updated. | 9d0311b | Kratos |
| 14 | 2026-06-30 | **Performance fix + bug hunt.** Diagnosed 3 bugs: (1) Override matrix blank - INNER JOIN killing all future agents. (2) Adhoc preview 403 - session cookie lost between navigations. (3) Tab slowness >30s - LOWER(TRIM()) in SQL JOIN defeats all indexes on 83k rows. Fixes applied: rewrote get_all_agents() + get_agents_for_manager() to query agent_master (1,619 rows) directly. Replaced INNER JOIN SQL enrichment in get_roster_for_range() with Python dict lookup (get_master_lookup()). Override route now passes l1 filter to DB query instead of Python filtering 83k rows. New server: PID 33724/29308. Fixes applied, testing deferred to tomorrow. | -- | Kratos |

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

### Master Data (agent_master) — Added Session 12
- [x] `agent_master` SQLite table (UNIQUE login_id COLLATE NOCASE)
- [x] HeadCount Excel parser (`app/master.py`): reads `HeadCount_Base` sheet from both MAA and BLR files
- [x] login_id stored lowercase to match BigQuery format
- [x] float WIN IDs (e.g. `231505622.0`) cleaned to int string automatically
- [x] Auto-load on startup if `agent_master` is empty — loads both MAA + BLR from OneDrive
- [x] All roster queries LEFT JOIN `agent_master`; COALESCE: Excel wins over BQ
- [x] `get_teams()` now uses clean LOB names from master (e.g. `Account Review` not `Account_Review_NST_WMT_IN`)
- [x] Override Editor and Ad-Hoc Roster both use enriched agent data from master
- [x] Admin UI: `/admin/master` — stats dashboard + drag-drop upload + OneDrive reload button
- [x] **1,619 agents loaded** (MAA: 942, BLR: 679, 2 overlap)

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
|   |-- master.py                       HeadCount Excel parser + auto-loader (NEW - Session 12)
|   |-- routes/
|   |   |-- __init__.py
|   |   |-- roster.py                   /roster/future, /roster/historical
|   |   |-- summary.py                  /summary
|   |   |-- export.py                   /export/csv, /export/excel, /export/pdf
|   |   |-- admin.py                    /admin/overrides, /admin/adhoc, /admin/master
|   |-- templates/
|   |   |-- index.html                  Main UI
|   |   |-- login.html                  Admin login page
|   |   |-- partials/
|   |   |   |-- roster_table.html       Matrix table partial
|   |   |   |-- summary_table.html      Summary partial
|   |   |-- admin/
|   |       |-- overrides.html          Override Editor page
|   |       |-- adhoc.html              Ad-Hoc Roster page
|   |       |-- master_upload.html      Master Data upload + stats page (NEW - Session 12)
|   |-- static/
|       |-- style.css                   Sticky columns, scrollbar, HTMX spinner
|-- data/
    |-- roster.db                       SQLite cache (gitignored, auto-created)
```

---

## Open Items / Next Steps (Monday)

| # | Issue | Status | Plan |
|---|-------|--------|------|
| 1 | WIN_NBR / L1_Manager still blank for many agents |  DONE | Excel master file (agent_master table) is now source of truth. 1,619 agents loaded. |
| 2 | `SCHED_ACTV_DUR_MIN_QTY` is NULL in BQ source | KNOWN | Column is NULL in the table -- using max-duration deduplication still works correctly. No action needed. |
| 3 | Manual fixes get wiped on BQ refresh |  RESOLVED | Upsert now uses CASE WHEN -- blank incoming values never overwrite existing good values. |
| 4 | More agents with incorrect Role and Team |  DONE | Fixed by agent_master Excel source of truth (Session 12). |
| 5 | AI Launchpad hosting | PLANNED | Use launchpad sub-agent to deploy. Dockerfile needed. Cloud SQL for DB. Cloud SQL = same schema, change one line in config.py. |
| 6 | Excel master file upload UI |  DONE | Built in Session 12 — /admin/master with drag-drop upload + OneDrive auto-reload. |
| 7 | GCP credentials (for production) | OPEN | Service account key OR gcloud ADC needed. See GCP_Auth_Setup.md. |
| 8 | Override matrix blank after HC file | IN PROGRESS | Root cause: INNER JOIN + LOWER(TRIM()) on 83k rows killed index. Fix applied: get_roster_for_range() now does Python enrichment via master dict. Test tomorrow. |
| 9 | Tab navigation too slow (>30s) | IN PROGRESS | Root cause: same SQL JOIN issue. Fix applied: get_roster_for_range() now: fast date scan + O(n) Python dict lookup. Test tomorrow. |
| 10 | Adhoc preview 403 Forbidden | RESOLVED | Root cause: session cookie lost - user was not logged in. After login it works correctly. No code change needed. |

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

## HeadCount Excel Column Mapping (agent_master, 0-indexed)

*Sheet: `HeadCount_Base` | Files: `Head_Count_MAA.xlsx` (942) + `Head_Count_BLR.xlsx` (679)*

| Col Index | Excel Header | App Field | Notes |
|-----------|-------------|-----------|-------|
| [01] | User ID | `login_id` | KEY — stored lowercase |
| [02] | WIN ID | `win_id` | float cleaned to int string (231505622.0 → "231505622") |
| [09] | First Name | — | Combined with Last Name |
| [10] | Last Name | — | Combined with First Name |
| [11] | Associate Name (WD) | `full_name` | Used directly if present |
| [12] | Role | `role` | e.g. "Fraud Analyst" |
| [13] | Status | `status` | e.g. "Active" |
| [15] | LOB | `lob` | Clean names e.g. "Account Review" |
| [29] | Location | `location` | e.g. "MAA" / "BLR" |
| [52] | Team Lead Name | `l1_manager` | |
| [53] | Team Manager Name | `l2_manager` | |
| [54] | Ops Manager Name | `ops_manager` | |

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
| GET | `/admin/master` | Admin | Master Data stats + upload page |
| POST | `/admin/master` | Admin | Upload HeadCount Excel file |
| POST | `/admin/master/reload-defaults` | Admin | Reload master data from OneDrive (MAA + BLR) |

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
| 2026-06-30 | agent_master table as source of truth for all agent metadata | BQ CS_AGNT data quality too poor (NULLs, multi-row, wrong LOB names); HeadCount Excel is authoritative |
| 2026-06-30 | COALESCE: Excel wins over BQ on all metadata fields | Ensures clean names, correct teams, and valid WIN IDs in every UI view |
| 2026-06-30 | login_id stored lowercase in agent_master | Matches BQ format for case-insensitive JOIN |
| 2026-06-30 | Auto-load on startup if agent_master is empty | Zero-config startup - no manual step needed after fresh install |
| 2026-06-30 | Eliminate SQL JOIN in get_roster_for_range() | LOWER(TRIM()) on 83k rows kills SQLite indexes and causes >30s queries. Solution: load agent_master as Python dict (1,619 rows), do fast date-indexed roster scan, enrich rows in Python with O(n) dict lookup. Zero join overhead. |
| 2026-06-30 | get_all_agents() and get_agents_for_manager() query agent_master directly | Avoids scanning 83k roster rows for agent lists. 1,619 agent_master rows is trivially fast. vcc_id resolved via a cheap MIN() subquery on roster. |

---

*Last updated: 2026-06-30 | Session 14 | Updated by: Kratos (code-puppy-c9f12d)*
*Status: Performance fix IN PROGRESS. Fixes applied to db.py + admin.py, not yet tested end-to-end. Resume tomorrow.*
