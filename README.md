# Calendar Deadline Tracker

A small scheduled job that watches a macOS Calendar for anything starting within the next N days and surfaces only what's *new* - once an event has been flagged, it's remembered in a state file and never repeated, so a job that runs every morning doesn't re-announce the same deadline for two weeks straight.

## How it works

- `calendar_lib.py` is a thin AppleScript bridge to Calendar.app - add events, list events in a date range, create/delete calendars. All-day events only, handled correctly against Calendar.app's exclusive end-date convention for multi-day events.
- `check_deadlines.py` lists upcoming events in a configurable window (default 14 days), diffs against a small JSON state file of what's already been flagged, prints only the new ones, and updates the state file.

## Why a state file instead of just listing events every time

The point of a scheduled check is to flag *changes*, not to re-read the same calendar entry out loud every single day until the event passes. The state file is the memory that makes "tell me what's new" actually mean new.

## Testing

Both the date ("as of") and the calendar/state file are injectable via flags specifically so this can be tested against a disposable calendar and state file without touching the real one:

```bash
python3 check_deadlines.py --as-of 2026-11-01 --calendar Test --state /tmp/test-state.json
```

## Usage

```bash
python3 check_deadlines.py                  # real run, real calendar, default 14-day window
```

Schedule it with cron or launchd for a daily check.

## Stack

Python · AppleScript (via `osascript`) · macOS Calendar.app

---
Part of a small portfolio of tested automation/AI builds — see [ParishSynthMind](https://github.com/ParishSynthMind) for the others.
