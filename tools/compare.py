"""One-off: dump ORF news feed and derStandard Newsroom with dates for comparison."""
import collections
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime


def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "rss-filter-compare/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return ET.fromstring(r.read())


def items(root):
    out = []
    for it in root.iter():
        if it.tag.split("}")[-1] != "item":
            continue
        f = {c.tag.split("}")[-1]: (c.text or "").strip() for c in it}
        d = f.get("date") or f.get("pubDate") or ""
        try:
            dt = datetime.fromisoformat(d) if "T" in d else parsedate_to_datetime(d)
        except Exception:
            dt = None
        out.append((dt, f.get("subject", ""), f.get("title", "")))
    return out


for name, url in [("ORF", "https://rss.orf.at/news.xml"), ("STD", "https://www.derstandard.at/rss")]:
    its = items(get(url))
    ds = [d for d, _, _ in its if d]
    print(f"=== {name}: {len(its)} items, {min(ds)} .. {max(ds)}")
    print("per day:", dict(collections.Counter(d.date().isoformat() for d in ds)))
    print("subjects:", dict(collections.Counter(s for _, s, _ in its).most_common()))
    for d, s, t in its:
        print(f"{name} | {d:%m-%d %H:%M} | {s} | {t}")
