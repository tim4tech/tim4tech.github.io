---
name: swap-in-spot-tracker
description: Point a ride or event on the training calendar at a live SPOT / Spotwalla / Garmin tracking link so followers can watch it in real time. Use when the user is about to start or is already on something scheduled and wants the calendar to show live tracking — for example "swap in my SPOT link for today's ride", "make Saturday's ride trackable", "here's the Spotwalla link for the Tower 300".
---

# Swap in a SPOT tracker

Promotes one entry on [training/index.html](../../../training/index.html) to
live tracking. The tracker becomes the entry's primary link and it gets a
**Tracking live** badge; the RideWithGPS route stays on the card as a secondary
link so people can still see the planned course. This works the same for a
single-day ride and for a multi-day event.

## 1. Identify the entry

The `--match` argument accepts:

- a date — `2026-09-24`, or any date falling inside a multi-day entry
- a case-insensitive title substring — `tower`
- both — `2026-09-24:tower`

The script refuses to guess: if a match is ambiguous it lists the candidates and
exits. Widen or narrow the query and try again.

To see what is on the calendar:

```bash
python3 .claude/scripts/training_events.py list
```

Add `--all` to include past rides.

If it isn't on the calendar yet, add it first with the `add-training-ride`
skill, then come back.

## 2. Get the tracking URL

Ask the user for the link if they haven't pasted one. Any `http(s)` URL works —
common sources are:

- Spotwalla — `https://spotwalla.com/tripViewer.php?id=...`
- SPOT shared page — `https://maps.findmespot.com/...`
- Garmin MapShare — `https://share.garmin.com/<name>`

Don't invent or reconstruct a tracking URL. Use exactly what the user provides.

## 3. Swap it in

```bash
python3 .claude/scripts/training_events.py track \
  --match "2026-09-24:tower" \
  --tracker "https://spotwalla.com/tripViewer.php?id=abc123"
```

Run it from the repository root. The script confirms which ride changed, the
live link, and the planned route it kept.

## 4. Publish

Live tracking is only useful if it's actually online, so this is the one case
where committing and pushing promptly matters. Ask before pushing, then:

```bash
git add training/index.html && git commit -m "Add live tracking for the Tower 300" && git push
```

GitHub Pages takes a minute or so to rebuild.

## Afterward

Once it's over, take the badge back off so the card points at the route again:

```bash
python3 .claude/scripts/training_events.py untrack --match "2026-09-24:tower"
```
