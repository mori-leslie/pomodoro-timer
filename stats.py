import json
import os
import tempfile
from datetime import date, datetime

STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")
OBSIDIAN_DIR = os.path.expanduser("~/Documents/Obsidian Vault/Pomodoro")


def _load():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE) as f:
        return json.load(f)


def _save(data):
    dir_ = os.path.dirname(STATS_FILE)
    with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_name = tmp.name
    os.replace(tmp_name, STATS_FILE)


def record_session(focus_minutes: int):
    """Call this when a work session completes."""
    data = _load()
    today = str(date.today())

    if today not in data:
        data[today] = {"sessions": 0, "focus_minutes": 0}

    data[today]["sessions"] += 1
    data[today]["focus_minutes"] += focus_minutes
    _save(data)
    _write_obsidian(data, today, focus_minutes)


def get_today_stats():
    data = _load()
    today = str(date.today())
    entry = data.get(today, {"sessions": 0, "focus_minutes": 0})
    return entry["sessions"], entry["focus_minutes"], _streak(data)


def _streak(data):
    """Count consecutive days with at least one session."""
    streak = 0
    day = date.today()
    while True:
        if str(day) in data and data[str(day)]["sessions"] > 0:
            streak += 1
            day = date.fromordinal(day.toordinal() - 1)
        else:
            break
    return streak


def _write_obsidian(data, today, focus_minutes):
    os.makedirs(OBSIDIAN_DIR, exist_ok=True)
    note_path = os.path.join(OBSIDIAN_DIR, f"{today}.md")

    entry = data[today]
    streak = _streak(data)
    time_str = datetime.now().strftime("%H:%M")

    lines = [
        f"# Pomodoro — {today}",
        "",
        f"- **Sessions completed:** {entry['sessions']}",
        f"- **Focus time:** {entry['focus_minutes']} min",
        f"- **Streak:** {streak} day{'s' if streak != 1 else ''}",
        "",
        "## Session Log",
        "",
    ]

    # Preserve existing log entries before appending new one
    existing_log = []
    if os.path.exists(note_path):
        with open(note_path) as f:
            content = f.read()
        in_log = False
        for line in content.splitlines():
            if line == "## Session Log":
                in_log = True
                continue
            if in_log and line.startswith("- "):
                existing_log.append(line)

    existing_log.append(f"- {time_str} — {focus_minutes} min focus session")
    lines += existing_log

    # Atomic write
    dir_ = os.path.dirname(note_path)
    with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False, suffix=".md") as tmp:
        tmp.write("\n".join(lines) + "\n")
        tmp_name = tmp.name
    os.replace(tmp_name, note_path)
