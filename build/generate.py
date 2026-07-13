#!/usr/bin/env python3
"""Generate static city pages for Small Movers Canada.

Reads the canonical template (_template/city.html) and the base44 City export
(build/City_export.csv), swaps only city-specific content, and writes each city
to <slug>/index.html. Run from the repo root: python3 build/generate.py
"""
import csv
import html
import os
import re
from urllib.parse import urlparse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(REPO, "_template", "city.html")
CSV_PATH = os.path.join(REPO, "build", "City_export.csv")
BLOG_CSV = os.path.join(REPO, "build", "Blog_export.csv")

# Per-province phone numbers (override whatever is in the CSV).
PROVINCE_PHONE = {
    "BC": "236-506-5898",
    "AB": "587-602-9862",
    "ON": "289-800-2197",
    "SK": "639-638-8439",
    "MB": "431-441-8631",
}

# Full province names, used when the CSV row leaves province_full blank.
PROVINCE_FULL = {
    "BC": "British Columbia",
    "AB": "Alberta",
    "ON": "Ontario",
    "SK": "Saskatchewan",
    "MB": "Manitoba",
}

# Per-city hourly-rate overrides (pulled from src/pages/*.jsx; only Toronto differs).
RATE_OVERRIDES = {
    "toronto": (95, 150),
}

# The canonical template's hero H1 (replaced wholesale with the city's real H1).
TEMPLATE_H1 = ('<h1>Small &amp; Hourly Movers&nbsp;in&nbsp;'
               '<span class="city-highlight">[CITY]</span></h1>')


def esc(s):
    """HTML-escape; safe in both element-text and attribute contexts."""
    return html.escape(s or "", quote=True)


def tel_digits(display):
    return "+1" + re.sub(r"\D", "", display)


def build_h1(h1_heading, city_name):
    """Escape the real H1 and wrap the city name in the highlight span."""
    e = esc(h1_heading)
    ec = esc(city_name)
    if ec and ec in e:
        e = e.replace(ec, f'<span class="city-highlight">{ec}</span>', 1)
    return e


def load_cities():
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f)]

    # Dedupe by slug: keep most recently updated, tie-break on longest paragraph.
    best = {}
    for r in rows:
        slug = (r.get("slug") or "").strip()
        if not slug:
            continue
        key = (r.get("updated_date") or "", len(r.get("local_paragraph") or ""))
        if slug not in best or key > best[slug][0]:
            best[slug] = (key, r)
    return [v[1] for v in best.values()]


def _blog_img(slug, url):
    url = (url or "").strip()
    if not url:
        return None
    ext = os.path.splitext(urlparse(url).path)[1] or ".webp"
    return f"/assets/blog/{slug}{ext}"


def load_blog_by_city():
    """Map city_slug -> list of published posts (newest first)."""
    if not os.path.exists(BLOG_CSV):
        return {}
    rows = list(csv.DictReader(open(BLOG_CSV, newline="", encoding="utf-8-sig")))
    by_city = {}
    for r in rows:
        if str(r.get("is_published", "")).strip().lower() != "true":
            continue
        cslug = (r.get("city_slug") or "").strip().lower()
        if cslug:
            by_city.setdefault(cslug, []).append(r)
    for cslug in by_city:
        by_city[cslug].sort(key=lambda r: (r.get("published_date") or ""), reverse=True)
    return by_city


def city_blog_section(city_name, posts):
    """A 'Moving Tips for <City>' section; empty string when the city has no posts."""
    if not posts:
        return ""
    cards = []
    for p in posts:
        pslug = (p.get("slug") or "").strip()
        img = _blog_img(pslug, p.get("image_url"))
        thumb = (f'<div class="city-blog-thumb"><img src="{img}" alt="{esc(p.get("title"))}" loading="lazy"></div>'
                 if img else '<div class="city-blog-thumb"></div>')
        cards.append(
            f'<a class="city-blog-card" href="/blog/{pslug}/">\n'
            f'  {thumb}\n'
            f'  <div class="city-blog-body">\n'
            f'    <h3>{esc(p.get("title"))}</h3>\n'
            f'    <p>{esc(p.get("excerpt"))}</p>\n'
            f'    <span class="city-blog-link">Read more →</span>\n'
            f'  </div>\n</a>'
        )
    cards_html = "\n".join(cards)
    return (
        '<section class="city-blog">\n'
        '  <div class="container">\n'
        '    <div style="text-align:center;"><span class="section-label">From the Blog</span></div>\n'
        f'    <h2 class="section-heading" style="text-align:center;">Moving Tips for {esc(city_name)}</h2>\n'
        f'    <div class="city-blog-grid">\n{cards_html}\n    </div>\n'
        '  </div>\n</section>'
    )


def render(template, row, blog_by_city):
    city = (row.get("city_name") or "").strip()
    slug = (row.get("slug") or "").strip()
    prov = (row.get("province") or "").strip()
    prov_full = (row.get("province_full") or "").strip() or PROVINCE_FULL.get(prov, prov)
    phone = PROVINCE_PHONE.get(prov, (row.get("phone_number") or "").strip())
    rate1, rate2 = RATE_OVERRIDES.get(slug, (85, 140))

    out = template

    # 1. SEO <title> and meta description — use the real CMS values verbatim.
    out = re.sub(r"<title>.*?</title>",
                 lambda m: f"<title>{esc(row.get('meta_title'))}</title>",
                 out, count=1, flags=re.DOTALL)
    out = re.sub(r'(<meta name="description" content=")[^"]*(">)',
                 lambda m: m.group(1) + esc(row.get("meta_description")) + m.group(2),
                 out, count=1)

    # 2. Hero H1 — real heading with the city name highlighted.
    out = out.replace(TEMPLATE_H1, f"<h1>{build_h1(row.get('h1_heading'), city)}</h1>")

    # 3. Drop the schema geo block (no coordinates in the export).
    out = re.sub(r'\s*"geo":\s*\{[^}]*\},', "", out, count=1)

    # 4. Phone: tel: links (bare digits) first, then the visible number.
    out = out.replace("tel:[PHONE]", "tel:" + tel_digits(phone))
    out = out.replace("[PHONE]", esc(phone))

    # 5. Remaining city/province tokens.
    out = out.replace("[CITY-SLUG]", slug)
    out = out.replace("[PROVINCE-ABBR]", esc(prov))
    out = out.replace("[PROVINCE]", esc(prov_full))
    out = out.replace("[NEIGHBORHOODS]", esc(row.get("neighbourhoods")))
    out = out.replace("[PARAGRAPH]", esc(row.get("local_paragraph")))
    out = out.replace("[CITY]", esc(city))

    # 6. Pricing overrides (only for cities that differ from the defaults).
    if rate1 != 85:
        out = out.replace("$85", "$" + str(rate1))
    if rate2 != 140:
        out = out.replace("$140", "$" + str(rate2))

    # 7. City blog section — posts tagged to this city (empty if none).
    section = city_blog_section(city, blog_by_city.get(slug.lower(), []))
    out = out.replace("<!--CITY_BLOG_SECTION-->", section)

    return out


def main():
    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()

    cities = sorted(load_cities(), key=lambda r: r.get("slug", ""))
    blog_by_city = load_blog_by_city()
    written = 0
    for row in cities:
        slug = row["slug"].strip()
        html_out = render(template, row, blog_by_city)
        leftover = set(re.findall(r"\[[A-Z\-]+\]", html_out))
        if leftover:
            print(f"  WARNING {slug}: unreplaced tokens {leftover}")
        out_dir = os.path.join(REPO, slug)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_out)
        written += 1
    print(f"Wrote {written} city pages.")


if __name__ == "__main__":
    main()
