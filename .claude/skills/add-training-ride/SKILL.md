---
name: add-training-ride
description: Add a ride or an event to the training calendar at /training, linking to its RideWithGPS route. Use when the user wants to put a ride, workout, race, tour, or multi-day event on the training calendar — for example "add Saturday's ride to the calendar", "put this route on the training plan", "add the Tower 300 in September", or when they paste a ridewithgps.com/routes/... URL and want it scheduled.
---

# Add a ride or event

Adds one entry to the JSON block inside [training/index.html](../../../training/index.html).
Never hand-edit that block when this skill applies — the script validates dates,
prevents duplicates, and keeps the list sorted.

## 1. Collect the details

Required:

| Field | Notes |
| --- | --- |
| `--date` | `YYYY-MM-DD`. Resolve relative dates ("Saturday", "next Tuesday") against today's date before calling. |
| `--title` | Short name, for example `North Hill Loop`. |

Optional:

| Field | Notes |
| --- | --- |
| `--end` | `YYYY-MM-DD`. Only for something spanning several days. "September 24th through 29th" means `--date 2026-09-24 --end 2026-09-29`. Omit for a single day. |
| `--kind` | `ride` for a training ride, `event` for a race, tour, or multi-day happening. Defaults to `ride`. Infer it from how the user describes the entry rather than asking. |
| `--url` | RideWithGPS route URL. |
| `--distance` | Free text: `42 mi`, `70 km`. |
| `--elevation` | Free text: `2,100 ft`. |
| `--start` | 24-hour `HH:MM`. The page renders it as `7:30 am`. |
| `--location` | Start location or meeting point. |
| `--notes` | One or two sentences: the workout, what to bring, regroup plan. |

If the user gives a RideWithGPS URL without a name, fetch the page and read the
route name from its `<title>`. Distance and elevation are rendered client-side
on RideWithGPS and are **not** in the fetched HTML.

**Never invent distance, elevation, or notes.** Ask the user, or leave the field
out — the card reads fine without it, and a wrong number published on the site is
worse than a missing one.

Ask only for what's genuinely missing. A date and a title are enough to proceed;
don't interrogate the user for every optional field.

## 2. Add it

A single-day ride:

```bash
python3 .claude/scripts/training_events.py add \
  --date 2026-08-27 \
  --title "North Hill Loop" \
  --url "https://ridewithgps.com/routes/56866408" \
  --kind ride
```

A multi-day event:

```bash
python3 .claude/scripts/training_events.py add \
  --date 2026-09-24 \
  --end 2026-09-29 \
  --title "Tower 300" \
  --url "https://ridewithgps.com/routes/56778774" \
  --kind event
```

Run it from the repository root. The script prints the entry it added.

A multi-day entry shows on every day it covers in the month grid, and its agenda
card shows the range and a day count.

## 3. Confirm

Show the user what was added and mention it appears at `/training`. Check with:

```bash
python3 .claude/scripts/training_events.py list
```

Leave the change uncommitted unless the user asks you to commit or push —
pushing to `main` publishes it to GitHub Pages.

## Related

- To point an entry at live tracking once it starts, use the
  `swap-in-spot-tracker` skill.
- To delete one: `python3 .claude/scripts/training_events.py remove --match "2026-09-24:tower"`
