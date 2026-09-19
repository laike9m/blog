#!/usr/bin/env python3
"""Simulate worker.js's request logic against the real GitHub Pages origin.

This exists because of a bug that shipped: the original Worker tried the bare
path first and broke out of the candidate loop on "not 404". GitHub Pages
answers an extensionless directory path with a *301*, so the loop exited
immediately and proxied the redirect straight through -- all 16 post URLs
started 301-ing instead of serving content.

Checking that "<path>/index.html returns 200" was not enough: the assumption
was right, the control flow was wrong. This script mirrors the actual candidate
ORDER and break condition so that class of bug can't come back.

Keep in sync with worker.js.

Usage:
    uv run --with requests tools/check_worker_logic.py
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


def looks_like_extensionless_page(pathname: str) -> bool:
    last = pathname[pathname.rfind("/") + 1:]
    return last != "" and "." not in last


def worker_fetch(pathname: str):
    """Mirror of the candidate loop in worker.js."""
    candidates = []
    if looks_like_extensionless_page(pathname):
        candidates.append(pathname + "/index.html")
    elif pathname.endswith("/"):
        candidates.append(pathname + "index.html")
    candidates.append(pathname)

    response = None
    for candidate in candidates:
        response = session.get(
            ORIGIN + candidate, allow_redirects=False, timeout=30
        )
        if response.status_code == 200:
            break
    return response


def main() -> None:
    slugs = [
        (e.find(f"{ATOM}id").text or "").strip().rsplit("/", 1)[-1]
        for e in ET.parse(FEED).getroot().findall(f"{ATOM}entry")
    ]

    paths = (
        [f"{PREFIX}/{s}" for s in slugs]        # bare post URLs (the regression)
        + [f"{PREFIX}/", f"{PREFIX}/2", f"{PREFIX}/search/"]
        + [f"{PREFIX}/feed.atom",
           f"{PREFIX}/assets/uploads/b60ce7e02c4afbc21ef0e0249c97082e.png"]
    )

    failures = []
    for path in paths:
        r = worker_fetch(path)
        if r.status_code != 200:
            failures.append(f"{path} -> {r.status_code}")
    print(f"  . {len(paths) - len(failures)}/{len(paths)} paths resolve to 200 "
          f"with no redirect leaked")

    # A genuinely missing page must still surface as a 404, not a 200.
    r = worker_fetch(f"{PREFIX}/definitely-not-a-real-post")
    if r.status_code == 200:
        failures.append("missing page returned 200 instead of 404")
    else:
        print(f"  . unknown path correctly returns {r.status_code}")

    if failures:
        print(f"\nFAILED ({len(failures)}):")
        for f in failures:
            print(f"  x {f}")
        sys.exit(1)
    print("\nWorker logic is correct against the live origin.")


if __name__ == "__main__":
    main()
