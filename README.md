# kinokalender

ICS-Kalender für deutsche Kinostarts, generiert aus dem [IMDb DE Coming-Soon Calendar](https://www.imdb.com/calendar/?region=DE&type=MOVIE).

## Subscribe

- **iCal/ICS:** `https://raw.githubusercontent.com/isntfunny/kinokalender/main/kinostarts.ics`
- **Webcal:** `webcal://raw.githubusercontent.com/isntfunny/kinokalender/main/kinostarts.ics`

## Event format

Each event in the ICS carries:

| Field | Example | Notes |
|---|---|---|
| `SUMMARY` | `🍿 The Devil Wears Prada 2` | Display title with emoji prefix. |
| `DTSTART` | `20260430` | German theatrical release date (all-day). |
| `UID` | `tt33612209-2026-04-30@imdb-de-calendar` | Stable across runs. |
| `URL` | `https://www.imdb.com/title/tt33612209/` | IMDB id parseable from this. |
| `DESCRIPTION` | `IMDB: tt33612209\nPoster: https://m.media-amazon.com/...` | Structured `Key: Value` lines. |

## Run locally

```bash
pip install -r requirements.txt
camoufox fetch          # one-time browser download (~80 MB)
python kinostarts.py
```

Output: `kinostarts.ics` in the current directory.

## How it works

IMDb's calendar page is a Next.js app behind an Amazon WAF JS-challenge. We use [Scrapling](https://github.com/D4Vinci/Scrapling)'s `StealthyFetcher` (camoufox-backed) to render the page, then extract the `__NEXT_DATA__` JSON blob — no DOM scraping needed. The JSON already groups movies by release date and includes the IMDB id, title, and poster URL natively.

## Update cadence

GitHub Actions runs the scraper daily at 06:00 UTC and commits the regenerated `kinostarts.ics` if anything changed.

## History

This repo previously generated the calendar from filmstarts.de via `requests` + `BeautifulSoup`. That source had no IMDB id, so consumers had to do a separate lookup per movie. The IMDb calendar carries the IMDB id natively, which is the main reason for the switch.
