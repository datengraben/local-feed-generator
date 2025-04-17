#!/usr/bin/env python
# coding: utf-8

"""RSS Generator

Usage:
    rss.py [options]

Options:
    -f <XML-FILE>           Input feed file in atom xml format [default: atom.xml]
    --force-regenerate, -r  Force generation of atom/rss.xml
    --offline, -o           Skip online scraping (if possible read from sqlite.db)
    --skip, -s              Skip other Feed sources
"""
import datetime
import html
import json
import locale
import random
from json.decoder import JSONDecodeError

import bs4
import feedparser
import pandas as pd
import pytz
import requests

# from networkx import k_components
from docopt import docopt
from feedgen.feed import FeedGenerator

arguments = docopt(__doc__, version="0.0.1")

# Bc we parse german date-time strings, we need german locale
locale.setlocale(
    category=locale.LC_ALL,
    locale="de_DE.utf8",  # Note: do not use "de_DE" as it doesn't work
)

DTNOW = datetime.datetime.now()

# mock browser headers
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua": '"Chromium";v="109", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "cookie": "cookielawinfo-checkbox-necessary=yes; cookielawinfo-checkbox-functional=no; cookielawinfo-checkbox-performance=no; cookielawinfo-checkbox-analytics=no; cookielawinfo-checkbox-advertisement=no; cookielawinfo-checkbox-others=no",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
}


def get_text(url):
    return bs4.BeautifulSoup(
        requests.get(url.strip(), headers=headers, timeout=10).text
    )


def _localdt(dt):
    """Normalizes (/wo microseconds) and localizes dt object"""
    dt.replace(microsecond=0)
    return pytz.timezone("Europe/Berlin").localize(dt)


def localdt(str_val, pattern, _fix=True):
    """Parses into localized dt object"""
    dt = datetime.datetime.strptime(str_val, pattern)
    if (DTNOW - dt).days <= 7 and _fix and dt.hour == 0 and dt.minute == 0:
        dt = dt.replace(hour=DTNOW.hour, minute=DTNOW.minute)
    return _localdt(dt)


def _bs4(s):
    return bs4.BeautifulSoup(s, features="lxml")


# TODO create type of RSS-entry to be returned
def general_scraper(_url, _mapper, _header=headers):
    """
    :param str _url:       url to GET content from, this will be fed into _mapper
    :param lambda _mapper: lambda with only one param body (from response of GET _url) and should return an dict
    :param dict _header:   dict like object to be used for request.get(_url)
    :return: list of rss posts
    """
    resp = requests.get(_url, headers=_header)
    posts = []
    try:
        posts = list(_mapper(resp.text))
    except IndexError as e:
        print("Couldn't parse one item in url '{}'".format(_url))
        print(e)
    except JSONDecodeError as e:
        print("Error while fetching", _url)
        print(resp)
        print(e)
        erroroutfile = "/tmp/error-out-" + str(
            hash("error" + str(random.randint(0, 1000)))
        )
        with open(erroroutfile, "w+") as fp:
            fp.write(resp.text)
            print("Written output to", erroroutfile)
    print("Importiere:", len(posts), " für ", _url)
    return posts


all_posts = []

# # Werkstatt-Kirche
# - [x] fertig

URL = "https://werkstattkirche.de"
POSTS = URL + "/neuigkeiten/"
EVENTS = URL + "/category/veranstaltung"

# scrape posts
all_posts += general_scraper(
    POSTS,
    lambda body: map(
        lambda x: {
            "title": x.select("h2.eael-entry-title > a")[0].text,
            "link": x.select("h2.eael-entry-title > a")[0]["href"],
            "date-raw": x.select("time")[0]["datetime"],
            "date-posted": localdt(x.select("time")[0]["datetime"], "%d. %B %Y"),
            "text": x.select("p")[0].text,
            "author-name": "Werkstatt-Kirche",
            "author-email": "info@werkstattkirche.de",
        },
        _bs4(body).select("article"),
    ),
)

# Gießen.de
# - [x] fertig

year = datetime.date.today().year
url = "https://www.giessen.de/Rathaus/Newsroom/Aktuelle-Meldungen/index.php?ModID=255&object=tx%2C2874.5.1&La=1&NavID=1894.87&text=&kat=8.51&jahr={}&startkat=2874.229".format(
    year
)

all_posts += general_scraper(
    url,
    lambda body: map(
        lambda x: {
            "title": x.select("h4")[0].text,
            "link": "http://giessen.de" + x.select("a")[2]["href"],
            "date-posted": localdt(x.select("small.date")[0].text, "%d.%m.%Y"),
            "date-raw": "",
            "text": "",
            "author-name": "Stadt - Aktuelle Meldungen",
            "author-email": "info@giessen.de",
        },
        _bs4(body).select("article"),
    ),
)


# # Stadtwerke Gießen
#
# Ist sicher in der Gießener Zeug enthalten.
#
# - [x] fertig
#

url = "https://www.swg-konzern.de/presse/archiv/jahr/{}".format(year)
all_posts += general_scraper(
    url,
    lambda body: list(
        map(
            lambda x: {
                "title": x["title"],
                "link": "http://www.swg-konzern.de" + x["href"],
                "text": x.select("div.teaser-text")[0].text,
                "date-raw": x.select("time")[0]["datetime"],
                "date-posted": localdt(x.select("time")[0]["datetime"], "%Y-%m-%d"),
                "author-name": "SWG",
                "author-email": "info@swg-konzern.de",
            },
            _bs4(body).select(".news-list > a"),
        )
    ),
)


# # Stadttheater Gießen
# - [x] fertig

url = "https://stadttheater-giessen.de/de/ajax/?action=load_magazine&start=0&items=12"
theater_headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "sec-ch-ua": '"Chromium";v="109", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "x-requested-with": "XMLHttpRequest",
    "cookie": "wires=380e9468b111d143eeb61efe552e61d4; theme=pink",
    "Referer": "https://stadttheater-giessen.de/",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

# Only youngest five posts
LIMIT = 10  # TODO create parameter for this
all_posts += general_scraper(
    url,
    lambda body: map(
        lambda x: {
            "title": html.unescape(
                x["title"] + " - " + x["magazine_excerpt"][:60] + "..."
            ),
            "link": "http://stadttheater-giessen.de" + x["url"],
            "date-posted": _localdt(DTNOW),
            "author-name": "Stadttheater",
            "author-email": "dialog@stadttheater-giessen.de",
        },
        json.loads(body)["data"][:LIMIT],
    ),
    _header=theater_headers,
)


# # Stadt Gießen amtliche Bekanntmachung
#
# - [x] fertig
# - [ ] TODO ich kann das Datum noch mit als Key benutzen, z.B. wenn ein neues Dokument bekannt gemacht wurde

url = "https://www.giessen.de/Rathaus/Newsroom/Amtliche-Bekanntmachungen/"
all_posts += general_scraper(
    url,
    lambda body: list(
        map(
            lambda x: {
                "title": x.select("a")[0].text,
                "link": "http://giessen.de" + x.select("a")[0]["href"],
                "date-raw": x.select("small")[1].text.split(":")[1].strip(),
                "date-posted": localdt(
                    x.select("small")[1].text.split(":")[1].strip(), "%d.%m.%Y"
                ),
                "author-name": "Stadt - Amtliche Bekanntmachungen",
                "author-email": "presse@giessen.de",
            },
            _bs4(body).select(".main-content-area")[0].select("ul > li"),
        )
    ),
)

# # Oberhessisches Museum
# - [x] Fertig

url = "https://www.giessen.de/Erleben/Kultur/Museen-Ausstellungen/Oberhessisches-Museum/index.php?&object=tx,2874.5&ModID=255&call=suche&kat=2874.251&kuo=1&sfkat=0&sfmonat=0&sfjahr=0&k_sub=0&NavID=1894.209&La=1"
all_posts += general_scraper(
    url,
    lambda body: list(
        map(
            lambda x: {
                "title": x.select("h4.liste-titel > a")[0].text,
                "link": "https://www.giessen.de"
                + x.select("h4.liste-titel > a")[0]["href"],
                "date-raw": x.select("small.date")[0].text,
                "date-posted": localdt(x.select("small.date")[0].text, "%d.%m.%Y"),
                "author-name": "Oberhessisches Museum",
                "author-email": "museum@giessen.de",
            },
            _bs4(body).select(".main-content-area * article"),
        )
    ),
)


# Htize und Trockenheit
# - [x] Fertig

all_posts += general_scraper(
    "https://www.giessen.de/Rathaus/Newsroom/Aktuelle-Meldungen/index.php?NavID=2874.584.1",
    lambda body: map(
        lambda x: {
            "title": x.select("h4 > a")[0].text,
            "link": "http://giessen.de" + x.select("h4 > a")[0]["href"],
            "date-raw": x.select("small.date")[0].text,
            "date-posted": localdt(x.select("small.date")[0].text, "%d.%m.%Y"),
            "author-name": "Stadt - Hitze und Trockenheit",
            "author-email": "",
        },
        _bs4(body).select("section.mitteilungen > article"),
    ),
)


# Universum Gießen

all_posts += general_scraper(
    "https://universum-giessen.com/",
    lambda body: map(
        lambda x: {
            "title": x.select("h2")[0].text,
            "link": x.select("h2 > a")[0]["href"],
            "date-raw": x.find("div", itemprop="datePublished").text,
            "date-posted": localdt(
                x.find("div", itemprop="datePublished").text, "%Y-%m-%d", _fix=True
            ),
            "author-name": "Universum - Onlinemagazin der JLU",
            "author-email": "universum.giessen@gmail.com",
        },
        _bs4(body).select("article"),
    ),
)

# Asta Uni Gießen


def asta_mapper(body):

    posts = _bs4(body).select("article.post")

    # print(posts)

    return map(
        lambda x: {
            "title": "Neuer Beitrag",
            "link": x.select("figure > a")[0]["href"],
            "date-raw": x.find("time", itemprop="datePublished").text,
            "date-posted": localdt(
                x.find("time", itemprop="datePublished").text, "%d. %B %Y", _fix=True
            ),
            # TODO hier direkt das datetime aus dem itemprop nehmen
            "author-name": "Asta - Uni Gießen",
            "author-email": "info@asta-giessen.de",
        },
        posts,
    )


all_posts += general_scraper("https://www.asta-giessen.de/", asta_mapper)

# Haus der Nachhaltigkeit


def hdn_element(x):

    link = x.select("a")
    link = link[0]["href"]
    title = x.select("div.elementor-post__text > h3.elementor-post__title")[0].text
    date_raw = x.select("span.elementor-post-date")[0].text.strip()

    return {
        "title": title,
        "link": link,
        "date-raw": date_raw,
        "date-posted": localdt(date_raw, "%d. %B %Y", _fix=True),
        "author-name": "Haus der Nachhaltigkeit",
        "author-email": "info@hdn-giessen.de",
    }


def hdn_mapper(body):
    posts = _bs4(body).select("article.elementor-post")
    return map(hdn_element, posts)


all_posts += general_scraper("https://hdn-giessen.de/aktuelles-2", hdn_mapper)

# # Erstellung des Atom-Feeds
#
# Testweise Erstellung um zu schauen ob alle Attribute gesetzt sind

fg = FeedGenerator()
fg.id("http://datengraben.com/lokal")
fg.title("Gießen lokal")
# fg.author( {'name': 'Chris', 'email': 'datengraben@gmx.de'})
fg.link(href="http://datengraben.com", rel="alternate")
fg.link(href="http://datengraben.com/giessen-aktuelles.atom.xml", rel="self")
fg.language("de")

deleted_urls = pd.read_csv("conf/deleted.csv")["url"].values


def import_into_feed(all_posts):
    i = 0
    for post in all_posts:

        try:

            # filter deleted uris
            if post["link"] in deleted_urls:
                # print("Skip", post['link'])
                continue

            fe = fg.add_entry()
            fe.id(post["link"])
            fe.title(post["title"])
            fe.source(post["link"])
            fe.link(href=post["link"])

            fe.author({"name": post["author-name"], "email": post["author-email"]})

            date_posted = post["date-posted"]

            # Fix datetime objects when struct_time
            if type(date_posted).__name__ == "struct_time":
                from datetime import datetime
                from time import mktime

                date_posted = datetime.fromtimestamp(mktime(date_posted))

                # Make it timezone aware to fullfill FeedGenerator api
                import pytz

                date_posted = pytz.utc.localize(date_posted)

            fe.pubDate(date_posted)
            fe.updated(date_posted)
            i += 1
        except ValueError as e:
            print(f"Problem with {post}")
            print(e)
            print(post["date-posted"])
            print(type(post["date-posted"]).__name__)
    print("----------------")
    print("Gesamt:", i - 1)
    print("")


import_into_feed(all_posts)

# Validation

for e in fg.entry():
    if e.id() is None or e.title() is None:
        print(e.id())

computed_posts = {}
for e in fg.entry():
    computed_posts[e.link()[0]["href"]] = e
print("Computed posts:", len(computed_posts.keys()))


known_posts = {}
for e in feedparser.parse("./atom.xml")["entries"]:
    known_posts[e.id] = e
print("Existing posts:", len(known_posts.keys()))

# Für alle heute berechneten posts
update_count = 0
delete_count = 0
for entry in fg.entry():
    # Wenn es einen Eintrag in der alten atom.xml mit dieser ID gibt,
    # - Nimm dessen date-published in die neue atom.xml
    if entry.id() in known_posts.keys():
        existing_entry = known_posts[entry.id()]

        last_time_created = localdt(
            existing_entry["published"][:19], "%Y-%m-%dT%H:%M:%S", _fix=False
        )

        entry.pubDate(last_time_created)
        entry.updated(last_time_created)
    else:
        update_count += 1
    # Wenn nicht,
    # - tue nichts (neue einträge haben ein valides date)

existing_posts = len(known_posts.keys())
computed_posts = len(computed_posts)

if computed_posts < existing_posts:
    delete_count = existing_posts - computed_posts

print("Es wurden", update_count, "neue Posts hinzgefügt")
print("Es wurden", delete_count, "alte Posts gelöscht oder zurückgehalten")

if not arguments["--skip"]:
    # Import from other sources
    from scraper.muk import get_feed as muk

    import_into_feed(muk())

if arguments["--force-regenerate"] or (update_count > 0 or delete_count > 0):
    atomfeed = fg.atom_str(pretty=True)
    fg.atom_file(arguments["-f"])
    print("Outfile generated at", arguments["-f"])
