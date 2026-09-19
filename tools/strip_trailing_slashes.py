#!/usr/bin/env python3
"""Strip trailing slashes from page URLs in the built site.

Blogmaker served posts as /blog/two-way-translation (no trailing slash). Hugo
always appends one to pretty URLs and has no switch to turn that off, so the
generated links, canonicals, sitemap and search index all point at
/blog/two-way-translation/ instead.

Overriding the theme templates is the wrong fix: PaperMod references
.Permalink in 52 places across 20 files, and many of those are *asset* URLs
(cover images, stylesheets, the search bundle) that must keep their exact
paths. So we post-process the output instead, with one narrow rule:

    a URL under /blog/ that ends in "/" and whose last segment contains no "."
    is a page URL -> drop the slash

That leaves every asset untouched (they all carry an extension) and leaves the
site root /blog/ alone (it has no segment after the prefix).

The files on disk are NOT moved -- <slug>/index.html stays exactly where it is.
Only the links *inside* the output change. worker.js already serves the
extensionless form directly, so the two line up.

Usage:
    python3 tools/strip_trailing_slashes.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE = "https://clicknow.ai"
PREFIX = "/blog"
SUFFIXES = {".html", ".xml", ".json", ".atom", ".txt"}

# A /blog/... URL ending in a slash, captured up to the quote/bracket/space
# that terminates it.
PATTERN = re.compile(
    r"(?P<origin>" + re.escape(SITE) + r")?"
    + re.escape(PREFIX)
    + r"/(?P<path>[^\"'\s<>\\]+?)/(?=[\"'\s<>\\])"
)


def replace(match: re.Match) -> str:
    path = match.group("path")
    # Anything with a dot in its final segment is a file, not a page.
    if "." in path.rsplit("/", 1)[-1]:
        return match.group(0)
    return f"{match.group('origin') or ''}{PREFIX}/{path}"


def main() -> None:
    changed = 0
    edits = 0
    for file in sorted(PUBLIC.rglob("*")):
        if not file.is_file() or file.suffix not in SUFFIXES:
            continue
        original = file.read_text(encoding="utf-8")
        updated, count = PATTERN.subn(replace, original)
        if count:
            file.write_text(updated, encoding="utf-8")
            changed += 1
            edits += count
    print(f"  . stripped {edits} trailing slashes across {changed} files")


if __name__ == "__main__":
    main()
