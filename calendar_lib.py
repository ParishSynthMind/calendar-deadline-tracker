"""
AppleScript bridge to macOS Calendar.app for Neo's Diary job.

All dates are plain datetime.date (no time component — this job only deals
in all-day events). Calendar.app all-day multi-day events use an exclusive
end date (the day AFTER the last day off), so every function here takes
end_exclusive, not the last inclusive day.
"""
import datetime
import subprocess
import tempfile
import os


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _date_block(var_name: str, d: datetime.date) -> str:
    # Set day to 1 before changing year/month to dodge invalid intermediate
    # dates (e.g. currently day=31, target month=Feb).
    return (
        f"set {var_name} to current date\n"
        f"set day of {var_name} to 1\n"
        f"set year of {var_name} to {d.year}\n"
        f"set month of {var_name} to {d.month}\n"
        f"set day of {var_name} to {d.day}\n"
        f"set time of {var_name} to 0\n"
    )


def run_applescript(script: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".applescript")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(script)
        result = subprocess.run(
            ["osascript", path], capture_output=True, text=True, timeout=30
        )
    finally:
        os.remove(path)
    if result.returncode != 0:
        raise RuntimeError(f"AppleScript failed: {result.stderr.strip()}")
    return result.stdout.strip()


def ensure_calendar(name: str) -> None:
    script = f'''
tell application "Calendar"
    if not (exists calendar "{_esc(name)}") then
        make new calendar with properties {{name:"{_esc(name)}"}}
    end if
end tell
'''
    run_applescript(script)


def delete_calendar(name: str) -> None:
    script = f'''
tell application "Calendar"
    if exists calendar "{_esc(name)}" then
        delete calendar "{_esc(name)}"
    end if
end tell
'''
    run_applescript(script)


def add_event(
    calendar_name: str,
    title: str,
    start: datetime.date,
    end_exclusive: datetime.date,
    notes: str = "",
) -> str:
    ensure_calendar(calendar_name)
    script = f'''
tell application "Calendar"
    tell calendar "{_esc(calendar_name)}"
        {_date_block("startDate", start)}
        {_date_block("endDate", end_exclusive)}
        set newEvent to make new event with properties {{summary:"{_esc(title)}", start date:startDate, end date:endDate, allday event:true, description:"{_esc(notes)}"}}
        set theUID to uid of newEvent
    end tell
end tell
return theUID
'''
    return run_applescript(script)


def list_events(calendar_name: str, start: datetime.date, end_exclusive: datetime.date):
    script = f'''
tell application "Calendar"
    {_date_block("rangeStart", start)}
    {_date_block("rangeEnd", end_exclusive)}
    set evts to (every event of calendar "{_esc(calendar_name)}" whose start date ≥ rangeStart and start date < rangeEnd)
    set output to ""
    repeat with e in evts
        set s to start date of e
        set y to (year of s) as integer
        set m to (month of s) as integer
        set d to (day of s) as integer
        set output to output & (summary of e) & "" & character id 1 & (uid of e) & "" & character id 1 & y & "-" & m & "-" & d & character id 10
    end repeat
end tell
return output
'''
    raw = run_applescript(script)
    events = []
    if not raw:
        return events
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("\x01")
        if len(parts) != 3:
            continue
        title, uid, date_str = parts
        y, m, d = (int(x) for x in date_str.split("-"))
        events.append({
            "title": title,
            "uid": uid,
            "start_date": datetime.date(y, m, d),
        })
    return events
