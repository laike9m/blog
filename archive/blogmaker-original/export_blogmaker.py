#!/usr/bin/env python3
"""Export a Blogmaker blog losslessly.

The Atom feed is convenient but LOSSY: it strips heading tags and other inline
markup. So we use the feed only as the post *index* + metadata source, and
scrape each live post page for the authoritative body HTML, which Blogmaker
renders inside `<div class="published-text">`.

Inline images are hosted on editor.blogmaker.app (NOT on your own domain), so
they are mirrored locally too and rewritten to /blog/assets/uploads/... —
matching the path scheme already used by cover images, so every existing image
URL keeps working after the migration.

Usage:
    uv run --with markdownify --with requests --with beautifulsoup4 export_blogmaker.py
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

FEED_URL = "https://clicknow.ai/blog/feed.atom"
SITE_ROOT = "https://clicknow.ai/blog/"
ATOM = "{http://www.w3.org/2005/Atom}"
UPLOADS_PREFIX = "/blog/assets/uploads/"

OUT = Path(__file__).parent / "export"
POSTS_DIR = OUT / "content" / "posts"
HTML_DIR = OUT / "content" / "html"
UPLOADS_DIR = OUT / "static" / "assets" / "uploads"

session = requests.Session()
session.headers["User-Agent"] = "blog-migration-export/1.0"


def yaml_escape(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def mirror_asset(url: str) -> str | None:
    """Download an image and return its new site-relative URL."""
    filename = Path(urlparse(url).path).name
    if not filename:
        return None
    dest = UPLOADS_DIR / filename
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        resp = session.get(url, timeout=60)
        if resp.status_code != 200:
            print(f"    !! {resp.status_code} {url}", file=sys.stderr)
            return None
        dest.write_bytes(resp.content)
        print(f"    + {filename} ({len(resp.content):,} bytes)")
    return UPLOADS_PREFIX + filename


def fetch_body_html(post_url: str) -> str:
    """Pull the authoritative post body out of the live page."""
    resp = session.get(post_url, timeout=60)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    node = soup.find("div", class_="published-text")
    if node is None:
        raise RuntimeError(f"no .published-text found on {post_url}")
    return node.decode_contents()


def localize(html: str) -> str:
    """Mirror every remote image and make all internal links root-relative."""
    soup = BeautifulSoup(html, "html.parser")

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src.startswith("http"):
            continue
        new = mirror_asset(src)
        if new:
            img["src"] = new
        img.attrs.pop("loading", None)

    for a in soup.find_all("a", href=True):
        a["href"] = a["href"].replace(SITE_ROOT, "/blog/").replace(
            "https://clicknow.ai/blog", "/blog"
        )

    return str(soup)


def main() -> None:
    for directory in (POSTS_DIR, HTML_DIR, UPLOADS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    print(f"Fetching index: {FEED_URL}")
    raw = session.get(FEED_URL, timeout=60).content
    (OUT / "feed.atom").write_bytes(raw)

    entries = ET.fromstring(raw).findall(f"{ATOM}entry")
    print(f"{len(entries)} posts\n")

    dump = []
    for entry in entries:
        def text(tag: str) -> str:
            node = entry.find(f"{ATOM}{tag}")
            return (node.text or "").strip() if node is not None else ""

        url = text("id")
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        title = text("title")
        print(f"[{slug}] {title}")

        author_node = entry.find(f"{ATOM}author/{ATOM}name")
        author = (author_node.text or "").strip() if author_node is not None else ""

        cover = ""
        for link in entry.findall(f"{ATOM}link"):
            if link.get("rel") == "enclosure":
                cover = link.get("href", "")
        cover_local = mirror_asset(cover) if cover else ""

        body_html = localize(fetch_body_html(url))
        (HTML_DIR / f"{slug}.html").write_text(body_html, encoding="utf-8")

        body_md = markdownify(body_html, heading_style="ATX", bullets="-").strip()
        body_md = re.sub(r"\n{3,}", "\n\n", body_md)

        published, updated, summary = text("published"), text("updated"), text("summary")
        front = [
            "---",
            f"title: {yaml_escape(title)}",
            f"slug: {yaml_escape(slug)}",
            f"date: {published}" if published else "",
            f"lastmod: {updated}" if updated else "",
            f"summary: {yaml_escape(summary)}" if summary else "",
            f"author: {yaml_escape(author)}" if author else "",
            f"cover: {yaml_escape(cover_local)}" if cover_local else "",
            f"canonical_source: {yaml_escape(url)}",
            "---",
            "",
        ]
        (POSTS_DIR / f"{slug}.md").write_text(
            "\n".join(l for l in front if l != "") + "\n" + body_md + "\n",
            encoding="utf-8",
        )

        dump.append(
            {
                "slug": slug,
                "url": url,
                "title": title,
                "published": published,
                "updated": updated,
                "summary": summary,
                "author": author,
                "cover": cover_local,
                "cover_original": cover,
                "body_html": body_html,
            }
        )

    (OUT / "posts.json").write_text(
        json.dumps(dump, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    images = sorted(p.name for p in UPLOADS_DIR.iterdir())
    print(f"\nDone: {len(dump)} posts, {len(images)} images -> {OUT}")


if __name__ == "__main__":
    main()
