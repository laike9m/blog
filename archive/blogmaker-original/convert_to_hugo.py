#!/usr/bin/env python3
"""Convert the Blogmaker export into a Hugo (PaperMod) content tree.

Path handling is deliberately asymmetric, because Hugo treats the two cases
differently when baseURL contains a subpath (https://clicknow.ai/blog/):

  * front matter `cover.image` -> PaperMod runs it through `absURL`, which
    already prepends the baseURL path. So it must NOT contain /blog, or you
    get /blog/blog/assets/...
  * inline markdown images     -> PaperMod's render-image hook emits the
    destination verbatim. So it MUST keep the /blog prefix.

Usage:
    uv run --with pyyaml tools/convert_to_hugo.py
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export"
SITE = ROOT / "site"
DEST_POSTS = SITE / "content" / "posts"
DEST_STATIC = SITE / "static" / "assets" / "uploads"

FM_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    match = FM_RE.match(text)
    if not match:
        raise ValueError("missing front matter")
    meta = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        meta[key.strip()] = value
    return meta, match.group(2)


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> None:
    if DEST_POSTS.exists():
        shutil.rmtree(DEST_POSTS)
    DEST_POSTS.mkdir(parents=True)
    DEST_STATIC.mkdir(parents=True, exist_ok=True)

    # Mirror images 1:1 so every historical /blog/assets/uploads/... URL works.
    src_uploads = EXPORT / "static" / "assets" / "uploads"
    count_img = 0
    for img in sorted(src_uploads.iterdir()):
        if img.is_file():
            shutil.copy2(img, DEST_STATIC / img.name)
            count_img += 1

    # Prevent /blog/posts/ from existing as a duplicate listing page; the
    # homepage is the canonical post index (as it was on Blogmaker).
    (SITE / "content" / "posts" / "_index.md").write_text(
        '---\ntitle: "Posts"\nbuild:\n  render: never\n  list: never\n---\n',
        encoding="utf-8",
    )

    count_post = 0
    for md in sorted((EXPORT / "content" / "posts").glob("*.md")):
        meta, body = parse_front_matter(md.read_text(encoding="utf-8"))

        # Use `url`, not `slug`: Hugo's slug sanitiser strips the leading
        # hyphen from "-1137-google-search", which would silently 404 that
        # post and change its feed id. `url` is taken literally.
        lines = [
            "---",
            f"title: {quote(meta['title'])}",
            f"url: {quote('/' + meta['slug'] + '/')}",
            f"date: {meta['date']}",
        ]
        if meta.get("lastmod"):
            lines.append(f"lastmod: {meta['lastmod']}")
        if meta.get("summary"):
            lines.append(f"description: {quote(meta['summary'])}")
            lines.append(f"summary: {quote(meta['summary'])}")
        if meta.get("author"):
            lines.append(f"author: {quote(meta['author'])}")
        if meta.get("cover"):
            # Keep the /blog prefix. Hugo's absURL treats a leading-slash path
            # as relative to the HOST root and does not insert the baseURL
            # subpath, so stripping /blog here yields /assets/... and 404s.
            lines += [
                "cover:",
                f"  image: {quote(meta['cover'])}",
                "  relative: false",
            ]
        lines += ["---", ""]

        (DEST_POSTS / md.name).write_text(
            "\n".join(lines) + "\n" + body.lstrip("\n"), encoding="utf-8"
        )
        count_post += 1

    print(f"{count_post} posts -> {DEST_POSTS}")
    print(f"{count_img} images -> {DEST_STATIC}")


if __name__ == "__main__":
    main()
