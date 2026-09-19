#!/usr/bin/env python3
"""Verify the built Hugo site against the original Blogmaker blog.

Checks, in order of how badly they'd hurt if they broke:
  1. every original post URL still resolves to a built page
  2. no /blog/blog/... double-prefix (the classic subdirectory-baseURL bug)
  3. every local asset referenced by the HTML actually exists on disk
  4. /blog/feed.atom exists and its entry ids match the original feed exactly
  5. the old paginated URL /blog/2 still resolves

Usage:
    uv run --with beautifulsoup4 tools/verify_build.py
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ORIGINAL_FEED = ROOT / "tools" / "blogmaker-feed.atom"
ATOM = "{http://www.w3.org/2005/Atom}"
PREFIX = "/blog"

failures: list[str] = []
notes: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def public_path(url_path: str) -> Path | None:
    """Map a public /blog/... URL onto a file in the build output."""
    rel = url_path.removeprefix(PREFIX).lstrip("/")
    candidates = [PUBLIC / rel, PUBLIC / rel / "index.html"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def main() -> None:
    original = ET.parse(ORIGINAL_FEED).getroot()
    original_ids = [
        (e.find(f"{ATOM}id").text or "").strip()
        for e in original.findall(f"{ATOM}entry")
    ]

    # --- 1. every original post URL still resolves ------------------------
    for post_url in original_ids:
        path = urlparse(post_url).path
        check(public_path(path) is not None, f"post URL missing from build: {path}")
    notes.append(f"checked {len(original_ids)} original post URLs")

    # --- 2 & 3. scan every built HTML page --------------------------------
    html_files = sorted(PUBLIC.rglob("*.html"))
    asset_refs = 0
    for html_file in html_files:
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        rel_name = html_file.relative_to(PUBLIC)

        for attr, tags in (("src", soup.find_all(["img", "script"])),
                           ("href", soup.find_all("link"))):
            for tag in tags:
                ref = tag.get(attr)
                if not ref:
                    continue
                parsed = urlparse(ref)
                if parsed.scheme in ("http", "https"):
                    if parsed.netloc != "clicknow.ai":
                        continue
                    path = parsed.path
                elif ref.startswith("/"):
                    path = ref
                else:
                    continue

                check("/blog/blog/" not in path,
                      f"double /blog prefix in {rel_name}: {ref}")

                if "/assets/" in path or path.endswith((".png", ".jpg", ".jpeg",
                                                        ".gif", ".webp", ".css",
                                                        ".js")):
                    asset_refs += 1
                    # Must be under /blog -- a bare /assets/... means the
                    # baseURL subpath was dropped, which 404s in production
                    # even though the file exists in the build output.
                    check(path.startswith(PREFIX + "/"),
                          f"asset path missing {PREFIX} prefix in {rel_name}: {ref}")
                    check(public_path(path) is not None,
                          f"missing asset {path} (referenced by {rel_name})")
    notes.append(f"scanned {len(html_files)} HTML pages, {asset_refs} asset refs")

    # --- 4. feed.atom ------------------------------------------------------
    feed_file = PUBLIC / "feed.atom"
    check(feed_file.is_file(), "feed.atom was not generated")
    if feed_file.is_file():
        new = ET.parse(feed_file).getroot()
        new_ids = [
            (e.find(f"{ATOM}id").text or "").strip()
            for e in new.findall(f"{ATOM}entry")
        ]
        check(
            set(new_ids) == set(original_ids),
            "feed entry ids changed -> every subscriber would be re-notified.\n"
            f"    only in old: {sorted(set(original_ids) - set(new_ids))}\n"
            f"    only in new: {sorted(set(new_ids) - set(original_ids))}",
        )
        notes.append(f"feed.atom has {len(new_ids)} entries, ids match original")

    # --- 5. legacy pagination URL -----------------------------------------
    check(public_path("/blog/2") is not None, "/blog/2 (old page 2) does not resolve")

    # --- 6. the duplicate section listing must NOT exist -------------------
    check(not (PUBLIC / "posts" / "index.html").is_file(),
          "/blog/posts/ was rendered (duplicate listing page)")

    print("\n".join(f"  . {n}" for n in notes))
    if failures:
        print(f"\nFAILED ({len(failures)}):")
        for f in failures:
            print(f"  x {f}")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
