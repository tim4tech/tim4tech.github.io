#!/usr/bin/env python3
"""Manage the training rides embedded in training/index.html.

The calendar page keeps its events in a single JSON block:

    <script type="application/json" id="training-events"> [ ... ] </script>

This script is the safe way to edit that block. It validates input, keeps the
list sorted by date and time, and rewrites the block as formatted JSON without
touching anything else on the page.

Usage:
    training_events.py list [--all]
    training_events.py add --date YYYY-MM-DD --title TITLE [--end YYYY-MM-DD] [options]
    training_events.py track  --match QUERY --tracker URL
    training_events.py untrack --match QUERY
    training_events.py remove --match QUERY

QUERY selects an existing entry. It matches a date (2026-09-24, including any
date inside a multi-day entry), a case-insensitive substring of the title, or
"DATE:substring" for both. The command fails rather than guessing when a query
matches more than one entry.
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAGE = REPO / "training" / "index.html"

BLOCK = re.compile(
    r'(<script type="application/json" id="training-events">)(.*?)(</script>)',
    re.DOTALL,
)

KINDS = ["ride", "event"]

# Written in this order so the JSON block stays readable.
FIELD_ORDER = [
    "date", "end", "title", "url", "kind", "distance",
    "elevation", "start", "location", "notes", "tracker",
]


def die(msg):
    sys.exit("error: " + msg)


# --------------------------------------------------------------------------
# load / save
# --------------------------------------------------------------------------

def load():
    if not PAGE.exists():
        die("calendar page not found at %s" % PAGE)
    src = PAGE.read_text(encoding="utf-8")
    m = BLOCK.search(src)
    if not m:
        die("could not find the training-events JSON block in %s" % PAGE)
    try:
        events = json.loads(m.group(2))
    except json.JSONDecodeError as e:
        die("the training-events block is not valid JSON: %s" % e)
    if not isinstance(events, list):
        die("the training-events block must contain a JSON array")
    return src, m, events


def save(src, m, events):
    events.sort(key=lambda e: (e.get("date", ""), e.get("start") or ""))

    ordered = []
    for e in events:
        row = {k: e[k] for k in FIELD_ORDER if e.get(k) not in (None, "")}
        # Keep any field this script does not know about.
        for k, v in e.items():
            if k not in row and not k.startswith("_") and v not in (None, ""):
                row[k] = v
        ordered.append(row)

    body = "\n" + json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"
    out = src[:m.start(2)] + body + src[m.end(2):]
    PAGE.write_text(out, encoding="utf-8")


# --------------------------------------------------------------------------
# validation / matching
# --------------------------------------------------------------------------

def valid_date(s):
    try:
        datetime.date.fromisoformat(s)
    except ValueError:
        die("date must be YYYY-MM-DD and a real date, got %r" % s)
    return s


def valid_time(s):
    if s is None:
        return None
    if not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", s):
        die("start must be 24-hour HH:MM, got %r" % s)
    h, m = s.split(":")
    return "%02d:%s" % (int(h), m)


def valid_url(s, label):
    if s is None:
        return None
    if not re.match(r"https?://", s):
        die("%s must start with http:// or https://, got %r" % (label, s))
    return s


def describe(e):
    when = e["date"]
    if e.get("end") and e["end"] != e["date"]:
        when += " to " + e["end"]
    bits = [when, e["title"]]
    if e.get("start"):
        bits.append(e["start"])
    return "  ".join(bits)


def find(events, query):
    """Return the index of the one ride matching query, or exit."""
    date_part, _, text_part = query.partition(":")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_part):
        date_part, text_part = None, query

    hits = []
    for i, e in enumerate(events):
        # ISO dates compare correctly as strings, so this also catches a date
        # falling inside a multi-day entry.
        if date_part and not (e["date"] <= date_part <= e.get("end", e["date"])):
            continue
        if text_part and text_part.lower() not in e.get("title", "").lower():
            continue
        hits.append(i)

    if not hits:
        die("no ride matches %r. Run `list --all` to see what is on the calendar." % query)
    if len(hits) > 1:
        lines = "\n".join("  " + describe(events[i]) for i in hits)
        die("%r matches %d rides. Narrow it down, for example "
            "\"2026-09-24:tower\".\n%s" % (query, len(hits), lines))
    return hits[0]


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_list(args):
    _, _, events = load()
    today = datetime.date.today().isoformat()
    shown = 0
    for e in events:
        if not args.all and e.get("end", e["date"]) < today:
            continue
        flag = "  [live]" if e.get("tracker") else ""
        print(describe(e) + flag)
        shown += 1
    if shown == 0:
        print("no rides" if args.all else "no upcoming rides (use --all to include past ones)")


def cmd_add(args):
    src, m, events = load()

    date = valid_date(args.date)
    end = valid_date(args.end) if args.end else None
    if end and end < date:
        die("--end (%s) falls before --date (%s)" % (end, date))
    if end == date:
        end = None

    event = {
        "date": date,
        "end": end,
        "title": args.title.strip(),
        "url": valid_url(args.url, "--url"),
        "kind": args.kind,
        "distance": args.distance,
        "elevation": args.elevation,
        "start": valid_time(args.start),
        "location": args.location,
        "notes": args.notes,
    }
    event = {k: v for k, v in event.items() if v not in (None, "")}

    for e in events:
        if e["date"] == date and e["title"].lower() == event["title"].lower():
            die("a ride called %r already exists on %s. Use `remove` first, or "
                "pick a different title." % (e["title"], date))

    events.append(event)
    save(src, m, events)
    print("added: " + describe(event))


def cmd_track(args):
    src, m, events = load()
    i = find(events, args.match)
    tracker = valid_url(args.tracker, "--tracker")

    events[i]["tracker"] = tracker
    save(src, m, events)

    e = events[i]
    print("tracking: " + describe(e))
    print("  live link:      " + tracker)
    if e.get("url"):
        print("  planned route:  " + e["url"] + "  (kept as a secondary link)")
    else:
        print("  no RideWithGPS route was set on this ride")


def cmd_untrack(args):
    src, m, events = load()
    i = find(events, args.match)
    if not events[i].pop("tracker", None):
        die("%s has no tracker link to remove" % describe(events[i]))
    save(src, m, events)
    print("tracker removed: " + describe(events[i]))


def cmd_remove(args):
    src, m, events = load()
    i = find(events, args.match)
    gone = events.pop(i)
    save(src, m, events)
    print("removed: " + describe(gone))


# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Manage training rides on the calendar page.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="show rides on the calendar")
    pl.add_argument("--all", action="store_true", help="include past rides")
    pl.set_defaults(fn=cmd_list)

    pa = sub.add_parser("add", help="add a training ride")
    pa.add_argument("--date", required=True, help="YYYY-MM-DD")
    pa.add_argument("--end", help="YYYY-MM-DD, for an entry spanning several days")
    pa.add_argument("--title", required=True)
    pa.add_argument("--url", help="RideWithGPS route URL")
    pa.add_argument("--kind", choices=KINDS, default="ride")
    pa.add_argument("--distance", help='free text, for example "42 mi"')
    pa.add_argument("--elevation", help='free text, for example "2,100 ft"')
    pa.add_argument("--start", help="24-hour HH:MM")
    pa.add_argument("--location")
    pa.add_argument("--notes")
    pa.set_defaults(fn=cmd_add)

    pt = sub.add_parser("track", help="point a ride at a SPOT tracker, keeping its route")
    pt.add_argument("--match", required=True, help="date, title substring, or DATE:substring")
    pt.add_argument("--tracker", required=True, help="live tracking URL")
    pt.set_defaults(fn=cmd_track)

    pu = sub.add_parser("untrack", help="remove a ride's tracker link")
    pu.add_argument("--match", required=True)
    pu.set_defaults(fn=cmd_untrack)

    pr = sub.add_parser("remove", help="delete a ride")
    pr.add_argument("--match", required=True)
    pr.set_defaults(fn=cmd_remove)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
