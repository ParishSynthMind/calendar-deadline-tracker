#!/usr/bin/env python3
"""
Check a macOS Calendar for anything starting within the next N days
(default 14) that hasn't already been flagged, print it, and mark it told
in a state file so it never repeats.

Silent (no output, exit 0) when there's nothing new - designed to run on a
schedule and only make noise when there's actually something to flag.

Usage:
    python3 check_deadlines.py
    python3 check_deadlines.py --as-of 2026-11-01            # testing: pretend "today" is this date
    python3 check_deadlines.py --calendar Test --state /tmp/test-state.json   # testing: isolated calendar/state
"""
import argparse
import datetime
import json
import os
import sys

import calendar_lib

DEFAULT_STATE = os.path.join(os.path.dirname(__file__), "deadlines-notified.json")


def parse_date(s: str) -> datetime.date:
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()


def load_state(path: str) -> dict:
    if not os.path.exists(path):
        return {"notified": {}}
    with open(path) as f:
        return json.load(f)


def save_state(path: str, state: dict) -> None:
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", type=parse_date, default=None)
    parser.add_argument("--calendar", default="Deadlines")
    parser.add_argument("--state", default=DEFAULT_STATE)
    parser.add_argument("--window-days", type=int, default=14)
    args = parser.parse_args()

    today = args.as_of or datetime.date.today()
    window_end_exclusive = today + datetime.timedelta(days=args.window_days + 1)

    events = calendar_lib.list_events(args.calendar, today, window_end_exclusive)
    state = load_state(args.state)

    new_events = [e for e in events if e["uid"] not in state["notified"]]
    new_events.sort(key=lambda e: e["start_date"])

    for e in new_events:
        days_out = (e["start_date"] - today).days
        when = "today" if days_out == 0 else f"in {days_out} day{'s' if days_out != 1 else ''}"
        print(f"DEADLINE: {e['title']} - {e['start_date'].isoformat()} ({when})")
        state["notified"][e["uid"]] = {
            "title": e["title"],
            "start_date": e["start_date"].isoformat(),
            "told_on": today.isoformat(),
        }

    save_state(args.state, state)


if __name__ == "__main__":
    sys.exit(main())
