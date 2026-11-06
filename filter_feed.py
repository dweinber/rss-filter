#!/usr/bin/env python3
"""Build a filtered derStandard Newsroom feed.

Usage: python filter_feed.py [output.xml]

Removes Newsroom items that
  - also appear in a section feed listed in EXCLUDE (optionally with a
    title pattern that rescues matching items),
  - are "evergreen" pinned posts older than MAX_AGE_DAYS,
  - have puzzle/quiz titles (TITLE_EXCLUDE).
Standard library only.
"""
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

SOURCE = "https://www.derstandard.at/rss"
TITLE = "derStandard Newsroom (gefiltert)"

# Section feeds to drop. Value: regex of titles to KEEP anyway, or None.
EXCLUDE = {
    "https://www.derstandard.at/rss/diskurs": None,
    # Sport: drop everything except World/European Championship items
    "https://www.derstandard.at/rss/sport": re.compile(
        r"\b(WM|EM|Weltmeisterschaft|Europameisterschaft|Euro 20\d\d)\b"
        r"|\w+-(WM|EM)\b|\b(WM|EM)-\w+"
    ),
    # add more, e.g. "https://www.derstandard.at/rss/etat": None,
}

MAX_AGE_DAYS = 14

# Puzzles, quizzes and the like (case-insensitive). Kept specific so news
# headlines like "Rätsel um ..." are not caught.
TITLE_EXCLUDE = re.compile(
    r"sudoku|quiz|kreuzwort|schieberätsel|wortsuche|standardrätsel|"
    r"bilderrätsel|buchstabensalat|kakuro|nonogramm|\brätsel (vom|der woche)\b",
    re.IGNORECASE,
)

ET.register_namespace("media", "http://search.yahoo.com/mrss/")
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "standard-filter/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return ET.fromstring(r.read())


def story_key(item):
    """Normalise to the link without query/fragment, so tracking params don't matter."""
    link = (item.findtext("link") or item.findtext("guid") or "").strip()
    return link.split("?")[0].split("#")[0].rstrip("/")


def main(out_path):
    source = fetch(SOURCE)
    channel = source.find("channel")

    # story key -> (section url, keep-pattern)
    excluded = {}
    for url, keep in EXCLUDE.items():
        for item in fetch(url).iter("item"):
            excluded[story_key(item)] = (url.rsplit("/", 1)[-1], keep)

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    kept = dropped = 0
    for item in list(channel.findall("item")):
        title = item.findtext("title") or ""
        reason = None

        pub = item.findtext("pubDate")
        if pub:
            try:
                if parsedate_to_datetime(pub) < cutoff:
                    reason = "old"
            except (TypeError, ValueError):
                pass
        if TITLE_EXCLUDE.search(title):
            reason = "puzzle"
        hit = excluded.get(story_key(item))
        if hit:
            section, keep = hit
            if keep is not None and keep.search(title):
                print(f"RESCUED ({section})", title)
            else:
                reason = section

        if reason:
            channel.remove(item)
            dropped += 1
            print(f"DROP ({reason})", title)
        else:
            kept += 1
            print("KEEP", title, "|", story_key(item))

    t = channel.find("title")
    if t is not None:
        t.text = TITLE

    ET.ElementTree(source).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"kept {kept}, dropped {dropped} -> {out_path}")
    if kept == 0:
        sys.exit("No items left - refusing to publish an empty feed")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "feed.xml")
