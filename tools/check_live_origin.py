#!/usr/bin/env python3
"""End-to-end check against the live GitHub Pages origin.

Confirms the origin behaves the way worker.js assumes BEFORE we cut traffic
over to it in Cloudflare.

Usage:
    uv run --with requests tools/check_live_origin.py
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ORIGIN = "https://laike9m.github.io"
PREFIX = "/blog"
ATOM = "{http://www.w3.org/2005/Atom}"
FEED = Path(__file__).resolve().parent / "blogmaker-feed.atom"

session = requests.Session()
failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)


def get(path: str, allow_redirects: bool = False):
    return session.get(ORIGIN + path, allow_redirects=allow_redirects, timeout=30)


def main() -> None:
    slugs = [
        (e.find(f"{ATOM}id").text or "").strip().rsplit("/", 1)[-1]
        for e in ET.parse(FEED).getroot().findall(f"{ATOM}entry")
    ]

    r = get(PREFIX + "/")
    check(r.status_code == 200, f"homepage: {r.status_code}")
    check("github.io" not in r.text, "homepage HTML leaks github.io")
    check("clicknow.ai/blog/" in r.text, "homepage does not reference clicknow.ai")
    print(f"  . homepage {r.status_code}, {len(r.content):,} bytes")

    # This is exactly what worker.js does for extensionless URLs. It must be a
    # direct 200 -- if GitHub Pages redirected here instead, the Worker would
    # fall back and visitors would see the URL change.
    bad = []
    for slug in slugs:
        r = get(f"{PREFIX}/{slug}/index.html")
        if r.status_code != 200:
            bad.append(f"{slug} -> {r.status_code}")
    check(not bad, "index.html direct fetch failed for: " + ", ".join(bad))
    print(f"  . {len(slugs)} posts served directly via index.html")

    r = get(f"{PREFIX}/feed.atom")
    check(r.status_code == 200, f"feed.atom: {r.status_code}")
    if r.status_code == 200:
        root = ET.fromstring(r.content)
        ids = [(e.find(f"{ATOM}id").text or "").strip()
               for e in root.findall(f"{ATOM}entry")]
        old = [(e.find(f"{ATOM}id").text or "").strip()
               for e in ET.parse(FEED).getroot().findall(f"{ATOM}entry")]
        check(set(ids) == set(old), "live feed ids differ from the original")
        check(all(i.startswith("https://clicknow.ai/blog/") for i in ids),
              "feed ids do not point at clicknow.ai")
        print(f"  . feed.atom {len(ids)} entries, ids match original")

    for asset in [
        "/blog/assets/uploads/b60ce7e02c4afbc21ef0e0249c97082e.png",
        "/blog/assets/uploads/ac6e68a8a3c67cccd73a1016293bfac9.png",
    ]:
        r = get(asset)
        check(r.status_code == 200, f"asset {asset}: {r.status_code}")
    print("  . sample assets 200")

    r = get(f"{PREFIX}/two-way-translation/index.html")
    check('href="https://clicknow.ai/blog/two-way-translation/"' in r.text
          or "clicknow.ai/blog/two-way-translation/" in r.text,
          "canonical does not point at clicknow.ai")
    print("  . canonical points at clicknow.ai")

    if failures:
        print(f"\nFAILED ({len(failures)}):")
        for f in failures:
            print(f"  x {f}")
        sys.exit(1)
    print("\nOrigin is ready. Safe to switch the Cloudflare Worker.")


if __name__ == "__main__":
    main()
