# Redirects map — base44 → static (review before applying)

**Domain unchanged:** `smallmoverscanada.ca` stays the canonical domain, so there's **no
cross-domain redirect**. The old base44 app served the same domain; only the URL *shapes*
change (case + trailing slash).

## 1. Auto-handled by `vercel.json` — no rule needed

`vercel.json` has `"trailingSlash": true`, so Vercel issues a 308 from the no-slash form
to the slash form automatically. Every old indexed URL below already lands correctly:

| Old (from old sitemap, lowercase, no slash) | New | Handled by |
|---|---|---|
| `/` | `/` | identical |
| `/locations` | `/locations/` | trailingSlash |
| `/about` | `/about/` | trailingSlash |
| `/alberta`, `/british-columbia`, `/ontario`, `/saskatchewan` | `…/` | trailingSlash |
| `/{city-slug}` × 76 (e.g. `/calgary`) | `/{city-slug}/` | trailingSlash |
| `/blog/{post-slug}` (once blogs are built) | `/blog/{post-slug}/` | trailingSlash |

City/province/about slugs are **unchanged**, so no per-page rules are required for them.

## 2. Explicit redirects needed (case mismatch + removed pages)

The old React routes were **PascalCase** (`createPageUrl` mapped page keys directly), and
two admin pages no longer exist. Vercel path matching is case-sensitive, so these need
real rules:

| Old URL | New URL | Type | Why |
|---|---|---|---|
| `/Home` | `/` | 301 | PascalCase route key |
| `/Locations` | `/locations/` | 301 | PascalCase route key |
| `/Blog` | `/blog/` | 301 | PascalCase route key |
| `/Admin` | `/` | 301 | admin tool — not migrated |
| `/BlogAdmin` | `/` | 301 | admin tool — not migrated |

> Note: the old internal nav linked to `/Locations` and `/Blog` (capitalized) while the old
> sitemap advertised `/locations`. Both forms may be indexed — the rules above + trailingSlash
> cover both.

## 3. Ready-to-apply `vercel.json` block

Add this `redirects` array to `vercel.json` (keeps existing `cleanUrls`/`trailingSlash`):

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "cleanUrls": true,
  "trailingSlash": true,
  "redirects": [
    { "source": "/Home", "destination": "/", "permanent": true },
    { "source": "/Locations", "destination": "/locations/", "permanent": true },
    { "source": "/Blog", "destination": "/blog/", "permanent": true },
    { "source": "/Admin", "destination": "/", "permanent": true },
    { "source": "/BlogAdmin", "destination": "/", "permanent": true }
  ]
}
```

## 4. Open items
- **Blog post slugs:** old `/blog/{slug}` → new `/blog/{slug}/` is auto-handled, **provided
  the new post slugs match the old ones.** I'll confirm against the `Blog` export when we
  build the blog.
- If analytics show other crawled variants (e.g. `/About`, `/Calgary`), send them over and
  I'll add rules.
