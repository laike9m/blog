/**
 * clicknow.ai/blog  ->  GitHub Pages reverse proxy
 *
 * Drop-in replacement for the Blogmaker-generated Worker. Everything else in
 * your setup stays exactly as-is:
 *   - Carrd keeps serving clicknow.ai (untouched, no backend access needed)
 *   - The existing Worker routes stay the same:
 *         clicknow.ai/blog*
 *         clicknow.ai/blog/*
 *   - Every public URL is preserved byte-for-byte
 *
 * The trick: name the GitHub repo `blog` so GitHub Pages serves the site at
 * https://<user>.github.io/blog/... — the path then maps 1:1 onto
 * https://clicknow.ai/blog/... and no URL rewriting is needed at all.
 */

const ORIGIN = "https://laike9m.github.io"; // <-- your GitHub Pages host
const PREFIX = "/blog";

/** Paths that look like a page rather than a file (no extension, no slash). */
function looksLikeExtensionlessPage(pathname) {
  const last = pathname.slice(pathname.lastIndexOf("/") + 1);
  return last !== "" && !last.includes(".");
}

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // Only ever handle the blog subtree; anything else falls through to Carrd.
    if (url.pathname !== PREFIX && !url.pathname.startsWith(PREFIX + "/")) {
      return fetch(request);
    }

    // Blogmaker served posts WITHOUT a trailing slash
    // (clicknow.ai/blog/two-way-translation), while Hugo/GitHub Pages store
    // them as <slug>/index.html. Asking the origin for the bare path gets a
    // 301 to the trailing-slash form, which would change the URL users and
    // search engines see.
    //
    // So for extensionless paths we ask for <path>/index.html FIRST and serve
    // that at the original address. Order matters: GitHub Pages answers the
    // bare path with a 301, not a 404, so trying it first would short-circuit
    // "fall through on 404" logic and leak the redirect.
    const candidates = [];
    if (looksLikeExtensionlessPage(url.pathname)) {
      candidates.push(url.pathname + "/index.html");
    } else if (url.pathname.endsWith("/")) {
      candidates.push(url.pathname + "index.html");
    }
    candidates.push(url.pathname); // raw path last, as the fallback

    let response;
    let originUrl;
    for (const candidate of candidates) {
      originUrl = new URL(ORIGIN + candidate + url.search);
      response = await fetch(
        new Request(originUrl, {
          method: request.method,
          headers: request.headers,
          body:
            request.method === "GET" || request.method === "HEAD"
              ? null
              : request.body,
          redirect: "manual",
        }),
        { cf: { cacheTtl: 300, cacheEverything: true } },
      );
      if (response.status === 200) break;
    }

    // Rewrite any origin-side redirect so the visitor never sees github.io.
    if (response.status >= 300 && response.status < 400) {
      const location = response.headers.get("location");
      if (location) {
        const target = new URL(location, originUrl);
        if (target.origin === ORIGIN) {
          const headers = new Headers(response.headers);
          headers.set("location", url.origin + target.pathname + target.search);
          return new Response(null, { status: response.status, headers });
        }
      }
    }

    const headers = new Headers(response.headers);
    headers.delete("content-security-policy");
    headers.delete("x-github-request-id");
    headers.set("x-proxied-by", "cloudflare-worker");

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};
