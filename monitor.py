"""Anne Frank House ticket monitor.

Checks the public ticket calendar API and sends an ntfy.sh push notification
when any watched date becomes available.

Env vars:
  WATCH_DATES  comma-separated dates or ranges, e.g. "2026-10-10..2026-10-12,2026-10-20"
  NTFY_TOPIC   ntfy.sh topic name (keep it long and random)

Usage:
  python monitor.py            check and notify on newly available dates
  python monitor.py --dry-run  print availability, no notification, no state change
  python monitor.py --test     send a test notification
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

API = "https://tickets.annefrank.org/api/v1/calendardates/tickets/{start}/{end}/en-US"
SHOP_URL = "https://tickets.annefrank.org/en-US/tickets"
STATE_FILE = Path(__file__).with_name("state.json")
DEFAULT_WATCH = "2026-10-10..2026-10-12"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def parse_dates(spec):
    dates = set()
    for part in filter(None, (p.strip() for p in spec.split(","))):
        if ".." in part:
            a, b = (dt.date.fromisoformat(x.strip()) for x in part.split(".."))
            while a <= b:
                dates.add(a)
                a += dt.timedelta(days=1)
        else:
            dates.add(dt.date.fromisoformat(part))
    return dates


def fetch_calendar(start, end):
    url = API.format(start=start.isoformat(), end=end.isoformat())
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return {d["capacityDate"]: d for d in json.load(resp)}


def notify(topic, title, message):
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": "high", "Tags": "ticket", "Click": SHOP_URL},
    )
    urllib.request.urlopen(req, timeout=20).read()


def load_state():
    try:
        return set(json.loads(STATE_FILE.read_text())["notified"])
    except (FileNotFoundError, ValueError, KeyError):
        return set()


def save_state(notified):
    STATE_FILE.write_text(json.dumps({"notified": sorted(notified)}, indent=2))


def main():
    args = set(sys.argv[1:])
    topic = os.environ.get("NTFY_TOPIC", "").strip()

    if "--test" in args:
        if not topic:
            sys.exit("NTFY_TOPIC is not set")
        notify(topic, "Anne Frank monitor test", "Notifications are working.")
        print(f"Test notification sent to topic '{topic}'")
        return

    today = dt.date.today()
    watch = {d for d in parse_dates(os.environ.get("WATCH_DATES") or DEFAULT_WATCH) if d >= today}
    if not watch:
        print("No future dates to watch; nothing to do.")
        return

    calendar = fetch_calendar(today, max(watch))
    available = set()
    for d in sorted(watch):
        entry = calendar.get(d.isoformat())
        if entry is None:
            status = "not released"
        elif entry.get("isAvailable"):
            status = "AVAILABLE"
            available.add(d.isoformat())
        else:
            status = "sold out" if entry.get("isSoldOut") else "unavailable"
        print(f"{d}  {status}")

    if "--dry-run" in args:
        return

    notified = load_state()
    new = available - notified
    if new:
        if not topic:
            sys.exit("Tickets available but NTFY_TOPIC is not set")
        dates = ", ".join(sorted(new))
        notify(topic, "Anne Frank tickets available!", f"Tickets available for: {dates}\nTap to open the ticket shop.")
        print(f"Notified: {dates}")
    # Keep only dates still available, so a date that sells out and frees up again re-notifies.
    save_state(notified & available | new)


if __name__ == "__main__":
    main()
