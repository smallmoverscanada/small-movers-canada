# Small Movers Canada — static site

Static HTML site for [smallmoverscanada.ca](https://smallmoverscanada.ca), migrated from
base44. Deployed on Vercel (static files + one serverless function for the quote form).

## Structure

```
/index.html                 Homepage
/[city]/index.html          76 city pages
/[province]/index.html      british-columbia, alberta, ontario, saskatchewan
/locations/, /about/        National pages
/blog/, /blog/[slug]/       Blog index + posts
/thank-you/                 Post-quote confirmation (noindex)
/api/quote.js               Serverless function — emails the quote form via Resend
/assets/                    Logo, favicon, founder photo, blog images
/_template/city.html        Canonical city-page template (design source of truth)
/build/                     Generators + CMS exports (City_export.csv, Blog_export.csv)
sitemap.xml, robots.txt, vercel.json
```

## Regenerating pages

City pages come from `build/City_export.csv`; everything else from `build/pages.py`
(which also reads `build/Blog_export.csv`). After editing the template or a CSV:

```bash
python3 build/generate.py   # 76 city pages
python3 build/pages.py      # home, locations, about, provinces, blog, thank-you, sitemap
```

## Environment variables (set in Vercel)

| Name | Purpose |
|------|---------|
| `RESEND_API_KEY` | Resend API key — used by `/api/quote` to email quote requests to info@smallmoverscanada.ca |

The Resend "from" domain (`smallmoverscanada.ca`) must be verified in Resend.
