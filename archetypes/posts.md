---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
# `url` must be set explicitly, and must match the filename. Hugo's `slug`
# sanitiser rewrites some names (it strips a leading hyphen, for example), and
# a rewritten URL is a dead link the moment it's published.
url: "/{{ .File.ContentBaseName }}/"
date: {{ .Date }}
description: ""
author: "laike9m"
draft: true
# Optional cover image. Note the /blog prefix -- required here, because this
# value goes through absURL. Inline images in the body need it too.
# cover:
#   image: "/blog/assets/uploads/your-image.png"
#   relative: false
---

Write the post here.

Images: put the file in `static/assets/uploads/` and reference it as
`![alt](/blog/assets/uploads/your-image.png)` — with the `/blog` prefix.
