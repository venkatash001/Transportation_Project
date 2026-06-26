"""
matrix.py - Transform flat roster rows into matrix and summary structures.
Supports override cells: {label, is_override, note, shift_type}
"""
from datetime import date, timedelta
from collections import defaultdict


def date_range(start: date, end: date) -> list[date]:
    """Return inclusive list of dates from start to end."""
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _make_cell(label: str, shift_type: str = "FULL",
               is_override: bool = False, note: str = "") -> dict:
    return {
        "label":       label,
        "shift_type":  shift_type,
        "is_override": is_override,
        "note":        note,
    }


OFF_CELL = _make_cell("OFF", shift_type="OFF")


def build_matrix(
    rows: list[dict],
    dates: list[date],
    overrides: dict[str, dict[str, dict]] | None = None,
) -> tuple[list[dict], list[date]]:
    """
    Convert flat roster rows to a matrix for template rendering.

    overrides format: {vcc_id: {date_str: {"shift_label": str, "note": str}}}

    Each cell in agent["schedule"] is a dict:
        label, shift_type, is_override, note
    """
    overrides = overrides or {}
    agents: dict[str, dict] = {}
    schedules: dict[str, dict[str, dict]] = defaultdict(dict)

    for row in rows:
        vcc = row.get("vcc_id", "")
        if not vcc:
            continue
        if vcc not in agents:
            agents[vcc] = {
                "vcc_id":     vcc,
                "win_id":     row.get("win_id", ""),
                "login_id":   row.get("login_id", ""),
                "full_name":  row.get("full_name", ""),
                "team_name":  row.get("team_name", ""),
                "role":       row.get("role", ""),
                "l1_manager": row.get("l1_manager", ""),
            }
        d = row.get("schedule_date", "")
        if d:
            schedules[vcc][d] = _make_cell(
                row.get("shift_label", "OFF"),
                shift_type=row.get("shift_type", "FULL"),
            )

    date_strs = [d.isoformat() for d in dates]
    result: list[dict] = []
    for vcc, agent in sorted(agents.items(), key=lambda x: x[1]["full_name"].lower()):
        entry = dict(agent)
        schedule: dict[str, dict] = {}
        for ds in date_strs:
            ovr = overrides.get(vcc, {}).get(ds)
            if ovr:
                schedule[ds] = _make_cell(
                    ovr["shift_label"], is_override=True, note=ovr.get("note", "")
                )
            else:
                schedule[ds] = schedules[vcc].get(ds, OFF_CELL)
        entry["schedule"] = schedule
        result.append(entry)

    return result, dates


def build_summary(
    rows: list[dict],
    dates: list[date],
    overrides: dict[str, dict[str, dict]] | None = None,
) -> list[dict]:
    """Aggregate per-day summary stats, applying overrides."""
    overrides = overrides or {}
    all_agents: set[str] = set()
    daily: dict[str, dict[str, str]] = defaultdict(dict)

    for row in rows:
        vcc = row.get("vcc_id", "")
        d   = row.get("schedule_date", "")
        if vcc and d:
            all_agents.add(vcc)
            daily[d][vcc] = row.get("shift_label", "OFF")

    # Apply overrides to daily map
    for vcc, date_map in overrides.items():
        for ds, ovr in date_map.items():
            all_agents.add(vcc)
            daily[ds][vcc] = ovr["shift_label"]

    total_agents = len(all_agents)
    summary: list[dict] = []
    for d in dates:
        ds        = d.isoformat()
        day_data  = daily.get(ds, {})
        sched_map = {v: lbl for v, lbl in day_data.items() if lbl != "OFF"}
        shifts: dict[str, int] = defaultdict(int)
        for lbl in sched_map.values():
            shifts[lbl] += 1
        summary.append({
            "date":          ds,
            "day_name":      d.strftime("%a"),
            "full_day_name": d.strftime("%A"),
            "scheduled":     len(sched_map),
            "week_off":      max(total_agents - len(sched_map), 0),
            "total_agents":  total_agents,
            "shifts":        dict(sorted(shifts.items())),
        })
    return summary
