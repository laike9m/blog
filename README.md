# Clicknow Blog

Static Hugo blog served at **https://clicknow.ai/blog**, migrated off Blogmaker.

## How the /blog subdirectory works

`clicknow.ai` itself is a **Carrd** site, and Carrd gives you no backend access.
The `/blog` subdirectory is therefore *not* served by Carrd at all — a
**Cloudflare Worker** intercepts `/blog*` and reverse-proxies it. That Worker
used to point at Blogmaker; it now points here.

```
visitor -> Cloudflare -> /*      -> Carrd        (untouched)
                      -> /blog*  -> Worker -> laike9m.github.io/blog  (this repo)
```

The repo is named `blog` on purpose: GitHub Pages then serves it at
`laike9m.github.io/blog/...`, which maps **1:1** onto `clicknow.ai/blog/...`,
so the Worker can pass paths straight through with no rewriting.

Worker source: [`worker.js`](./worker.js).

## Writing a post

Create `content/posts/my-post.md`:

```markdown
---
title: "My Post"
url: "/my-post/"
date: 2026-01-30T10:00:00Z
description: "One-line summary shown on the index and in the feed."
author: "laike9m"
cover:
  image: "/assets/uploads/my-image.png"
  relative: false
---

Body goes here.
```

Then `git push` — GitHub Actions builds and deploys automatically.

## Path rules (easy to get wrong)

`baseURL` contains a subpath (`https://clicknow.ai/blog/`), and Hugo treats the
two image cases differently:

| Where | Write it as | Why |
|---|---|---|
| `cover.image` front matter | `/assets/uploads/x.png` | PaperMod runs it through `absURL`, which already prepends `/blog` |
| Inline markdown `![](...)` | `/blog/assets/uploads/x.png` | the render hook emits the path verbatim |

Getting this backwards produces either `/blog/blog/assets/...` or a 404.
`tools/verify_build.py` in the migration workspace catches both.

## Things that must not change

- **`url:` front matter, not `slug:`** — Hugo's slug sanitiser strips the
  leading hyphen from `-1137-google-search` and silently breaks that URL.
- **`/blog/feed.atom`** — existing RSS subscribers depend on this exact path.
  `layouts/home.atom.atom` also trims the trailing slash from entry `<id>`s so
  they stay identical to Blogmaker's; otherwise every subscriber gets all 16
  posts re-delivered as new.
- **No `--baseURL` flag in CI** — see the comment in
  `.github/workflows/deploy.yml`.

## Local development

```bash
hugo server            # http://localhost:1313/blog/
hugo --gc --minify     # production build into ./public
```

## Regression guard

`tools/verify_build.py` runs in CI between build and deploy. It pins the
migration contract against `tools/blogmaker-feed.atom` (a frozen copy of the
original Blogmaker feed):

- all 16 original post URLs still resolve
- asset paths keep the `/blog` prefix
- `feed.atom` entry ids stay byte-identical

If any of these break, the deploy fails instead of silently shipping.

> [!NOTE]
> `hugo server` writes into `public/`, leaving `localhost:1313` URLs behind.
> `public/` is gitignored and CI always builds from a clean checkout, so this
> can't reach production — but don't publish a locally-served `public/` by hand.
