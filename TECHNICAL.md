# Technical Documentation: RSS-Posts-Gießen.py

## Overview

`RSS-Posts-Gießen.py` is a web scraper that aggregates local news and announcements from multiple Gießen-area websites into a single Atom feed (`atom.xml`). It also generates per-source RSS files grouped by hostname.

## Dependencies

| Library | Role |
|---|---|
| `requests` | HTTP GET requests to scraped URLs |
| `bs4` (BeautifulSoup) | HTML parsing for scraped pages |
| `feedgen` | Generating Atom/RSS XML output |
| `feedparser` | Reading existing `atom.xml` to preserve `pubDate` across runs |
| `docopt` | CLI argument parsing (`-f`, `--force-regenerate`, `--offline`, `--skip`) |
| `pandas` | Reading `conf/deleted.csv` (blocklist of URLs to exclude) |
| `pytz` | Timezone localization (Europe/Berlin) |

## Architecture

### Entry Point & CLI

```
docopt(__doc__)  →  arguments dict
  -f <XML-FILE>          output file (default: atom.xml)
  --force-regenerate     always write output even if no changes
  --offline              skip HTTP scraping
  --skip                 skip secondary feed sources (e.g. muk.py)
```

### Post Schema

Every scraper produces dicts conforming to this schema:

```python
{
    "title":        str,   # article headline
    "link":         str,   # canonical URL
    "date-posted":  datetime (tz-aware, Europe/Berlin),
    "date-raw":     str,   # original date string from source
    "author-name":  str,   # human-readable source name
    "author-email": str,   # contact email for source
}
```

### Core Utilities

**`general_scraper(url, mapper, header)`**  
Makes an HTTP GET to `url`, passes `response.text` to `mapper`, returns a list of post dicts. Catches `IndexError` (malformed HTML) and `JSONDecodeError` (bad JSON APIs) — writes raw response to `/tmp/error-out-<hash>` on JSON errors.

**`localdt(str_val, pattern, _fix)`**  
Parses a German-locale date string using `strptime`. If `_fix=True` and the parsed date has no time component and is within 7 days of now, it stamps it with the current hour/minute (avoids midnight timestamps for recent items).

**`_localdt(dt)`**  
Attaches `Europe/Berlin` timezone to an already-parsed `datetime` object.

**`_bs4(s)`**  
Shorthand for `BeautifulSoup(s, features="lxml")`.

### Scraped Sources

| Author Name | URL | Method |
|---|---|---|
| Werkstatt-Kirche | `werkstattkirche.de/neuigkeiten/` | HTML — `article h4 > a`, `time[datetime]` |
| Stadt - Aktuelle Meldungen | `giessen.de/…/Aktuelle-Meldungen/…` | HTML — `article h4`, `small.date` |
| SWG | `swg-konzern.de/presse/archiv/jahr/{year}` | HTML — `.news-list > a`, `time[datetime]` |
| Stadttheater | `stadttheater-giessen.de/…/load_magazine` | JSON API — `data[].title`, `data[].url` |
| Stadt - Amtliche Bekanntmachungen | `giessen.de/…/Amtliche-Bekanntmachungen/` | HTML — `.main-content-area ul > li` |
| Oberhessisches Museum | `giessen.de/…/Oberhessisches-Museum/…` | HTML — `article h4.liste-titel`, `small.date` |
| Stadt - Hitze und Trockenheit | `giessen.de/…/NavID=2874.584.1` | HTML — `section.mitteilungen > article` |
| Universum - Onlinemagazin der JLU | `universum-giessen.com/` | HTML — `article h2`, `div[itemprop=datePublished]` |
| Asta - Uni Gießen | `asta-giessen.de/` | HTML — `article.post`, `time[itemprop=datePublished]` |
| Haus der Nachhaltigkeit | `hdn-giessen.de/aktuelles-2` | HTML — `article.elementor-post` |
| MuK Gießen | `muk-giessen.de/feed/` | Native RSS feed via `feedparser` (`scraper/muk.py`) |

### Feed Generation Pipeline

```
all_posts (list of dicts)
    │
    ▼
import_into_feed(all_posts)
    ├── filter out URLs in conf/deleted.csv
    ├── fg.add_entry() for each post
    │     id        = post["link"]
    │     link/src  = post["link"] + "?utm_source=datengraben.com"
    │     pubDate   = post["date-posted"]
    └── struct_time → datetime conversion for feedparser entries
    │
    ▼
Date preservation loop
    ├── feedparser.parse("./atom.xml")  →  known_posts
    └── for each fg.entry():
            if id in known_posts → restore original pubDate
            else → new post (counted as update_count)
    │
    ▼
Per-hostname feed generation
    ├── group fg.entry() by URL hostname (from entry.id())
    └── for each hostname → write {hostname}.atom.xml
    │
    ▼
Master feed output
    └── fg.atom_file(arguments["-f"])   →   atom.xml (default)
```

### Date Preservation

On each run the script reads the existing `atom.xml` with `feedparser` and restores the original `pubDate` for any entry whose `id` (URL) already exists. This prevents publish dates from shifting on re-scrapes. New entries keep the freshly-parsed date, and `update_count` / `delete_count` track changes.

### scraper/ modules

| File | Status | Purpose |
|---|---|---|
| `scraper/muk.py` | Active | Parses MuK Gießen native RSS feed via `feedparser` |
| `scraper/werkstattkirche.py` | Prototype | Early standalone scraper, not imported |
| `scraper/gi-akt.py` | Prototype | Link exploration for giessen-aktuell.de |
| `scraper/gi-an.py` | Prototype | Link exploration for giessener-anzeiger.de |
| `scraper/gi-allg.py` | Prototype | Link exploration for giessener-allgemeine.de |
| `scraper/gi-oh.py` | Stub | Placeholder for Oberhessische Presse |

### Configuration

- **`conf/deleted.csv`** — one `url` column; entries matching `post["link"]` are silently skipped during feed import.

## Per-Hostname RSS Files

In addition to the combined `atom.xml`, the script generates one Atom file per source hostname (e.g. `werkstattkirche.de.atom.xml`). These are written unconditionally at the end of each run and can be used to subscribe to a single source.
