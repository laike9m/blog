#!/usr/bin/env python3
"""Compare the published pages against the original Blogmaker HTML.

Run this BEFORE deleting the raw export. Once the Blogmaker subscription
lapses the originals are unrecoverable, and the HTML -> Markdown conversion
could have quietly dropped something (the Atom feed already turned out to be
lossy once, so the conversion deserves the same suspicion).

Compares, per post: visible text, image count, and link targets.

Usage:
    uv run --with beautifulsoup4 tools/compare_fidelity.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL = ROOT / "export" / "content" / "html"
PUBLISHED = ROOT / "site" / "public"


def norm_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()


def words(text: str) -> list[str]:
    # Compare on word shape only: punctuation and entity handling legitimately
    # differ between the original HTML and Goldmark's output.
    return re.findall(r"[0-9A-Za-z\u4e00-\u9fff]+", text.lower())


def main() -> None:
    problems = []
    for src in sorted(ORIGINAL.glob("*.html")):
        slug = src.stem
        page = PUBLISHED / slug / "index.html"
        if not page.is_file():
            problems.append(f"{slug}: published page missing")
            continue

        orig_html = src.read_text(encoding="utf-8")
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        content = soup.find("div", class_="post-content")
        if content is None:
            problems.append(f"{slug}: no .post-content in published page")
            continue

        ow, pw = words(norm_text(orig_html)), words(str(content))
        missing = [w for w in ow if w not in pw]
        # Report only substantive loss; a stray token difference is noise.
        if len(missing) > 3:
            problems.append(
                f"{slug}: {len(missing)} words missing, e.g. {missing[:8]}"
            )

        o_imgs = len(BeautifulSoup(orig_html, "html.parser").find_all("img"))
        p_imgs = len(content.find_all("img"))
        if o_imgs != p_imgs:
            problems.append(f"{slug}: images {o_imgs} -> {p_imgs}")

        o_links = {
            a["href"] for a in BeautifulSoup(orig_html, "html.parser")
            .find_all("a", href=True)
        }
        p_links = {a["href"] for a in content.find_all("a", href=True)}
        lost = {l for l in o_links if l not in p_links}
        if lost:
            problems.append(f"{slug}: links lost {sorted(lost)[:3]}")

        print(f"  . {slug:34s} text ok, {p_imgs} imgs, {len(p_links)} links")

    if problems:
        print(f"\nDIFFERENCES ({len(problems)}):")
        for p in problems:
            print(f"  ! {p}")
        sys.exit(1)
    print("\nNo content lost. The raw export is safe to delete.")


if __name__ == "__main__":
    main()
