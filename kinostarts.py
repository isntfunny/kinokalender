"""
kinokalender — Generates a Kinostarts ICS calendar from IMDb's German theatrical calendar.

Source:  https://www.imdb.com/calendar/?region=DE&type=MOVIE
Output:  kinostarts.ics

Each ICS event carries:
- SUMMARY:     🍿 <Title>
- DTSTART:     German theatrical release date (all-day)
- UID:         <imdbId>-<yyyy-mm-dd>@imdb-de-calendar
- URL:         https://www.imdb.com/title/<imdbId>/
- DESCRIPTION: structured "Key: Value" lines, parseable by consumers
                 IMDB: tt1234567
                 Poster: https://m.media-amazon.com/...
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, date as DateType
from pathlib import Path
from typing import TypedDict

from ics import Calendar, Event
from scrapling.fetchers import StealthyFetcher


URL = "https://www.imdb.com/calendar/?region=DE&type=MOVIE"
OUTPUT = "kinostarts.ics"

NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
    re.DOTALL,
)


class Movie(TypedDict):
    imdb_id: str
    title: str
    date: DateType
    poster_url: str | None


def fetch_next_data(url: str) -> dict:
    """Open IMDb's calendar in a stealth browser and return the parsed __NEXT_DATA__ JSON."""
    print(f"🔎 Lade {url}", flush=True)
    page = StealthyFetcher.fetch(
        url,
        headless=True,
        network_idle=True,
        timeout=60_000,
        wait_selector="script#__NEXT_DATA__",
    )
    if page.status != 200:
        raise RuntimeError(f"unexpected HTTP status from IMDb: {page.status}")
    html = page.html_content or ""
    match = NEXT_DATA_RE.search(html)
    if not match:
        raise RuntimeError("__NEXT_DATA__ script tag not found in IMDb response")
    return json.loads(match.group(1))


def extract_movies(next_data: dict) -> list[Movie]:
    """Pull movie entries out of the IMDb calendar JSON. TV titles are skipped."""
    groups = (
        next_data.get("props", {})
        .get("pageProps", {})
        .get("groups", [])
    )
    movies: list[Movie] = []
    for group in groups:
        raw_date = group.get("group")
        try:
            release = datetime.strptime(raw_date, "%b %d, %Y").date()
        except (TypeError, ValueError):
            print(f"⚠️ Datum nicht parsebar: {raw_date!r}", flush=True)
            continue
        for entry in group.get("entries", []):
            if entry.get("titleType", {}).get("id") != "movie":
                continue
            imdb_id = entry.get("id")
            title = entry.get("titleText")
            if not imdb_id or not title:
                continue
            image_model = entry.get("imageModel") or {}
            movies.append({
                "imdb_id": imdb_id,
                "title": title,
                "date": release,
                "poster_url": image_model.get("url"),
            })
    return movies


def write_ics(movies: list[Movie], filename: str = OUTPUT) -> None:
    """Write an ICS file with one event per movie."""
    calendar = Calendar()
    for m in movies:
        event = Event()
        event.name = f"🍿 {m['title']}"
        event.begin = m["date"].isoformat()
        event.make_all_day()
        event.uid = f"{m['imdb_id']}-{m['date'].isoformat()}@imdb-de-calendar"
        event.url = f"https://www.imdb.com/title/{m['imdb_id']}/"
        desc_lines = [f"IMDB: {m['imdb_id']}"]
        if m.get("poster_url"):
            desc_lines.append(f"Poster: {m['poster_url']}")
        event.description = "\n".join(desc_lines)
        calendar.events.add(event)
    Path(filename).write_text("".join(calendar), encoding="utf-8")
    print(f"✅ {len(movies)} Filme exportiert nach '{filename}'", flush=True)


def main() -> int:
    try:
        next_data = fetch_next_data(URL)
    except Exception as exc:
        print(f"❌ Fetch fehlgeschlagen: {exc}", file=sys.stderr, flush=True)
        return 1
    movies = extract_movies(next_data)
    if not movies:
        print("⚠️ Keine Filme aus IMDb extrahiert", file=sys.stderr, flush=True)
        return 1
    write_ics(movies)
    return 0


if __name__ == "__main__":
    sys.exit(main())
