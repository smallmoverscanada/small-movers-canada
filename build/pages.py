#!/usr/bin/env python3
"""Generate the national marketing pages (homepage for now) for Small Movers Canada.

Reuses the shared CSS from _template/city.html so the look stays in lock-step with
the city pages, builds a national header/footer, and pulls the city list from the
same City export. Run from repo root: python3 build/pages.py
"""
import ast
import csv
import datetime as _dt
import html
import os
import re
from urllib.parse import urlparse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(REPO, "_template", "city.html")
CSV_PATH = os.path.join(REPO, "build", "City_export.csv")

PROVINCE_PHONE = {
    "BC": "236-506-5898",
    "AB": "587-602-9862",
    "ON": "289-800-2197",
    "SK": "639-638-8439",
    "MB": "431-441-8631",
}
PROVINCE_FULL = {"BC": "British Columbia", "AB": "Alberta", "ON": "Ontario",
                 "SK": "Saskatchewan", "MB": "Manitoba"}
PROVINCE_SLUG = {"BC": "british-columbia", "AB": "alberta", "ON": "ontario",
                 "SK": "saskatchewan", "MB": "manitoba"}
# Display order for province sections.
PROVINCE_ORDER = ["BC", "AB", "ON", "SK", "MB"]

GTM = "GTM-NV977B6T"


def esc(s):
    return html.escape(s or "", quote=True)


def tel(display):
    return "+1" + re.sub(r"\D", "", display)


def shared_style():
    """Pull the <style> block out of the city template so CSS stays identical."""
    src = open(TEMPLATE, encoding="utf-8").read()
    m = re.search(r"<style>(.*?)</style>", src, re.DOTALL)
    return m.group(1)


def load_cities():
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    best = {}
    for r in rows:
        slug = (r.get("slug") or "").strip()
        if not slug:
            continue
        key = (r.get("updated_date") or "", len(r.get("local_paragraph") or ""))
        if slug not in best or key > best[slug][0]:
            best[slug] = (key, r)
    return [v[1] for v in best.values()]


ARROW = ('<svg class="loc-arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" '
         'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
         'stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/>'
         '<polyline points="12 5 19 12 12 19"/></svg>')
PIN = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
       '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
       '<circle cx="12" cy="10" r="3"/></svg>')


def city_grid(cities):
    by_prov = {}
    for c in cities:
        by_prov.setdefault((c.get("province") or "").strip(), []).append(c)
    blocks = []
    for prov in PROVINCE_ORDER:
        items = by_prov.get(prov, [])
        if not items:
            continue
        items.sort(key=lambda c: c.get("city_name", ""))
        cards = "\n".join(
            f'<a class="loc-card" href="/{c["slug"].strip()}/" data-city="{esc(c.get("city_name"))}">'
            f'<span><span class="loc-city">{esc(c.get("city_name"))}</span>'
            f'<span class="loc-prov">{esc(prov)}</span></span>{ARROW}</a>'
            for c in items
        )
        full = esc(PROVINCE_FULL.get(prov, prov))
        pslug = PROVINCE_SLUG.get(prov, "")
        blocks.append(
            f'<div class="loc-province">\n'
            f'  <h3><span class="loc-pin">{PIN}</span>'
            f'<a href="/{pslug}/">{full}</a></h3>\n'
            f'  <div class="loc-grid">\n{cards}\n  </div>\n</div>'
        )
    return "\n".join(blocks)


def city_search():
    return '''    <div class="city-search">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input type="text" id="citySearch" placeholder="Search your city…" autocomplete="off" aria-label="Search for your city">
    </div>
    <p class="city-search-empty" hidden>No matching cities — try a different spelling.</p>'''


# Filters the city cards live as the visitor types; hides empty province sections.
CITY_SEARCH_JS = '''
<script>
(function () {
  var input = document.getElementById('citySearch');
  if (!input) return;
  var cards = [].slice.call(document.querySelectorAll('.loc-card'));
  var provinces = [].slice.call(document.querySelectorAll('.loc-province'));
  var empty = document.querySelector('.city-search-empty');
  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase();
    var anyVisible = false;
    cards.forEach(function (card) {
      var name = (card.getAttribute('data-city') || '').toLowerCase();
      var show = !q || name.indexOf(q) !== -1;
      card.style.display = show ? '' : 'none';
      if (show) anyVisible = true;
    });
    provinces.forEach(function (sec) {
      var hasVisible = [].slice.call(sec.querySelectorAll('.loc-card'))
        .some(function (c) { return c.style.display !== 'none'; });
      sec.style.display = hasVisible ? '' : 'none';
    });
    if (empty) empty.hidden = anyVisible || !q;
  });
})();
</script>'''


HOME_CSS = """
/* ── Marketing pages ──────────────────────── */
.home-hero { background:#0E2A47; color:#fff; padding:72px 20px 84px; text-align:center; position:relative; overflow:hidden; }
.home-hero::after { content:''; position:absolute; bottom:-2px; left:0; right:0; height:52px; background:#F6F1E7; clip-path:ellipse(60% 100% at 50% 100%); }
.home-hero .inner { max-width:880px; margin:0 auto; position:relative; }
.home-hero h1 { font-size:clamp(2rem,5.5vw,3.4rem); font-weight:800; color:#fff; margin:0 auto 18px; }
.home-hero .sub { font-size:1.1rem; color:rgba(255,255,255,0.75); max-width:600px; margin:0 auto 30px; line-height:1.6; }
.home-cta-row { display:flex; flex-direction:column; align-items:center; gap:12px; margin-bottom:34px; }
.home-hero .hero-pills { justify-content:center; }
.btn-outline-light { display:inline-flex; align-items:center; gap:8px; background:transparent; color:#fff; font-weight:600; font-size:0.95rem; padding:13px 26px; border-radius:10px; border:2px solid rgba(255,255,255,0.35); cursor:pointer; transition:background 0.2s; }
.btn-outline-light:hover { background:rgba(255,255,255,0.1); }

.value-props { background:#fff; padding:72px 20px; }
.vprops-grid { display:grid; grid-template-columns:1fr; gap:36px; margin-top:40px; max-width:1000px; margin-left:auto; margin-right:auto; }
.vprop { text-align:center; }
.vprop-icon { width:64px; height:64px; border-radius:16px; background:rgba(65,166,126,0.15); display:flex; align-items:center; justify-content:center; margin:0 auto 16px; color:#41A67E; }
.vprop h3 { font-family:'Inter',sans-serif; font-size:1.15rem; font-weight:700; margin-bottom:8px; }
.vprop p { color:#5a6a7a; font-size:0.95rem; max-width:300px; margin:0 auto; line-height:1.6; }

.home-locations { background:#F6F1E7; padding:72px 20px; }
.loc-province { margin-top:44px; }
.loc-province h3 { display:flex; align-items:center; gap:10px; font-size:1.5rem; margin-bottom:22px; }
.loc-pin { color:#4DA8DA; display:inline-flex; }
.loc-grid { display:grid; grid-template-columns:1fr; gap:14px; }
.loc-card { display:flex; align-items:center; justify-content:space-between; background:#fff; border:1px solid #ece6d8; border-radius:14px; padding:18px 20px; transition:border-color 0.2s, box-shadow 0.2s, transform 0.2s; }
.loc-card:hover { border-color:rgba(65,166,126,0.5); box-shadow:0 6px 20px rgba(14,42,71,0.06); transform:translateY(-1px); }
.loc-card .loc-city { display:block; font-weight:700; color:#0E2A47; }
.loc-card .loc-prov { display:block; font-size:0.8rem; color:#8a96a3; margin-top:2px; }
.loc-card .loc-arrow { color:#c2cad3; flex-shrink:0; transition:color 0.2s, transform 0.2s; }
.loc-card:hover .loc-arrow { color:#41A67E; transform:translateX(3px); }

/* City search */
.city-search { position:relative; max-width:440px; margin:28px auto 4px; }
.city-search svg { position:absolute; left:16px; top:50%; transform:translateY(-50%); color:#8a96a3; pointer-events:none; }
.city-search input { width:100%; padding:14px 18px 14px 46px; border:1.5px solid #d8dde3; border-radius:12px; font-size:1rem; font-family:'Inter',sans-serif; color:#0E2A47; background:#fff; outline:none; transition:border-color 0.2s, box-shadow 0.2s; }
.city-search input::placeholder { color:#9aa6b2; }
.city-search input:focus { border-color:#4DA8DA; box-shadow:0 0 0 3px rgba(77,168,218,0.15); }
.city-search-empty { text-align:center; color:#8a96a3; font-size:0.95rem; margin-top:28px; }

@media (min-width:640px) { .vprops-grid { grid-template-columns:repeat(3,1fr); } .loc-grid { grid-template-columns:1fr 1fr; } .home-cta-row { flex-direction:row; justify-content:center; } }
@media (min-width:1024px) { .loc-grid { grid-template-columns:1fr 1fr 1fr; } }
"""


PAGE_CSS = """
/* ── Inner page heroes & sections ─────────── */
.page-hero { background:#0E2A47; color:#fff; padding:60px 20px 66px; text-align:center; }
.page-hero h1 { font-size:clamp(1.9rem,4.5vw,3rem); color:#fff; margin:0 auto 14px; max-width:780px; }
.page-hero .sub { color:rgba(255,255,255,0.75); font-size:1.05rem; max-width:580px; margin:0 auto; line-height:1.6; }
.page-section { background:#fff; padding:64px 20px; }

/* About */
.about-photo { text-align:center; margin-bottom:44px; }
.about-photo img { width:240px; height:240px; border-radius:20px; object-fit:cover; margin:0 auto; box-shadow:0 14px 36px rgba(14,42,71,0.14); }
.about-photo h3 { font-size:1.4rem; margin-top:22px; }
.about-photo .loc { color:#5a6a7a; font-size:0.9rem; margin-top:2px; }
.about-socials { display:flex; gap:18px; justify-content:center; margin-top:16px; }
.about-socials a { color:#9aa6b2; transition:color 0.2s; }
.about-socials a:hover { color:#41A67E; }
.about-story { max-width:720px; margin:0 auto; }
.about-story p { color:#3a4f63; font-size:1.02rem; line-height:1.8; margin-bottom:20px; }
.about-story p.lead { font-size:1.25rem; font-weight:700; color:#0E2A47; }
.about-story p.accent { font-size:1.1rem; font-weight:600; color:#41A67E; }

/* Blog listing */
.blog-list { background:#F6F1E7; padding:56px 20px 72px; }
.blog-grid { display:grid; grid-template-columns:1fr; gap:28px; }
.blog-card { display:block; background:#fff; border:1px solid #ece6d8; border-radius:18px; overflow:hidden; transition:box-shadow 0.25s, border-color 0.25s, transform 0.2s; }
.blog-card:hover { box-shadow:0 10px 30px rgba(14,42,71,0.08); border-color:rgba(65,166,126,0.4); transform:translateY(-2px); }
.blog-card .thumb { height:200px; overflow:hidden; background:#0E2A47; }
.blog-card .thumb img { width:100%; height:100%; object-fit:cover; transition:transform 0.3s; }
.blog-card:hover .thumb img { transform:scale(1.05); }
.blog-card .body { padding:22px 22px 24px; }
.blog-card h2 { font-size:1.15rem; line-height:1.3; margin-bottom:8px; color:#0E2A47; }
.blog-card .excerpt { color:#5a6a7a; font-size:0.9rem; line-height:1.6; margin-bottom:16px; }
.blog-cats { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }
.blog-cat { background:rgba(65,166,126,0.15); color:#2c7a5b; font-size:0.72rem; font-weight:600; padding:3px 10px; border-radius:100px; }
.blog-meta { display:flex; gap:16px; flex-wrap:wrap; font-size:0.78rem; color:#8a96a3; border-top:1px solid #f0ece2; padding-top:14px; }
.blog-meta span { display:inline-flex; align-items:center; gap:5px; }

/* Blog post */
.post-hero { width:100%; height:300px; overflow:hidden; background:#0E2A47; }
.post-hero img { width:100%; height:100%; object-fit:cover; }
.post-wrap { max-width:760px; margin:0 auto; padding:40px 20px 64px; }
.post-back { display:inline-flex; align-items:center; gap:6px; font-size:0.85rem; color:#8a96a3; margin-bottom:24px; font-weight:600; }
.post-back:hover { color:#41A67E; }
.post-wrap h1 { font-size:clamp(1.8rem,4vw,2.6rem); color:#0E2A47; margin-bottom:18px; }
.post-byline { display:flex; gap:18px; flex-wrap:wrap; font-size:0.85rem; color:#8a96a3; border-top:1px solid #eee; border-bottom:1px solid #eee; padding:14px 0; margin-bottom:32px; }
.post-byline span { display:inline-flex; align-items:center; gap:6px; }
.post-content { color:#33414f; font-size:1.05rem; line-height:1.8; }
.post-content h2 { font-size:1.5rem; color:#0E2A47; margin:32px 0 12px; }
.post-content h3 { font-size:1.2rem; color:#0E2A47; margin:24px 0 10px; }
.post-content p { margin-bottom:18px; }
.post-content ul, .post-content ol { margin:0 0 18px 22px; }
.post-content li { margin-bottom:8px; }
.post-content a { color:#2c7a5b; text-decoration:underline; }
.post-content img { border-radius:12px; margin:20px 0; max-width:100%; }
.post-content strong { color:#0E2A47; }
@media (min-width:640px) { .blog-grid { grid-template-columns:1fr 1fr; } }
@media (min-width:768px) { .post-hero { height:380px; } }
@media (min-width:1024px) { .blog-grid { grid-template-columns:1fr 1fr 1fr; } }
"""

ICONS = {
    "pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>',
}


def header(cta_href="/locations/", cta_label="Find Your City", cta_icon="pin"):
    return f'''<header class="site-header">
  <div class="header-inner">
    <a href="/" class="logo">
      <span class="logo-mark"><img src="/assets/logo-icon.png" alt=""></span>
      Small Movers Canada
    </a>
    <nav>
      <ul class="nav-links">
        <li><a href="/">Home</a></li>
        <li><a href="/locations/">Locations</a></li>
        <li><a href="/blog/">Blog</a></li>
        <li><a href="/about/">About</a></li>
      </ul>
    </nav>
    <a href="{cta_href}" class="header-cta">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">{ICONS[cta_icon]}</svg>
      {cta_label}
    </a>
  </div>
</header>'''


def page_hero(badge, h1, sub=""):
    sub_html = f'\n  <p class="sub">{esc(sub)}</p>' if sub else ""
    return f'''<section class="page-hero">
  <span class="hero-badge">{esc(badge)}</span>
  <h1>{h1}</h1>{sub_html}
</section>'''


def locations_section(cities, intro):
    return f'''<section class="page-section">
  <div class="container">
    <p style="text-align:center; color:#5a6a7a; font-size:0.95rem; max-width:560px; margin:0 auto;">{esc(intro)}</p>
{city_search()}
{city_grid(cities)}
  </div>
</section>'''


def footer():
    nums = "\n".join(
        f'      <a href="tel:{tel(PROVINCE_PHONE[p])}">{PROVINCE_FULL[p]} — {PROVINCE_PHONE[p]}</a>'
        for p in PROVINCE_ORDER
    )
    prov_links = "\n".join(
        f'        <li><a href="/{PROVINCE_SLUG[p]}/">{PROVINCE_FULL[p]}</a></li>'
        for p in PROVINCE_ORDER
    )
    return f'''<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-brand">
      <div class="logo">
        <span class="logo-mark"><img src="/assets/logo-icon.png" alt=""></span>
        Small Movers Canada
      </div>
      <p>Affordable small and hourly moving services across Canada. Pay by the hour, not by the truck.</p>
    </div>
    <div class="footer-links">
      <h4>Quick Links</h4>
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/locations/">All Locations</a></li>
        <li><a href="/about/">About</a></li>
        <li><a href="/blog/">Blog</a></li>
{prov_links}
      </ul>
    </div>
    <div class="footer-contact">
      <h4>Call Us</h4>
{nums}
      <p>Serving cities across all of Canada</p>
    </div>
  </div>
  <div class="footer-bottom">
    <span>&copy; 2026 Jordan J. Caron Holdings LTD. All rights reserved.</span>
    <span>Serving cities across all of Canada</span>
  </div>
</footer>'''


def page_shell(title, description, canonical, body, header_html=None, robots="index, follow"):
    if header_html is None:
        header_html = header()
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/png" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/favicon.png">

<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM}');</script>
<!-- End Google Tag Manager -->

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>{shared_style()}{HOME_CSS}{PAGE_CSS}</style>
</head>
<body>
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
{header_html}
{body}
{footer()}
</body>
</html>'''


def render_home(cities):
    body = f'''
<section class="home-hero">
  <div class="inner">
    <span class="hero-badge">Serving Cities Across Canada</span>
    <h1>Small &amp; Hourly Movers for People Who Don't Need a Full Truck</h1>
    <p class="sub">Affordable moving help for small loads, furniture, and apartments. Pay by the hour, not by the truck size.</p>
    <div class="home-cta-row">
      <a href="#locations" class="btn-primary">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        Find Your City
      </a>
      <a href="/about/" class="btn-outline-light">How It Works</a>
    </div>
    <div class="hero-pills">
      <span><span class="pill-dot"></span> $85/hr per mover</span>
      <span><span class="pill-dot"></span> No hidden fees</span>
      <span><span class="pill-dot"></span> Same-day available</span>
    </div>
  </div>
</section>

<section class="value-props">
  <div class="container">
    <div style="text-align:center;"><span class="section-label">Why Small Movers Canada</span></div>
    <h2 class="section-heading" style="text-align:center;">The Small Jobs Big Movers Don't Want</h2>
    <p style="text-align:center; color:#5a6a7a; font-size:0.95rem; max-width:540px; margin:0 auto;">We specialize in small, affordable moves — and we do them better than the companies built for full-house jobs.</p>
    <div class="vprops-grid">
      <div class="vprop">
        <div class="vprop-icon"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div>
        <h3>Pay By the Hour</h3>
        <p>Only $85/hr per mover, with no full-truck minimums or hidden fees.</p>
      </div>
      <div class="vprop">
        <div class="vprop-icon"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
        <h3>Fast &amp; Flexible</h3>
        <p>Most small moves are done in 1–4 hours. Same-day, evenings, and weekends available.</p>
      </div>
      <div class="vprop">
        <div class="vprop-icon"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></div>
        <h3>Serving All of Canada</h3>
        <p>From Vancouver to Toronto, we connect you with local movers in cities across the country.</p>
      </div>
    </div>
  </div>
</section>

<section class="home-locations" id="locations">
  <div class="container">
    <div style="text-align:center;"><span class="section-label">Locations</span></div>
    <h2 class="section-heading" style="text-align:center;">Cities We Serve</h2>
    <p style="text-align:center; color:#5a6a7a; font-size:0.95rem; max-width:540px; margin:0 auto;">Find affordable small &amp; hourly moving services in your city.</p>
{city_search()}
{city_grid(cities)}
  </div>
</section>

<section class="final-cta">
  <div class="container">
    <h2>Ready to Book Your Small Move?</h2>
    <p>Find your city and get a free, no-obligation quote in under a minute.</p>
    <div class="cta-buttons">
      <a href="/locations/" class="btn-primary">View All Locations
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </a>
      <a href="/about/" class="btn-outline">About Us</a>
    </div>
  </div>
</section>
{CITY_SEARCH_JS}'''
    return page_shell(
        "Small & Hourly Movers Across Canada | Small Movers Canada",
        "Affordable small & hourly movers across Canada. Pay by the hour, not by the truck — "
        "small loads, furniture, and apartment moves. Find your city and get a free quote.",
        "https://smallmoverscanada.ca/",
        body,
    )


def cta_block(title, text, primary_href, primary_label, secondary_href, secondary_label):
    return f'''<section class="final-cta">
  <div class="container">
    <h2>{esc(title)}</h2>
    <p>{esc(text)}</p>
    <div class="cta-buttons">
      <a href="{primary_href}" class="btn-primary">{esc(primary_label)}
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </a>
      <a href="{secondary_href}" class="btn-outline">{esc(secondary_label)}</a>
    </div>
  </div>
</section>'''


def province_section(pcities, prov):
    cards = "\n".join(
        f'<a class="loc-card" href="/{c["slug"].strip()}/" data-city="{esc(c.get("city_name"))}">'
        f'<span><span class="loc-city">{esc(c.get("city_name"))}</span>'
        f'<span class="loc-prov">{esc(prov)}</span></span>{ARROW}</a>'
        for c in pcities
    )
    return f'''<section class="page-section">
  <div class="container">
    <div class="loc-grid">
{cards}
    </div>
  </div>
</section>'''


def render_locations(cities):
    body = (
        page_hero("Serving Cities Across Canada",
                  "Small &amp; Hourly Movers Near You",
                  "Find affordable moving services in your city. Select your location below.")
        + locations_section(cities, "Browse every city we serve, grouped by province.")
        + cta_block("Ready to Book Your Small Move?",
                    "Pick your city above to get a free quote, or learn more about how we work.",
                    "/", "Back to Home", "/about/", "About Us")
        + CITY_SEARCH_JS
    )
    return page_shell(
        "Small & Hourly Movers Near You | Small Movers Canada",
        "Find affordable small & hourly moving services in cities across Canada. "
        "Browse all Small Movers Canada locations by province.",
        "https://smallmoverscanada.ca/locations/",
        body,
    )


def render_province(cities, prov):
    full = PROVINCE_FULL[prov]
    phone = PROVINCE_PHONE[prov]
    pcities = sorted(
        [c for c in cities if (c.get("province") or "").strip() == prov],
        key=lambda c: c.get("city_name", ""),
    )
    body = (
        page_hero(full, f"Small &amp; Hourly Movers in {esc(full)}",
                  f"Find affordable moving services across {full}. Select your city below.")
        + province_section(pcities, prov)
        + cta_block("Ready to Book Your Move?",
                    f"Get a free, no-obligation quote from our {full} movers — or call us now.",
                    f"tel:{tel(phone)}", f"Call {phone}", "/locations/", "All Locations")
    )
    head = header(cta_href=f"tel:{tel(phone)}", cta_label=phone, cta_icon="phone")
    return page_shell(
        f"Moving Services in {full} | Small Movers Canada",
        f"Affordable small & hourly moving services across {full}. "
        f"Find local movers in your {prov} city with Small Movers Canada.",
        f"https://smallmoverscanada.ca/{PROVINCE_SLUG[prov]}/",
        body, header_html=head,
    )


SOCIAL_FB = '<path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>'
SOCIAL_IG = '<path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>'
SOCIAL_LI = '<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>'
SOCIAL_GLOBE = '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'


def render_about():
    body = f'''{page_hero("About Us", "Why Small Movers Canada Was Created")}
<section class="page-section">
  <div class="about-photo">
    <img src="/assets/jordan.jpg" alt="Jordan J. Caron — Founder of Small Movers Canada">
    <h3>Jordan J. Caron</h3>
    <p class="loc">Salt Spring Island, BC</p>
    <div class="about-socials">
      <a href="https://jordanjcaron.com/" target="_blank" rel="noopener noreferrer" title="Website"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{SOCIAL_GLOBE}</svg></a>
      <a href="https://facebook.com/JordanJCaron" target="_blank" rel="noopener noreferrer" title="Facebook"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">{SOCIAL_FB}</svg></a>
      <a href="https://instagram.com/JordanJCaron" target="_blank" rel="noopener noreferrer" title="Instagram"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">{SOCIAL_IG}</svg></a>
      <a href="https://www.linkedin.com/in/jordanjcaron" target="_blank" rel="noopener noreferrer" title="LinkedIn"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">{SOCIAL_LI}</svg></a>
    </div>
  </div>
  <div class="about-story">
    <p>I've been working in internet marketing since 2013, helping businesses grow online through websites, search, and digital strategy. In 2020 and 2021, like many people, my workload slowed down, and I found myself looking for additional work while the world adjusted to a new pace.</p>
    <p>Around that time, an old friend of mine, Brad, hired me to help him with small moving jobs in Victoria, BC. These were the kinds of moves most large moving companies didn't want — a couch, a few boxes, a marketplace pickup, or a short apartment move. What started as helping out quickly turned into something eye-opening.</p>
    <p>Over the next few months, I saw firsthand how big the demand was for small, affordable moving help. We helped countless people transport personal items that mattered to them — safely, quickly, and without the hassle of booking a full moving company for a small job. Brad was filling a massive gap in the moving market, often without even realizing it.</p>
    <p>What surprised me most was how he was getting his work done. Nearly all of it came from local classifieds like UsedVictoria. He didn't even have a website — yet he was consistently booked. Once I built him a simple website and helped him show up online, his business grew significantly.</p>
    <p class="lead">That experience sparked the idea for Small Movers Canada.</p>
    <p>Brad is happy focusing on serving Victoria, but I saw something bigger. People across Canada face the same problem every day: they need help with small moves, deliveries, and short-distance transport, and traditional movers either won't take the job or charge far more than it should cost.</p>
    <p>Small Movers Canada was created to make this much-needed service easier to find nationwide. Our goal is to connect people with reliable, local movers who are happy to handle smaller jobs — without minimums, unnecessary complexity, or confusing pricing.</p>
    <p class="accent">As we expand into 2026, our focus remains simple: make small moves easier, more accessible, and more affordable for people across Canada.</p>
  </div>
</section>
{cta_block("Ready to Book Your Move?",
           "Find affordable moving help in your city across Canada.",
           "/locations/", "View All Locations", "/", "Back to Home")}'''
    return page_shell(
        "About Us | Small Movers Canada",
        "Learn how Small Movers Canada was created to make small moves easier, "
        "more accessible, and more affordable across Canada.",
        "https://smallmoverscanada.ca/about/",
        body,
    )


I_USER = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
I_CAL = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>'
I_TAG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>'
I_BACK = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>'


def parse_list(s):
    s = (s or "").strip()
    if not s or s == "[]":
        return []
    try:
        v = ast.literal_eval(s)
        if isinstance(v, (list, tuple)):
            return [str(x).strip() for x in v if str(x).strip()]
    except (ValueError, SyntaxError):
        pass
    return [p.strip() for p in s.strip("[]").split(",") if p.strip()]


def fmt_date(s, long=False):
    s = (s or "").strip()[:10]
    if not s:
        return ""
    try:
        d = _dt.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return s
    return d.strftime(f"%{'B' if long else 'b'} %-d, %Y")


def blog_img(slug, url):
    url = (url or "").strip()
    if not url:
        return None
    ext = os.path.splitext(urlparse(url).path)[1] or ".webp"
    return f"/assets/blog/{slug}{ext}"


def load_blog():
    path = os.path.join(REPO, "build", "Blog_export.csv")
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8-sig")))
    pub = [r for r in rows if str(r.get("is_published", "")).strip().lower() == "true"]
    pub.sort(key=lambda r: (r.get("published_date") or ""), reverse=True)
    return pub


def render_blog_index(posts):
    cards = []
    for p in posts:
        slug = p["slug"].strip()
        img = blog_img(slug, p.get("image_url"))
        thumb = (f'<div class="thumb"><img src="{img}" alt="{esc(p.get("title"))}" loading="lazy"></div>'
                 if img else '<div class="thumb"></div>')
        cats = parse_list(p.get("categories"))
        cats_html = ('<div class="blog-cats">'
                     + "".join(f'<span class="blog-cat">{esc(c)}</span>' for c in cats[:2])
                     + "</div>") if cats else ""
        date = fmt_date(p.get("published_date"))
        date_html = f"<span>{I_CAL}{date}</span>" if date else ""
        cards.append(f'''<a class="blog-card" href="/blog/{slug}/">
  {thumb}
  <div class="body">
    {cats_html}
    <h2>{esc(p.get("title"))}</h2>
    <p class="excerpt">{esc(p.get("excerpt"))}</p>
    <div class="blog-meta"><span>{I_USER}{esc(p.get("author"))}</span>{date_html}</div>
  </div>
</a>''')
    body = (
        page_hero("Moving Resources", "Moving Tips &amp; Guides",
                  "Expert advice to help you plan a stress-free move across Canada.")
        + f'''<section class="blog-list">
  <div class="container">
    <div class="blog-grid">
{chr(10).join(cards)}
    </div>
  </div>
</section>'''
    )
    return page_shell(
        "Moving Blog & Tips | Small Movers Canada",
        "Helpful moving tips, packing guides, and local insights from Small Movers Canada.",
        "https://smallmoverscanada.ca/blog/",
        body,
    )


def render_blog_post(p):
    slug = p["slug"].strip()
    img = blog_img(slug, p.get("image_url"))
    hero = f'<div class="post-hero"><img src="{img}" alt="{esc(p.get("title"))}"></div>' if img else ""
    cats = parse_list(p.get("categories"))
    tags = parse_list(p.get("tags"))
    cats_html = ('<div class="blog-cats">'
                 + "".join(f'<span class="blog-cat">{esc(c)}</span>' for c in cats)
                 + "</div>") if cats else ""
    date = fmt_date(p.get("published_date"), long=True)
    date_html = f"<span>{I_CAL}{date}</span>" if date else ""
    tags_html = (f"<span>{I_TAG}" + ", ".join("#" + esc(t) for t in tags) + "</span>") if tags else ""
    content = p.get("content") or ""  # trusted HTML from the CMS
    body = f'''{hero}
<div class="post-wrap">
  <a class="post-back" href="/blog/">{I_BACK} Back to all posts</a>
  {cats_html}
  <h1>{esc(p.get("title"))}</h1>
  <div class="post-byline"><span>{I_USER}{esc(p.get("author"))}</span>{date_html}{tags_html}</div>
  <div class="post-content">
{content}
  </div>
</div>
{cta_block("Ready to Book Your Move?", "Get a fast, free quote from our hourly movers.", "/locations/", "Get a Free Quote", "/blog/", "More Articles")}'''
    return page_shell(
        f"{p.get('title')} | Small Movers Canada",
        p.get("excerpt") or "",
        f"https://smallmoverscanada.ca/blog/{slug}/",
        body,
    )


def render_thankyou():
    body = (
        page_hero("Request Received",
                  "Thanks — We've Got Your Request")
        + cta_block("In the meantime…",
                    "Browse the cities we serve or read our moving tips and guides.",
                    "/locations/", "View All Locations", "/blog/", "Moving Tips")
    )
    return page_shell(
        "Thank You | Small Movers Canada",
        "Your quote request has been received.",
        "https://smallmoverscanada.ca/thank-you/",
        body, robots="noindex, nofollow",
    )


BASE_URL = "https://smallmoverscanada.ca"


def build_sitemap(cities, posts):
    urls = [("/", "1.0", "weekly"),
            ("/locations/", "0.8", "weekly"),
            ("/about/", "0.6", "monthly"),
            ("/blog/", "0.7", "weekly")]
    for prov in PROVINCE_ORDER:
        urls.append((f"/{PROVINCE_SLUG[prov]}/", "0.8", "monthly"))
    for c in sorted(cities, key=lambda c: c.get("slug", "")):
        urls.append((f'/{c["slug"].strip()}/', "0.9", "monthly"))
    for p in posts:
        urls.append((f'/blog/{p["slug"].strip()}/', "0.6", "monthly"))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, pr, cf in urls:
        out.append(f"  <url>\n    <loc>{BASE_URL}{loc}</loc>\n"
                   f"    <changefreq>{cf}</changefreq>\n"
                   f"    <priority>{pr}</priority>\n  </url>")
    out.append("</urlset>\n")
    return "\n".join(out)


def main():
    cities = load_cities()
    posts = load_blog()
    out = {
        "index.html": render_home(cities),
        "locations/index.html": render_locations(cities),
        "about/index.html": render_about(),
        "blog/index.html": render_blog_index(posts),
        "thank-you/index.html": render_thankyou(),
    }
    for prov in PROVINCE_ORDER:
        out[f"{PROVINCE_SLUG[prov]}/index.html"] = render_province(cities, prov)
    for p in posts:
        out[f"blog/{p['slug'].strip()}/index.html"] = render_blog_post(p)

    for rel, html_out in out.items():
        path = os.path.join(REPO, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_out)
        leftover = set(re.findall(r"\[[A-Z\-]+\]", html_out))
        flag = f"  ⚠ tokens {leftover}" if leftover else ""
        print(f"wrote {rel}{flag}")

    with open(os.path.join(REPO, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap(cities, posts))
    print(f"wrote sitemap.xml ({len(cities) + len(posts) + 8} urls)")


if __name__ == "__main__":
    main()
