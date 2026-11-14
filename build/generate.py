#!/usr/bin/env python3
"""Generate static city pages for Small Movers Canada.

Reads the canonical template (_template/city.html) and the base44 City export
(build/City_export.csv), swaps only city-specific content, and writes each city
to <slug>/index.html. Run from the repo root: python3 build/generate.py
"""
import csv
import html
import json
import os
import re
from urllib.parse import urlparse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(REPO, "_template", "city.html")
CSV_PATH = os.path.join(REPO, "build", "City_export.csv")
BLOG_CSV = os.path.join(REPO, "build", "Blog_export.csv")
REVIEWS_CSV = os.path.join(REPO, "build", "Reviews.csv")

# Per-province phone numbers (override whatever is in the CSV).
PROVINCE_PHONE = {
    "BC": "236-506-5898",
    "AB": "587-602-9862",
    "ON": "289-800-2197",
    "SK": "639-391-7969",
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
    "calgary": (100, 140),
    "barrie": (85, 150),    # Khalil (Sairon Logistics) — $85/hr 1 mover, $150/hr 2 movers
    "innisfil": (85, 150),  # Khalil (Sairon Logistics)
    "orillia": (85, 150),   # Khalil (Sairon Logistics)
    "bradford": (85, 150),  # Khalil (Sairon Logistics) — Bradford West Gwillimbury
    "newmarket": (85, 150), # Khalil (Sairon Logistics)
    "georgina": (85, 150),  # Khalil (Sairon Logistics)
    "wasaga-beach": (85, 150),  # Khalil (Sairon Logistics)
    "winnipeg": (90, 140),  # Vansh/Anmol Kapoor — $90 1 mover, $140 2 movers (1.5h min, see 6e)
}

# Per-city phone overrides — a dedicated number for a specific city (overrides the
# province number on that city page only). Used for per-city monetization trials.
CITY_PHONE_OVERRIDES = {
    "victoria": "778-400-7868",
    "calgary": "587-317-9080",
    "courtenay": "778-716-0061",
    "kelowna": "778-946-0968",
    "vernon": "778-946-0968",
    "kingston": "343-600-4428",  # Bill (eastern ON) — Twilio tracking number
    "saskatoon": "639-638-8439",  # Trigo (Meshack) — existing Saskatoon line (kept; SK default moved to the new Twilio)
    "barrie": "249-444-6102",  # Khalil (Sairon Logistics) — Twilio tracking # → +18078086110, src=BAR
    "innisfil": "249-444-6102",  # Khalil — shares the Barrie tracking line (src=BAR)
    "orillia": "249-444-6102",   # Khalil — shares the Barrie tracking line (src=BAR)
    "bradford": "249-444-6102",  # Khalil — shares the Barrie tracking line (src=BAR)
    "newmarket": "249-444-6102",  # Khalil — shares the Barrie tracking line (src=BAR)
    "georgina": "249-444-6102",  # Khalil — shares the Barrie tracking line (src=BAR)
    "wasaga-beach": "249-444-6102",  # Khalil — shares the Barrie tracking line (src=BAR)
    "warman": "639-638-8439",       # Trigo (Meshack) — shares the Saskatoon line
    "martensville": "639-638-8439", # Trigo (Meshack) — shares the Saskatoon line
    "thunder-bay": "807-700-3451",  # Steve Bourgoin (Perfect Brushes) — Twilio tracking # → +18073560091, src=TBY
    "ottawa": "343-429-6895",  # Salaman (A1 Property Solutions) — Twilio tracking # → +16137956969, src=OTT
    "nepean": "343-429-6895",  # Salaman — shares the Ottawa tracking line (src=OTT)
    "kanata": "343-429-6895",  # Salaman — shares the Ottawa tracking line (src=OTT)
    "orleans": "343-429-6895", # Salaman — shares the Ottawa tracking line (src=OTT)
}
# smallmovers.ontario (SW/Central ON) — one tracking number across those city pages.
for _slug in ["guelph", "hamilton", "kitchener", "brantford", "cambridge", "burlington",
              "niagara-falls", "st-catharines",
              "stoney-creek", "ancaster", "grimsby", "georgetown", "maple", "aurora",
              "port-dover", "binbrook", "caledonia", "acton", "st-jacobs", "smithville",
              "halton-hills"]:
    CITY_PHONE_OVERRIDES[_slug] = "289-780-3118"
# Sal (GTA) — now on his main tracking number (replaced Rolan's retired 365-694-5533).
for _slug in ["mississauga", "brampton", "etobicoke", "north-york", "vaughan", "oakville"]:
    CITY_PHONE_OVERRIDES[_slug] = "289-780-3118"
# smallmovers.ontario pricing (both groups above): default hourly rates, plus a flat
# $50 fuel/travel/equipment/insurance fee and a per-km charge beyond 10 km.
ON_PARTNER_SLUGS = ["guelph", "hamilton", "kitchener", "brantford", "cambridge", "burlington",
                    "niagara-falls", "st-catharines",
                    "mississauga", "brampton", "etobicoke", "north-york", "vaughan", "oakville",
                    "stoney-creek", "ancaster", "grimsby", "georgetown", "maple", "aurora",
                    "port-dover", "binbrook", "caledonia", "acton", "st-jacobs", "smithville",
                    "halton-hills"]
# Lower Mainland partner — one tracking number + his custom pricing across these pages.
LM_SLUGS = ["vancouver", "surrey", "north-vancouver", "richmond", "langley", "port-moody",
            "white-rock", "pitt-meadows", "coquitlam", "port-coquitlam", "burnaby", "delta",
            "new-westminster", "west-vancouver", "ladner", "tsawwassen", "abbotsford",
            "maple-ridge", "chilliwack"]
for _slug in LM_SLUGS:
    CITY_PHONE_OVERRIDES[_slug] = "236-707-8241"
    RATE_OVERRIDES[_slug] = (105, 145)  # $105/hr 1 mover, $145/hr 2 movers
# Edmonton partner (Sugam) pricing — $90/hr 1 mover, $140/hr 2 movers, 3-hour minimum,
# plus a $75 truck & fuel fee.
EDM_SLUGS = ["edmonton", "sherwood-park", "fort-saskatchewan", "leduc",
             "spruce-grove", "beaumont"]
for _slug in EDM_SLUGS:
    RATE_OVERRIDES[_slug] = (90, 140)
    CITY_PHONE_OVERRIDES[_slug] = "587-713-9768"  # Sugam's Edmonton-area tracking number

# New ON town pages (weekly rollout) routed to Sal — his tracking number + ON pricing.
SAL_BATCH_SLUGS = ["waterdown", "dundas", "welland", "thorold"]
for _slug in SAL_BATCH_SLUGS:
    CITY_PHONE_OVERRIDES[_slug] = "289-780-3118"
ON_PARTNER_SLUGS += SAL_BATCH_SLUGS

# Cities that have a dedicated Senior Moves landing page — a contextual link is
# injected into the city page (see render()).
SENIOR_MOVES = {"hamilton": "/hamilton/senior-moves/", "surrey": "/surrey/senior-moves/"}

# Bidirectional "nearby towns we serve" cross-links (slug -> neighbouring slugs).
# Each new town links to its neighbours, and each neighbour links back.
NEARBY = {
    # New batch-1 pages:
    "ladner": ["delta", "richmond", "surrey", "tsawwassen"],
    "tsawwassen": ["delta", "ladner", "richmond"],
    "waterdown": ["hamilton", "burlington"],
    "dundas": ["hamilton", "ancaster"],
    "welland": ["st-catharines", "niagara-falls", "thorold"],
    "thorold": ["st-catharines", "welland"],
    # Back-links added to existing parent pages:
    "delta": ["ladner", "tsawwassen"],
    "richmond": ["ladner", "tsawwassen"],
    "surrey": ["ladner"],
    "hamilton": ["waterdown", "dundas"],
    "burlington": ["waterdown"],
    "ancaster": ["dundas"],
    "st-catharines": ["welland", "thorold"],
    "niagara-falls": ["welland"],
    # Vancouver -> Lower Mainland neighbours (SEO internal linking).
    "vancouver": ["burnaby", "north-vancouver", "west-vancouver",
                  "new-westminster", "coquitlam", "delta"],
    # Khalil (Sairon Logistics) — Barrie / Simcoe corridor. 'newmarket' lights up
    # automatically once that page is built (missing pages are skipped).
    "barrie": ["innisfil", "orillia", "bradford", "newmarket", "wasaga-beach"],
    "innisfil": ["barrie", "orillia", "bradford"],
    "orillia": ["barrie", "innisfil", "wasaga-beach"],
    "bradford": ["barrie", "newmarket", "innisfil", "georgina"],
    "newmarket": ["bradford", "barrie", "georgina"],
    "georgina": ["newmarket", "bradford", "barrie"],
    "wasaga-beach": ["barrie", "orillia", "innisfil"],
    # Trigo (Meshack) — Saskatoon satellites.
    "warman": ["saskatoon", "martensville"],
    "martensville": ["saskatoon", "warman"],
    "saskatoon": ["warman", "martensville"],
    # Brad (Durham) — broad-SEO trial pages.
    "oshawa": ["whitby", "ajax", "pickering"],
    "ajax": ["pickering", "whitby", "oshawa"],
    "kawartha-lakes": ["oshawa", "peterborough"],
    # Sugam (Edmonton) — broad-SEO satellites around Edmonton.
    "sherwood-park": ["edmonton", "fort-saskatchewan", "spruce-grove"],
    "spruce-grove": ["edmonton", "leduc", "sherwood-park"],
    "leduc": ["edmonton", "beaumont", "spruce-grove"],
    "beaumont": ["edmonton", "leduc"],
    "fort-saskatchewan": ["edmonton", "sherwood-park"],
    "edmonton": ["sherwood-park", "spruce-grove", "leduc", "fort-saskatchewan", "beaumont"],
    "calgary": ["airdrie", "red-deer"],
    # Salaman (A1 Property Solutions) — Ottawa cluster.
    "kanata": ["ottawa", "nepean", "orleans"],
    "orleans": ["ottawa", "nepean", "kanata"],
    "ottawa": ["kanata", "orleans", "nepean"],
    "nepean": ["kanata", "orleans", "ottawa"],
    # Sal — Halton Hills cluster.
    "halton-hills": ["georgetown", "acton", "milton"],
    "georgetown": ["acton", "halton-hills", "milton"],
    "acton": ["georgetown", "halton-hills", "milton"],
}

# The canonical template's hero H1 (replaced wholesale with the city's real H1).
TEMPLATE_H1 = ('<h1>Small &amp; Hourly Movers&nbsp;in&nbsp;'
               '<span class="city-highlight">[CITY]</span></h1>')


def esc(s):
    """HTML-escape; safe in both element-text and attribute contexts."""
    return html.escape(s or "", quote=True)


def tel_digits(display):
    return "+1" + re.sub(r"\D", "", display)


def phone_paren(display):
    """Render a dash-style number as (XXX) XXX-XXXX for meta-description snippets."""
    d = re.sub(r"\D", "", display)
    if len(d) == 11 and d[0] == "1":
        d = d[1:]
    if len(d) != 10:
        return display
    return f"({d[0:3]}) {d[3:6]}-{d[6:10]}"


def nearby_section(slug, city_names):
    """Render the 'Nearby towns we serve' cross-link block (empty if none)."""
    links = []
    for ns in NEARBY.get(slug, []):
        name = city_names.get(ns)
        if name:
            links.append(
                f'<a href="/{ns}/" style="color:#2c7a5b; font-weight:700;">'
                f'{esc(name)} movers</a>')
    if not links:
        return ""
    joined = ' &nbsp;&middot;&nbsp; '.join(links)
    return (
        '<section style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:760px; text-align:center;">\n'
        '    <h2 style="margin-bottom:14px;">Nearby towns we serve</h2>\n'
        '    <p style="color:#3a4f63; margin-bottom:22px;">Moving to or from a '
        'neighbouring community? Our crews cover the whole area.</p>\n'
        f'    <p style="font-size:1.05rem; line-height:2;">{joined}</p>\n'
        '  </div>\n</section>\n\n'
    )


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


def load_reviews_by_city():
    """Map city_slug -> list of published reviews (newest first)."""
    if not os.path.exists(REVIEWS_CSV):
        return {}
    rows = list(csv.DictReader(open(REVIEWS_CSV, newline="", encoding="utf-8-sig")))
    by_city = {}
    for r in rows:
        if str(r.get("is_published", "true")).strip().lower() == "false":
            continue
        cslug = (r.get("city_slug") or "").strip().lower()
        if cslug:
            by_city.setdefault(cslug, []).append(r)
    for cslug in by_city:
        by_city[cslug].sort(key=lambda r: (r.get("date") or ""), reverse=True)
    return by_city


def city_reviews_section(city_name, reviews):
    """A 'Customer Reviews' section; empty string when the city has no reviews."""
    if not reviews:
        return ""
    cards = []
    for r in reviews:
        try:
            rating = int(float(r.get("rating") or 5))
        except (TypeError, ValueError):
            rating = 5
        rating = max(1, min(5, rating))
        stars = "★" * rating + "☆" * (5 - rating)
        author = esc(r.get("author") or "")
        loc = esc(r.get("location") or "")
        who = author + (f" &mdash; {loc}" if loc else "")
        cards.append(
            '<div class="review-card">\n'
            f'  <div class="review-stars" aria-label="{rating} out of 5 stars">{stars}</div>\n'
            f'  <p class="review-text">{esc(r.get("text"))}</p>\n'
            f'  <p class="review-author">{who}</p>\n'
            '</div>'
        )
    cards_html = "\n".join(cards)
    return (
        '<section class="city-reviews">\n'
        '  <div class="container">\n'
        '    <div style="text-align:center;"><span class="section-label">Customer Reviews</span></div>\n'
        f'    <h2 class="section-heading" style="text-align:center;">What Customers Say in {esc(city_name)}</h2>\n'
        f'    <div class="city-reviews-grid">\n{cards_html}\n    </div>\n'
        '  </div>\n</section>'
    )


# ---------------------------------------------------------------------------
# Page-specific SEO blocks (hand-written, injected only on the slugs listed).
# Injected AFTER the generic rate swaps in render(), so the literal rates in
# this copy are preserved exactly as written.
# ---------------------------------------------------------------------------

# Custom H2 content block, injected at <!--CITY_SEO_SECTION-->.
SEO_SECTIONS = {
    "kitchener": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Local Movers in Kitchener &amp; Waterloo</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">We are local movers '
        'serving Kitchener, Waterloo, Cambridge and the Guelph area. Our crews know the region, '
        'from downtown Kitchener apartments to Uptown Waterloo condos and the student '
        'neighbourhoods near the universities. Because we charge by the hour with a right-sized '
        'crew, a small move across town does not cost what a full-service van line charges.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Moving a little further out? We also cover '
        '<a href="/cambridge/" style="color:#2c7a5b; font-weight:700;">Cambridge movers</a> and '
        '<a href="/guelph/" style="color:#2c7a5b; font-weight:700;">Guelph movers</a>, with the '
        'same hourly pricing and small-move focus.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "vancouver": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Affordable Small Moves in Vancouver</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Small moves cost less '
        'with us because we do not send a five-ton truck and a four-person crew for a job that does '
        'not need one. You get a right-sized crew, an hourly rate of $105/hr for one mover or '
        '$145/hr for two movers plus a truck, and a low minimum, so you only pay for the time your '
        'move actually takes.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">That is what keeps a studio, apartment or '
        'single-item move in Vancouver genuinely affordable: no big-truck overhead and no padded '
        'estimates, just honest hourly pricing.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "warman": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Warman and Saskatoon</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">A lot of our Warman jobs '
        'are short hops to or from Saskatoon &mdash; a first apartment in the city, a move back home '
        'to Warman, or a growing family upsizing. Because we bill by the hour with a right-sized crew '
        'instead of a full van line, a Warman&ndash;Saskatoon move usually costs a fraction of what '
        'the big companies quote.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Moving within town or a little further out? '
        'We also cover <a href="/saskatoon/" style="color:#2c7a5b; font-weight:700;">Saskatoon '
        'movers</a> and <a href="/martensville/" style="color:#2c7a5b; font-weight:700;">Martensville '
        'movers</a>, with the same hourly pricing and small-move focus. Give us both addresses when '
        'you request a quote and we will send back an honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "martensville": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Martensville and Saskatoon</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Many Martensville moves '
        'are quick trips to or from Saskatoon &mdash; students heading into the city, or families '
        'moving out to Martensville for more space. With by-the-hour pricing and a crew sized to the '
        'job, a Martensville&ndash;Saskatoon move costs far less than a traditional van line.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Staying local or heading further? We also '
        'cover <a href="/saskatoon/" style="color:#2c7a5b; font-weight:700;">Saskatoon movers</a> and '
        '<a href="/warman/" style="color:#2c7a5b; font-weight:700;">Warman movers</a>, same hourly '
        'rate and small-move focus. Send both addresses with your quote request and we will give you '
        'a flat, honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "sherwood-park": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Sherwood Park and Edmonton</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">A lot of our Sherwood Park '
        'jobs run to or from Edmonton &mdash; a move into the city for work, or out to Sherwood Park for '
        'more room and a quieter street. Because we charge by the hour with a right-sized crew instead of '
        'a full van line, a short Sherwood Park&ndash;Edmonton move costs far less than the big companies '
        'quote.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Staying local or heading a little further? We '
        'also cover <a href="/edmonton/" style="color:#2c7a5b; font-weight:700;">Edmonton movers</a> and '
        '<a href="/fort-saskatchewan/" style="color:#2c7a5b; font-weight:700;">Fort Saskatchewan '
        'movers</a>, with the same hourly pricing and small-move focus. Give us both addresses when you '
        'request a quote and we will send back an honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "spruce-grove": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Spruce Grove and Edmonton</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Many Spruce Grove moves are '
        'quick trips to or from Edmonton &mdash; a first apartment in the city, or a family moving west '
        'for more space. With by-the-hour pricing and a crew sized to the job, a Spruce '
        'Grove&ndash;Edmonton move costs far less than a traditional van line.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Staying in town or heading further? We also cover '
        '<a href="/edmonton/" style="color:#2c7a5b; font-weight:700;">Edmonton movers</a> and '
        '<a href="/leduc/" style="color:#2c7a5b; font-weight:700;">Leduc movers</a>, with the same hourly '
        'rate and small-move focus. Send both addresses with your quote request and we will give you an '
        'honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "leduc": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Leduc and Edmonton</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Plenty of our Leduc jobs run '
        'to or from Edmonton &mdash; a move into the city, or out to Leduc near the airport and more '
        'affordable homes. Because we bill by the hour with a right-sized crew instead of a full van '
        'line, a Leduc&ndash;Edmonton move usually costs a fraction of what the big companies quote.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Moving within town or a little further out? We '
        'also cover <a href="/edmonton/" style="color:#2c7a5b; font-weight:700;">Edmonton movers</a> and '
        '<a href="/beaumont/" style="color:#2c7a5b; font-weight:700;">Beaumont movers</a>, with the same '
        'hourly pricing and small-move focus. Give us both addresses and we will send back a flat, honest '
        'estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "beaumont": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Beaumont and Edmonton</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">A lot of Beaumont moves are '
        'short hops to or from Edmonton &mdash; a growing family upsizing, or a move out to Beaumont for '
        'the small-town feel. With hourly pricing and a crew sized to the job, a Beaumont&ndash;Edmonton '
        'move costs far less than a full van line.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Staying local or heading further? We also cover '
        '<a href="/edmonton/" style="color:#2c7a5b; font-weight:700;">Edmonton movers</a> and '
        '<a href="/leduc/" style="color:#2c7a5b; font-weight:700;">Leduc movers</a>, same hourly rate and '
        'small-move focus. Send both addresses with your quote request and we will give you an honest '
        'estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "fort-saskatchewan": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Fort Saskatchewan and Edmonton</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Many Fort Saskatchewan jobs '
        'run to or from Edmonton &mdash; a move into the city for work, or out to the Fort for more '
        'space. Because we charge by the hour with a right-sized crew instead of a full van line, a short '
        'Fort Saskatchewan&ndash;Edmonton move costs far less than the big companies quote.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Staying local or heading a little further? We '
        'also cover <a href="/edmonton/" style="color:#2c7a5b; font-weight:700;">Edmonton movers</a> and '
        '<a href="/sherwood-park/" style="color:#2c7a5b; font-weight:700;">Sherwood Park movers</a>, with '
        'the same hourly pricing and small-move focus. Give us both addresses and we will send back an '
        'honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "innisfil": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Innisfil and Barrie</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Plenty of our Innisfil '
        'jobs run to or from Barrie &mdash; a move into the city for work, or out to Innisfil for the '
        'lake and more space. Because we charge by the hour with a right-sized crew instead of a full '
        'van line, a short Innisfil&ndash;Barrie move costs far less than the big companies quote.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Staying in town or heading up the corridor? '
        'We also cover <a href="/barrie/" style="color:#2c7a5b; font-weight:700;">Barrie movers</a> '
        'and <a href="/bradford/" style="color:#2c7a5b; font-weight:700;">Bradford movers</a>, with '
        'the same hourly pricing and small-move focus. Give us both addresses with your quote and we '
        'will send an honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "orillia": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Orillia and Barrie</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Many Orillia moves are '
        'short trips down to Barrie or back up to the lakes &mdash; a new job, a first apartment, or '
        'a family resizing. With by-the-hour pricing and a crew sized to the job, an '
        'Orillia&ndash;Barrie move costs a fraction of a traditional van line.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Moving within Orillia or further afield? We '
        'also cover <a href="/barrie/" style="color:#2c7a5b; font-weight:700;">Barrie movers</a> and '
        '<a href="/innisfil/" style="color:#2c7a5b; font-weight:700;">Innisfil movers</a> on the same '
        'hourly rate. Send both addresses with your quote request for a flat, honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "oshawa": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Oshawa and Toronto</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">A lot of our Oshawa jobs '
        'run along the GO line to or from Toronto &mdash; a first apartment downtown, a move back out '
        'to Durham for more space, or a growing family resizing. Because we bill by the hour with a '
        'right-sized crew instead of a full van line, an Oshawa&ndash;Toronto move usually costs a '
        'fraction of what the big companies quote.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Moving within Durham instead? We also cover '
        '<a href="/whitby/" style="color:#2c7a5b; font-weight:700;">Whitby movers</a> and '
        '<a href="/pickering/" style="color:#2c7a5b; font-weight:700;">Pickering movers</a>, with the '
        'same hourly pricing and small-move focus. Give us both addresses when you request a quote and '
        'we will send back an honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "ajax": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Ajax and Toronto</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Many Ajax moves are short '
        'trips to or from Toronto &mdash; a commute-driven move into the city, or back out to Ajax for '
        'more room. With by-the-hour pricing and a crew sized to the job, an Ajax&ndash;Toronto move '
        'costs far less than a traditional van line.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Staying closer to home? We also cover '
        '<a href="/pickering/" style="color:#2c7a5b; font-weight:700;">Pickering movers</a> and '
        '<a href="/whitby/" style="color:#2c7a5b; font-weight:700;">Whitby movers</a> on the same '
        'hourly rate. Send both addresses with your quote request and we will give you a flat, honest '
        'estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "kawartha-lakes": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Kawartha Lakes and the GTA</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">A lot of Kawartha Lakes '
        'moves are trips out of the GTA &mdash; families and retirees leaving the city for more space '
        'and lake country around Lindsay, Fenelon Falls and Bobcaygeon. Because we bill by the hour '
        'with a right-sized crew, a move between Kawartha Lakes and the GTA usually costs far less '
        'than a full-service van line.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Moving locally or nearby? We also cover '
        '<a href="/oshawa/" style="color:#2c7a5b; font-weight:700;">Oshawa movers</a> and '
        '<a href="/peterborough/" style="color:#2c7a5b; font-weight:700;">Peterborough movers</a>, '
        'with the same hourly pricing and small-move focus. Give us both addresses with your quote '
        'and we will send an honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
    "bradford": (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        '    <h2 style="margin-bottom:16px;">Moving Between Bradford and Barrie</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">A lot of Bradford moves '
        'run along the GO corridor &mdash; up to Barrie or down toward Newmarket and the GTA. Because '
        'we bill by the hour with a right-sized crew, a short Bradford move usually costs far less '
        'than a full-service van line.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Staying in Bradford or moving nearby? We also '
        'cover <a href="/barrie/" style="color:#2c7a5b; font-weight:700;">Barrie movers</a> and '
        '<a href="/newmarket/" style="color:#2c7a5b; font-weight:700;">Newmarket movers</a>, with the '
        'same hourly pricing and small-move focus. Give us both addresses with your quote and we will '
        'send back an honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    ),
}


# ---- ON under-120k broad rollout (2026-11-06) ----------------------------
# Generated inter-city / local SEO sections for the Ontario satellite pages
# flipped to the "Movers in [City]" head-term style. Each hub entry carries a
# unique hook sentence so the pages are not boilerplate; standalone cities get
# a local "Small Moves in [City]" section instead.
def _mk_intercity(city, hub, hub_slug, hook, sib, sib_slug):
    return (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        f'    <h2 style="margin-bottom:16px;">Moving Between {city} and {hub}</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">'
        f'{hook} &mdash; and because we bill by the hour with a right-sized crew instead of a full van '
        f'line, a short {city}&ndash;{hub} move usually costs a fraction of what the big companies '
        'quote. A studio, an apartment, a condo or a few big items &mdash; you only pay for the time '
        'the move actually takes.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">Staying in town or heading a little further? '
        f'We also cover <a href="/{hub_slug}/" style="color:#2c7a5b; font-weight:700;">{hub} movers</a> '
        f'and <a href="/{sib_slug}/" style="color:#2c7a5b; font-weight:700;">{sib} movers</a>, with the '
        'same hourly pricing and small-move focus. Give us both addresses when you request a quote and '
        'we will send back an honest estimate.</p>\n'
        '  </div>\n</section>\n\n'
    )


def _mk_local(city, hook):
    return (
        '<section class="local-seo" style="padding:56px 20px;">\n'
        '  <div class="container" style="max-width:820px;">\n'
        f'    <h2 style="margin-bottom:16px;">Small Moves in {city}</h2>\n'
        '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">'
        f'{hook} Most moves here are smaller jobs &mdash; a one-bedroom, a condo, a single-item '
        f'delivery or a few rooms of furniture &mdash; and those do not need a five-ton truck and a '
        'four-person crew. We bring a right-sized crew and charge by the hour, so you are not paying '
        'for space and time your move never uses.</p>\n'
        '    <p style="color:#3a4f63; line-height:1.8;">That is what keeps a small or local move in '
        f'{city} genuinely affordable: no big-truck overhead and no padded estimates, just honest '
        'hourly pricing with a low minimum.</p>\n'
        '  </div>\n</section>\n\n'
    )


# slug: (City, Hub, hub_slug, hook, Sibling, sib_slug)
_ON_HUB = [
    ("ancaster", "Ancaster", "Hamilton", "hamilton", "Ancaster sits right against Hamilton's west end, so a lot of our jobs here are quick moves to or from the city", "Dundas", "dundas"),
    ("dundas", "Dundas", "Hamilton", "hamilton", "Dundas runs straight into Hamilton at the bottom of the valley, and plenty of moves cross between the two", "Ancaster", "ancaster"),
    ("stoney-creek", "Stoney Creek", "Hamilton", "hamilton", "Stoney Creek is Hamilton's east end now, so moves between the two are short, everyday trips", "Binbrook", "binbrook"),
    ("waterdown", "Waterdown", "Hamilton", "hamilton", "Waterdown sits on the edge of Hamilton and Burlington, so short hops into either are common", "Dundas", "dundas"),
    ("binbrook", "Binbrook", "Hamilton", "hamilton", "Binbrook is Hamilton's fast-growing south end, with new families moving out from the city", "Stoney Creek", "stoney-creek"),
    ("caledonia", "Caledonia", "Hamilton", "hamilton", "Caledonia is a short run down the Grand River from Hamilton", "Binbrook", "binbrook"),
    ("grimsby", "Grimsby", "Hamilton", "hamilton", "Grimsby sits between Hamilton and the Niagara wineries, an easy move in either direction", "Stoney Creek", "stoney-creek"),
    ("niagara-falls", "Niagara Falls", "St. Catharines", "st-catharines", "Niagara Falls and St. Catharines are a quick trip apart along the QEW", "Welland", "welland"),
    ("welland", "Welland", "St. Catharines", "st-catharines", "Welland sits just south of St. Catharines, so moves between the two are short runs", "Thorold", "thorold"),
    ("thorold", "Thorold", "St. Catharines", "st-catharines", "Thorold sits right between St. Catharines and Welland", "Welland", "welland"),
    ("smithville", "Smithville", "St. Catharines", "st-catharines", "Smithville is a short drive from both Grimsby and the St. Catharines area", "Grimsby", "grimsby"),
    ("aurora", "Aurora", "Toronto", "toronto", "Aurora sits on the GO line north of Toronto, so plenty of moves run down into the city", "Newmarket", "newmarket"),
    ("maple", "Maple", "Vaughan", "vaughan", "Maple is part of Vaughan, and many moves stay within the city or head next door", "Richmond Hill", "richmond-hill"),
    ("whitchurch-stouffville", "Whitchurch-Stouffville", "Markham", "markham", "Stouffville is a short hop from Markham on the north edge of York Region", "Aurora", "aurora"),
    ("pickering", "Pickering", "Toronto", "toronto", "Pickering sits between Toronto and Ajax on the lakeshore, an easy move either way", "Ajax", "ajax"),
    ("acton", "Acton", "Georgetown", "georgetown", "Acton and Georgetown are the two halves of Halton Hills", "Milton", "milton"),
    ("georgetown", "Georgetown", "Milton", "milton", "Georgetown sits right beside Milton in Halton Hills", "Acton", "acton"),
    ("st-jacobs", "St. Jacobs", "Kitchener", "kitchener", "St. Jacobs is just north of Waterloo and Kitchener", "Cambridge", "cambridge"),
    ("clarington", "Clarington", "Oshawa", "oshawa", "Clarington sits just east of Oshawa, so Bowmanville and Courtice moves often run into Durham", "Whitby", "whitby"),
    ("east-york", "East York", "Toronto", "toronto", "East York is central Toronto, so most moves here are short cross-town trips", "Scarborough", "scarborough"),
    ("kanata", "Kanata", "Ottawa", "ottawa", "Kanata is Ottawa's tech hub out west, so plenty of our jobs here run into the city or between the west-end suburbs", "Nepean", "nepean"),
    ("orleans", "Orléans", "Ottawa", "ottawa", "Orléans is Ottawa's fast-growing east end, and many moves run to or from downtown or the other suburbs", "Nepean", "nepean"),
    ("georgina", "Georgina", "Newmarket", "newmarket", "Georgina sits on the south shore of Lake Simcoe, so a lot of our jobs here run down to Newmarket, Aurora and the rest of York Region", "Bradford", "bradford"),
    ("wasaga-beach", "Wasaga Beach", "Barrie", "barrie", "Wasaga Beach sits on Georgian Bay northwest of Barrie, so plenty of moves run between the beach town and the city", "Orillia", "orillia"),
    ("halton-hills", "Halton Hills", "Milton", "milton", "Halton Hills — Georgetown and Acton — sits right next to Milton, so plenty of moves cross between them", "Georgetown", "georgetown"),
]
for _slug, _city, _hub, _hubslug, _hook, _sib, _sibslug in _ON_HUB:
    SEO_SECTIONS[_slug] = _mk_intercity(_city, _hub, _hubslug, _hook, _sib, _sibslug)

# slug: (City, hook)
_ON_LOCAL = [
    ("brantford", "Brantford", "Brantford is a working river city on the western edge of the Golden Horseshoe."),
    ("chatham-kent", "Chatham-Kent", "Chatham-Kent spreads across a string of small communities between Windsor and London."),
    ("thunder-bay", "Thunder Bay", "Thunder Bay sits on its own at the head of the lake, a long way from the southern cities."),
    ("peterborough", "Peterborough", "Peterborough is the hub of the Kawarthas, with students, downtown apartments and lakeside homes."),
    ("belleville", "Belleville", "Belleville sits on the Bay of Quinte, halfway between Toronto and Kingston."),
    ("sarnia", "Sarnia", "Sarnia sits on the water where Lake Huron meets the St. Clair River."),
    ("port-dover", "Port Dover", "Port Dover is a small Lake Erie town that doubles in size every summer."),
]
for _slug, _city, _hook in _ON_LOCAL:
    SEO_SECTIONS[_slug] = _mk_local(_city, _hook)

# Edmonton & Calgary refresh (2026-11-13) — added depth sections + internal links.
SEO_SECTIONS["edmonton"] = (
    '<section class="local-seo" style="padding:56px 20px;">\n'
    '  <div class="container" style="max-width:820px;">\n'
    '    <h2 style="margin-bottom:16px;">Small Moves Across Edmonton &amp; Area</h2>\n'
    '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Most of our Edmonton jobs are '
    'the small, specific moves the big van lines either turn down or overcharge for &mdash; a mattress or '
    'couch across town, a studio or one-bedroom apartment, a condo downsizing, or a reno\'s worth of '
    'furniture into storage. Because we send a right-sized crew and bill by the hour, you are not paying '
    'five-ton-truck rates for a half-ton job.</p>\n'
    '    <p style="color:#3a4f63; line-height:1.8;">We cover the whole city and the surrounding '
    'communities with the same hourly pricing, so a move out to '
    '<a href="/sherwood-park/" style="color:#2c7a5b; font-weight:700;">Sherwood Park movers</a>, '
    '<a href="/spruce-grove/" style="color:#2c7a5b; font-weight:700;">Spruce Grove movers</a> or '
    '<a href="/leduc/" style="color:#2c7a5b; font-weight:700;">Leduc movers</a> costs the same honest '
    'rate as a move within Edmonton. Give us the pickup and drop-off and we will send back a quick, flat '
    'estimate.</p>\n'
    '  </div>\n</section>\n\n'
)
SEO_SECTIONS["calgary"] = (
    '<section class="local-seo" style="padding:56px 20px;">\n'
    '  <div class="container" style="max-width:820px;">\n'
    '    <h2 style="margin-bottom:16px;">Small Moves Across Calgary &amp; Area</h2>\n'
    '    <p style="color:#3a4f63; line-height:1.8; margin-bottom:16px;">Calgary\'s small-move market is '
    'exactly what we are built for &mdash; the single-item deliveries, studio and one-bedroom moves, and '
    'condo downsizings that do not need a full crew and a five-ton truck. We bill by the hour with no '
    'truck minimums, so a Beltline condo or a Kensington walk-up costs only the time it actually takes, '
    'not a padded flat rate.</p>\n'
    '    <p style="color:#3a4f63; line-height:1.8;">We also cover the towns around the city, so whether '
    'you are moving within Calgary or out to '
    '<a href="/airdrie/" style="color:#2c7a5b; font-weight:700;">Airdrie movers</a>, it is the same '
    'by-the-hour pricing. Send us both addresses and we will come back with an honest quote.</p>\n'
    '  </div>\n</section>\n\n'
)


# FAQ items per slug: (question, answer). Injected at <!--CITY_FAQ_SECTION-->
# as both a visible section and FAQPage JSON-LD.
FAQS = {
    "kitchener": [
        ("How much do movers cost in Kitchener?",
         "Our small moves start at $85/hr for one mover and $140/hr for two movers. A $50 flat fee "
         "covers fuel, travel, equipment and insurance, with 10 km included and $1.50/km after that."),
        ("Is there a minimum number of hours?",
         "Two movers have a 2.5-hour minimum, which we waive for single-item and in-home moves. One "
         "mover starts at a 1-hour minimum."),
        ("Can you move a single item?",
         "Yes. Single-item moves such as a couch, a fridge or an appliance are one of the most common "
         "jobs we do, and the 2.5-hour minimum is waived for them."),
        ("Do you move on weekends?",
         "Yes. We book 7 days a week, including evenings and weekends, subject to availability."),
        ("How quickly can I book a move?",
         "Often same-day or next-day, depending on the schedule. Send a quick quote request and we "
         "will confirm the soonest slot."),
    ],
    "vancouver": [
        ("How much do cheap movers cost in Vancouver?",
         "Our small moves are $105/hr for one mover and $145/hr for two movers plus a truck. You pay "
         "by the hour with no big-truck overhead, which keeps a small move affordable."),
        ("Is there a minimum number of hours?",
         "One mover has a 2-hour minimum. Two movers plus a truck have a 2.5-hour minimum."),
        ("Can you move just one item?",
         "Yes. Single pieces like a couch, a bed or an appliance are a common job for our right-sized "
         "crews."),
        ("Do you offer same-day moves in Vancouver?",
         "Often yes, depending on the day's schedule. Send a quote request and we will confirm the "
         "soonest availability."),
    ],
}


def seo_section(slug):
    """Hand-written SEO H2 block for a specific page (empty if none)."""
    return SEO_SECTIONS.get(slug, "")


def faq_section(slug):
    """Visible FAQ section + FAQPage JSON-LD for a specific page (empty if none)."""
    items = FAQS.get(slug)
    if not items:
        return ""
    cards = []
    for q, a in items:
        cards.append(
            '      <div style="margin-bottom:26px;">\n'
            f'        <h3 style="margin-bottom:8px; color:#0E2A47;">{esc(q)}</h3>\n'
            f'        <p style="color:#3a4f63; line-height:1.7;">{esc(a)}</p>\n'
            '      </div>'
        )
    body = "\n".join(cards)
    jsonld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in items
        ],
    }
    script = json.dumps(jsonld, ensure_ascii=False, indent=2)
    return (
        '<section class="faq" id="faq" style="padding:64px 20px; background:#F6F1E7;">\n'
        '  <div class="container" style="max-width:760px;">\n'
        '    <h2 class="section-heading" style="text-align:center;">Frequently Asked Questions</h2>\n'
        '    <div style="margin-top:32px;">\n'
        f'{body}\n'
        '    </div>\n'
        '  </div>\n'
        f'  <script type="application/ld+json">\n{script}\n  </script>\n'
        '</section>\n\n'
    )


def render(template, row, blog_by_city, reviews_by_city, city_names):
    city = (row.get("city_name") or "").strip()
    slug = (row.get("slug") or "").strip()
    prov = (row.get("province") or "").strip()
    prov_full = (row.get("province_full") or "").strip() or PROVINCE_FULL.get(prov, prov)
    phone = CITY_PHONE_OVERRIDES.get(slug) or PROVINCE_PHONE.get(prov, (row.get("phone_number") or "").strip())
    rate1, rate2 = RATE_OVERRIDES.get(slug, (85, 140))

    out = template

    # 1. SEO <title> and meta description — use the real CMS values verbatim.
    out = re.sub(r"<title>.*?</title>",
                 lambda m: f"<title>{esc(row.get('meta_title'))}</title>",
                 out, count=1, flags=re.DOTALL)
    # Swap any phone number baked into the CMS meta description for this city's
    # real tracking number, so search snippets never advertise the wrong line.
    meta_desc = esc(row.get("meta_description"))
    meta_desc = re.sub(r'\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}', phone_paren(phone), meta_desc)
    out = re.sub(r'(<meta name="description" content=")[^"]*(">)',
                 lambda m: m.group(1) + meta_desc + m.group(2),
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

    # 6b. Lower Mainland partner pricing — different minimums + inclusions.
    if slug in LM_SLUGS:
        out = out.replace("for 1 mover (1 hour minimum)",
                          "for 1 mover (2 hour minimum)")
        out = out.replace("for 2 movers (2.5 hour minimum)",
                          "for 2 movers + truck (2.5 hour minimum)")
        out = out.replace("Truck, equipment &amp; insurance included",
                          "Truck, equipment, blankets &amp; basic assembly included")

    # 6c. smallmovers.ontario pricing — flat fee + per-km charge instead of "included".
    if slug in ON_PARTNER_SLUGS:
        out = out.replace(
            "<li>Truck, equipment &amp; insurance included</li>",
            "<li>$50 flat fee covers fuel, travel, equipment &amp; insurance</li>\n"
            "            <li>10 km included, then $1.50/km</li>\n"
            "            <li>2.5-hour minimum waived for single-item and in-home moves</li>")
        out = out.replace("</span> No hidden fees</span>",
                          "</span> $50 flat travel fee</span>")

    # 6d. Edmonton partner (Sugam) pricing — 3-hour minimum + $75 truck & fuel fee.
    if slug in EDM_SLUGS:
        out = out.replace("for 1 mover (1 hour minimum)",
                          "for 1 mover (3 hour minimum)")
        out = out.replace("for 2 movers (2.5 hour minimum)",
                          "for 2 movers (3 hour minimum)")
        out = out.replace("<li>Truck, equipment &amp; insurance included</li>",
                          "<li>$75 truck &amp; fuel fee</li>")
        out = out.replace("</span> No hidden fees</span>",
                          "</span> $75 truck &amp; fuel fee</span>")

    # 6e. Winnipeg partner (Vansh/Anmol Kapoor) — 2-mover minimum 1.5h instead of 2.5h.
    if slug == "winnipeg":
        out = out.replace("for 2 movers (2.5 hour minimum)",
                          "for 2 movers (1.5 hour minimum)")

    # 6f. Kingston partner (Ibrahim) — 2-mover minimum 1h instead of 2.5h.
    if slug == "kingston":
        out = out.replace("for 2 movers (2.5 hour minimum)",
                          "for 2 movers (1 hour minimum)")

    # 7. City reviews section — reviews tagged to this city (empty if none).
    reviews = city_reviews_section(city, reviews_by_city.get(slug.lower(), []))
    out = out.replace("<!--CITY_REVIEWS_SECTION-->", reviews)

    # 8. City blog section — posts tagged to this city (empty if none).
    section = city_blog_section(city, blog_by_city.get(slug.lower(), []))
    out = out.replace("<!--CITY_BLOG_SECTION-->", section)

    # 9. Contextual link to the Senior Moves page (cities that have one):
    #    link the "Senior Moves" service card, plus a banner before the final CTA.
    if slug in SENIOR_MOVES:
        su = SENIOR_MOVES[slug]
        out = out.replace(
            '<h3>Senior Moves</h3>\n'
            '        <p>Patient, careful movers who treat your belongings with respect.</p>',
            '<h3>Senior Moves</h3>\n'
            '        <p>Patient, careful movers who treat your belongings with respect. '
            f'<a href="{su}" style="color:#2c7a5b; font-weight:700;">See our {esc(city)} senior moves page &rarr;</a></p>',
            1)
        banner = (
            '<section style="background:#F6F1E7; padding:44px 20px; text-align:center;">\n'
            '  <div class="container">\n'
            '    <p style="color:#3a4f63; font-size:1.05rem; line-height:1.7; max-width:640px; margin:0 auto;">'
            'Moving a parent into a retirement residence? See our '
            f'<a href="{su}" style="color:#2c7a5b; font-weight:700;">{esc(city)} senior moves</a> page '
            'for what is included, suite setup, rates, and a list of local residences.</p>\n'
            '  </div>\n</section>\n\n'
        )
        out = out.replace('<section class="final-cta">', banner + '<section class="final-cta">', 1)

    # 10. "Nearby towns we serve" cross-links (new town pages + their parents).
    nearby = nearby_section(slug, city_names)
    if nearby:
        out = out.replace('<section class="final-cta">', nearby + '<section class="final-cta">', 1)

    # 11. Hand-written SEO section + FAQ (specific pages only). Done after the
    #     rate swaps so the literal rates in this copy are preserved. The markers
    #     are consumed together with their surrounding newlines so pages without
    #     a block are byte-identical to the pre-feature output (no diff noise).
    seo = seo_section(slug)
    out = out.replace("\n\n<!--CITY_SEO_SECTION-->", ("\n\n" + seo) if seo else "")
    out = out.replace("<!--CITY_FAQ_SECTION-->\n", faq_section(slug))

    return out


def main():
    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()

    cities = sorted(load_cities(), key=lambda r: r.get("slug", ""))
    blog_by_city = load_blog_by_city()
    reviews_by_city = load_reviews_by_city()
    city_names = {(r.get("slug") or "").strip(): (r.get("city_name") or "").strip()
                  for r in cities}
    written = 0
    for row in cities:
        slug = row["slug"].strip()
        html_out = render(template, row, blog_by_city, reviews_by_city, city_names)
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
