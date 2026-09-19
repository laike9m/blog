# Blogmaker original content (archive)

Frozen snapshot of the blog as Blogmaker served it, captured at migration time.
Kept because it becomes unrecoverable once the Blogmaker subscription lapses.

| File | What it is |
|---|---|
| `html/<slug>.html` | Original post body HTML, scraped from the live `.published-text` container |
| `posts.json` | Same content plus metadata, machine-readable |
| `export_blogmaker.py` | The scraper that produced the above |
| `convert_to_hugo.py` | HTML/Markdown -> Hugo content conversion |
| `compare_fidelity.py` | Audit comparing published pages against these originals |

## Why keep it

`compare_fidelity.py` confirmed no text, images or links were lost in the
conversion. But it compares *content*, not *structure* — a flattened nested
list or a reshaped table would pass. If something ever looks off in an old
post, diff it against the HTML here.

Note the images in `html/` are already rewritten to `/blog/assets/uploads/...`;
the true originals were served from `editor.blogmaker.app`, which will stop
resolving after cancellation. Every one of them is mirrored in
`static/assets/uploads/`.

Nothing here is used by the build.
