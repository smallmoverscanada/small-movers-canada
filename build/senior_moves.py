#!/usr/bin/env python3
"""Generate the Senior Moves landing page(s).

A reusable template for the senior-moves channel. Mirrors the city page shell
(header, footer, inline styles, phone, web form, schema) and swaps in
senior-specific, city-local content. All city specifics live in the CITIES
config, so copying to another partner city is a new config block, not a new
file. Run from the repo root: python3 build/senior_moves.py
"""
import html
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(REPO, "_template", "city.html")
GTM = "GTM-NV977B6T"
BASE = "https://smallmoverscanada.ca"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def tel_digits(display):
    return "+1" + re.sub(r"\D", "", display)


def shared_style():
    src = open(TEMPLATE, encoding="utf-8").read()
    return re.search(r"<style>(.*?)</style>", src, re.DOTALL).group(1)


SENIOR_CSS = """
/* ── Senior Moves page ───────────────────── */
.sr-section { padding:64px 20px; }
.sr-section.alt { background:#F6F1E7; }
.sr-lead { text-align:center; color:#5a6a7a; font-size:1.0rem; line-height:1.7; max-width:640px; margin:0 auto; }
.sr-grid3 { display:grid; grid-template-columns:1fr; gap:20px; max-width:960px; margin:36px auto 0; }
.sr-card { background:#fff; border:1px solid #ece6d8; border-radius:14px; padding:26px 28px; }
.sr-section.alt .sr-card { background:#fff; }
.sr-card h3 { font-size:1.1rem; color:#0E2A47; margin-bottom:10px; }
.sr-card p { color:#5a6a7a; font-size:0.95rem; line-height:1.6; }
.sr-check { max-width:720px; margin:34px auto 0; list-style:none; padding:0; display:grid; grid-template-columns:1fr; gap:14px; }
.sr-check li { display:flex; gap:12px; align-items:flex-start; color:#3a4f63; font-size:1.0rem; line-height:1.55; }
.sr-check li svg { flex-shrink:0; color:#41A67E; margin-top:3px; }
.sr-rate { max-width:680px; margin:34px auto 0; background:#0E2A47; color:#fff; border-radius:16px; padding:32px 30px; }
.sr-rate .rate-row { display:flex; justify-content:space-between; align-items:baseline; gap:16px; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.14); }
.sr-rate .rate-row:last-child { border-bottom:none; }
.sr-rate .rate-num { font-family:'Montserrat',sans-serif; font-weight:800; font-size:1.4rem; color:#7FD3AE; white-space:nowrap; }
.sr-rate .rate-lbl { color:rgba(255,255,255,0.85); font-size:0.97rem; }
.sr-rate .rate-note { color:rgba(255,255,255,0.7); font-size:0.88rem; margin-top:16px; line-height:1.55; }
.sr-steps { display:grid; grid-template-columns:1fr; gap:18px; max-width:860px; margin:34px auto 0; }
.sr-step { background:#fff; border:1px solid #ece6d8; border-radius:14px; padding:22px 24px; }
.sr-section.alt .sr-step { background:#fff; }
.sr-step .num { display:inline-flex; align-items:center; justify-content:center; width:32px; height:32px; border-radius:50%; background:#41A67E; color:#fff; font-weight:700; font-family:'Montserrat',sans-serif; margin-bottom:12px; }
.sr-step h3 { font-size:1.03rem; color:#0E2A47; margin-bottom:6px; }
.sr-step p { color:#5a6a7a; font-size:0.93rem; line-height:1.55; }
.res-list { max-width:820px; margin:34px auto 0; display:grid; grid-template-columns:1fr; gap:16px; }
.res-card { background:#fff; border:1px solid #ece6d8; border-radius:12px; padding:20px 22px; }
.sr-section.alt .res-card { background:#fff; }
.res-head { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:baseline; gap:8px; }
.res-card h3 { font-size:1.05rem; color:#0E2A47; }
.res-comm { font-size:0.8rem; font-weight:600; color:#2c7a5b; background:rgba(65,166,126,0.12); padding:3px 11px; border-radius:100px; white-space:nowrap; }
.res-card p { color:#5a6a7a; font-size:0.92rem; line-height:1.55; margin:8px 0 10px; }
.res-card a.res-link { font-size:0.85rem; font-weight:700; color:#2c7a5b; text-decoration:none; }
.res-card a.res-link:hover { text-decoration:underline; }
.res-note { text-align:center; color:#8a8172; font-size:0.9rem; max-width:620px; margin:22px auto 0; }
.sr-tips { max-width:720px; margin:30px auto 0; color:#3a4f63; font-size:1.0rem; line-height:1.75; padding-left:22px; }
.sr-tips li { margin-bottom:10px; }
.sr-faq { max-width:720px; margin:30px auto 0; }
.sr-faq .item { border-bottom:1px solid #e9e3d6; padding:18px 0; }
.sr-faq .item:last-child { border-bottom:none; }
.sr-faq h3 { font-size:1.05rem; color:#0E2A47; margin-bottom:6px; }
.sr-faq p { color:#5a6a7a; font-size:0.95rem; line-height:1.65; }
.sr-backlink { text-align:center; margin-top:30px; }
.sr-backlink a { color:#2c7a5b; font-weight:700; }
@media (min-width:720px) {
  .sr-grid3 { grid-template-columns:1fr 1fr 1fr; }
  .sr-steps { grid-template-columns:1fr 1fr; }
  .sr-check { grid-template-columns:1fr 1fr; }
}
"""

CHECK = ('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
         '<polyline points="20 6 9 17 4 12"/></svg>')
PHONE_SVG = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
             'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 '
             '19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 '
             '1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 '
             '1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>')

HAMILTON = {
    "city": "Hamilton", "prov": "Ontario", "prov_abbr": "ON", "slug": "hamilton",
    "phone": "289-780-3118", "path": "/hamilton/senior-moves/", "lead_type": "senior-hamilton",
    "hero_sub": ("Careful, patient help moving a parent into a retirement residence, or downsizing "
                 "from the family home. We handle the suite setup so day one feels like home."),
    "who_lead": ("Later-in-life moves come with a lot of feelings and a lot of logistics. Our crew "
                 "keeps it calm, careful, and on schedule so families can focus on the person, not "
                 "the heavy lifting."),
    "who_cards": [
        ("Moving a parent into a residence",
         "We handle the move into independent or assisted living and set the suite up so it feels like home from the first night."),
        ("Downsizing from a family home",
         "Going from a house to a suite means leaving a lot behind. We move what is coming and place it with care."),
        ("Moving between suites",
         "Changing suites or moving to a residence with more care? We make the short move simple and stress-free."),
    ],
    "rates_lead": ("You pay by the hour, not by the truck. A typical one-bedroom suite move is two "
                   "movers for two to four hours, usually well under a full-service price."),
    "rate_rows": [
        ("One mover", "$85/hr"),
        ("Two movers", "$140/hr"),
        ("Flat fee (fuel, travel, equipment & insurance)", "$50"),
        ("First 10 km included, then", "$1.50/km"),
    ],
    "rate_note": ("A 2.5-hour minimum applies to a two-mover crew, and it is waived for single-item "
                  "and in-suite moves. We give you an honest time estimate before the day so there "
                  "are no surprises."),
    "resource_heading": "Retirement Residences in Hamilton",
    "resource_intro": ("A helpful starting point if you are still comparing options. These are "
                       "independent and assisted living residences in Hamilton and nearby Stoney "
                       "Creek, Ancaster, Dundas, and Waterdown. We are not affiliated with any of them."),
    "residences": [
        ("Amica Dundas", "Dundas",
         "Independent living, assisted living, and memory care at 50 Hatt Street in Dundas.",
         "https://amica.ca/dundas"),
        ("Chartwell Georgian Retirement Residence", "Dundas",
         "Independent living with optional care support at 255 Governors Road in Dundas.",
         "https://chartwell.com/on/dundas/georgian"),
        ("V!VA Meadowlands", "Ancaster",
         "Independent and assisted living at 1248 Mohawk Road in Ancaster.",
         "https://vivalife.ca/viva-meadowlands/"),
        ("Parkland Ancaster", "Ancaster",
         "Independent living, assisted living, and memory care at 554 Golf Links Road in Ancaster.",
         "https://experienceparkland.com/en/locations/parkland-ancaster-ontario/"),
        ("Grandview Retirement Living", "Stoney Creek",
         "Independent and assisted living at 83 Centennial Parkway South in Stoney Creek.",
         "https://cornerstoneretirement.ca/location/grandview/"),
        ("Amica Stoney Creek", "Stoney Creek",
         "Independent living, assisted living, and memory care at 135 King Street East in Stoney Creek.",
         "https://amica.ca/stoneycreek"),
        ("Village Manor", "Waterdown",
         "Independent living, assisted living, and memory care at 57 John Street West in Waterdown.",
         "https://springliving.ca/property/village-manor/"),
        ("The Court at Rushdale", "Hamilton Mountain",
         "Independent living with on-site support available at 1360 Upper Sherman Avenue on Hamilton Mountain.",
         "https://www.atriaretirement.ca/retirement-communities/the-court-at-rushdale"),
        ("Chartwell Deerview Crossing", "Hamilton",
         "Independent living and memory care at 460 Rymal Road West in Hamilton.",
         "https://chartwell.com/on/hamilton/deerview-crossing"),
        ("Caroline Place", "Downtown Hamilton",
         "Independent and assisted living at 118 Market Street in downtown Hamilton.",
         "https://www.caroline-place.com"),
    ],
    "tips": [
        "Measure the suite and your key furniture first, so you know what will fit before moving day.",
        "Ask the residence for their move-in rules, elevator booking, and any insurance they require from movers.",
        "Label furniture and boxes with where they go in the new suite, so setup is quick.",
        "Keep a small bag of daily essentials and medications with you, not on the truck.",
        "Downsize before the move, not after, so you only move what fits the new space.",
        "Plan the first night: bed made, medications, glasses, and chargers easy to reach.",
    ],
    "faqs": [
        ("How long does a suite move take?",
         "Most moves into a retirement suite take two movers about two to four hours, depending on how much is coming and the access at both ends. We give you an honest time estimate before the day."),
        ("Do you set up the bed in the new suite?",
         "Yes. Our crew places your furniture where you want it and reassembles beds and basic furniture, so the suite is ready to settle into the same day."),
        ("Can you coordinate with the residence's move-in day?",
         "Yes. We work around the residence's assigned move-in window and their elevator or loading-dock booking, so the move lines up with their schedule."),
        ("Is there a minimum charge?",
         "Our Hamilton rate has a 2.5-hour minimum for a two-mover crew. That minimum is waived for single-item and in-suite moves, so a small move does not cost you a big minimum."),
        ("How far in advance should we book?",
         "A week or two of notice is ideal, especially near month-end. We can often help on shorter notice, so it is always worth a call."),
        ("Do you only move within Hamilton?",
         "We cover Hamilton and nearby communities including Stoney Creek, Ancaster, Dundas, and Waterdown, whether it is a move across town or from a family home into a residence."),
    ],
}

SURREY = {
    "city": "Surrey", "prov": "British Columbia", "prov_abbr": "BC", "slug": "surrey",
    "phone": "236-707-8241", "path": "/surrey/senior-moves/", "lead_type": "senior-surrey",
    "hero_sub": ("Careful, patient help moving a parent into a South Surrey or White Rock residence, "
                 "or downsizing from a longtime family home or townhouse. Our crew handles the suite "
                 "setup so day one feels like home."),
    "who_lead": ("A later-in-life move across the Peninsula comes with a lot of feelings and a lot of "
                 "logistics. Our crew keeps it calm and on schedule, so families can focus on the "
                 "person and not the heavy lifting."),
    "who_cards": [
        ("Moving a parent into a residence",
         "We handle the move into an independent or assisted living residence in Surrey or White Rock, and set the suite up so it feels like home the first night."),
        ("Downsizing from a house or townhouse",
         "Leaving a longtime family home in Surrey or Delta means leaving a lot behind. We move what is coming and place it with care."),
        ("Moving between suites",
         "Changing suites, or moving to a residence with more care on the Peninsula? We make the short move simple and stress-free."),
    ],
    "rates_lead": ("You pay by the hour, not by the truck. A typical one-bedroom suite move is two "
                   "movers for two to four hours, usually well under a full-service price."),
    "rate_rows": [
        ("One mover", "$105/hr"),
        ("Two movers plus truck", "$145/hr"),
    ],
    "rate_note": ("A 2-hour minimum applies for one mover, and a 2.5-hour minimum for two movers. "
                  "Your rate includes the truck, moving equipment, blankets, and basic disassembly "
                  "and reassembly, so there are no surprise add-ons. We give you an honest time "
                  "estimate before the day."),
    "resource_heading": "Retirement Residences in Surrey and White Rock",
    "resource_intro": ("A helpful starting point if you are still comparing options. These are "
                       "independent and assisted living residences across Surrey and White Rock, "
                       "from South Surrey and the Peninsula to Fleetwood, Newton, Cloverdale, and "
                       "City Centre. We are not affiliated with any of them."),
    "residences": [
        ("Amica White Rock", "White Rock",
         "Independent and assisted living at 15333 16th Avenue in White Rock.",
         "https://amica.ca/white-rock"),
        ("Oceana PARC", "White Rock",
         "Independent living in uptown White Rock at 1575 George Street.",
         "https://www.parcliving.ca"),
        ("Chartwell Crescent Gardens", "South Surrey",
         "Independent and assisted living near White Rock, just off Highway 99 in South Surrey.",
         "https://chartwell.com/bc/surrey/crescent-gardens"),
        ("Aspira Pacifica Retirement Residence", "South Surrey",
         "Independent and assisted living at 2525 King George Boulevard in South Surrey.",
         "https://www.aspiralife.ca/our-locations/british-columbia/surrey/aspira-pacifica-retirement-living/"),
        ("Aspira Peninsula Retirement Residence", "South Surrey",
         "Independent and assisted living at 2088 152nd Street in South Surrey.",
         "https://www.aspiralife.ca/our-locations/british-columbia/surrey/aspira-peninsula-retirement-living/"),
        ("Whitecliff", "South Surrey",
         "Independent and assisted living at 15501 16th Avenue in South Surrey.",
         "https://www.cogirseniorliving.ca/retirement-home-south-surrey-british-columbia/whitecliff"),
        ("Venvi Fleetwood Villa", "Fleetwood",
         "Independent and assisted living in the Fleetwood area of Surrey.",
         "https://www.cogirseniorliving.ca/retirement-home-surrey-british-columbia/venvi-fleetwood-villa"),
        ("Chartwell Imperial Place", "City Centre",
         "Independent and assisted living at 13853 102nd Avenue in Surrey City Centre.",
         "https://chartwell.com/bc/surrey/imperial-place"),
        ("Arbourside Court", "Newton",
         "Independent living with supportive services at 13751 74th Avenue in Newton.",
         "https://arbourside.com"),
        ("Bethshan Gardens", "Cloverdale",
         "Independent living, a non-profit residence at 17528 59th Avenue in Cloverdale.",
         "https://www.bethshangardens.org"),
    ],
    "tips": [
        "Measure the suite and your key furniture first. Peninsula residences often have smaller one-bedroom and studio suites than a Surrey house or townhouse.",
        "Ask the residence for their move-in rules, elevator or loading-bay booking, and any insurance they require from movers.",
        "Label furniture and boxes with where they go in the new suite, so setup is quick.",
        "Downsize before the move, not after, so you only move what fits the new space.",
        "Keep a small bag of daily essentials and medications with you, not on the truck.",
        "Plan around traffic. Moves from North Surrey or Delta into South Surrey and White Rock go smoother outside the morning and afternoon rush.",
    ],
    "faqs": [
        ("How long does a suite move take?",
         "Most moves into a retirement suite take two movers about two to four hours, depending on how much is coming and the access at both ends. We give you an honest time estimate before the day."),
        ("Do you set up the bed in the new suite?",
         "Yes. Our crew places your furniture where you want it and reassembles beds and basic furniture, so the suite is ready to settle into the same day."),
        ("Can you coordinate with the residence's move-in day?",
         "Yes. We work around the residence's assigned move-in window and their elevator or loading-bay booking, which many Surrey and White Rock buildings require."),
        ("Is there a minimum charge?",
         "Our Surrey rate has a 2-hour minimum for one mover and a 2.5-hour minimum for two movers, so a smaller suite move does not cost you a big minimum."),
        ("Which areas do you cover?",
         "We cover Surrey and White Rock, including South Surrey, Fleetwood, Guildford, Newton, Cloverdale, and City Centre, plus nearby Delta and Langley, whether the move is across town or from a family home into a residence."),
        ("How far in advance should we book?",
         "A week or two of notice is ideal, especially near month-end. We can often help on shorter notice, so it is always worth a call."),
    ],
}


def build_schema(cfg, canonical):
    faq_entities = [{
        "@type": "Question", "name": q,
        "acceptedAnswer": {"@type": "Answer", "text": a},
    } for q, a in cfg["faqs"]]
    graph = [
        {
            "@type": "MovingCompany", "name": "Small Movers Canada",
            "description": ("Senior moving help in %s, %s. Careful, patient crews for retirement "
                            "residence and suite moves." % (cfg["city"], cfg["prov"])),
            "url": canonical, "telephone": cfg["phone"], "priceRange": "$$",
            "areaServed": {"@type": "City", "name": cfg["city"],
                           "containedInPlace": {"@type": "AdministrativeArea", "name": cfg["prov"]}},
            "address": {"@type": "PostalAddress", "addressLocality": cfg["city"],
                        "addressRegion": cfg["prov_abbr"], "addressCountry": "CA"},
            "image": BASE + "/assets/logo-icon.png",
        },
        {
            "@type": "Service", "name": "Senior Moves in %s" % cfg["city"],
            "serviceType": "Senior and retirement residence moving",
            "provider": {"@type": "MovingCompany", "name": "Small Movers Canada", "telephone": cfg["phone"]},
            "areaServed": {"@type": "City", "name": cfg["city"]}, "url": canonical,
            "description": ("Moving seniors into retirement residences and between suites in %s and "
                            "nearby communities, with furniture placement and bed setup included." % cfg["city"]),
        },
        {"@type": "FAQPage", "mainEntity": faq_entities},
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": cfg["city"], "item": "%s/%s/" % (BASE, cfg["slug"])},
                {"@type": "ListItem", "position": 3, "name": "Senior Moves", "item": canonical},
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2)


def render(cfg):
    city = cfg["city"]
    phone = cfg["phone"]
    canonical = BASE + cfg["path"]
    title = "Senior Movers in %s | Retirement Residence Moves | Small Movers Canada" % city
    meta = ("Senior moves in %s. Careful, patient crews for retirement residence and suite moves, "
            "with furniture placement and bed setup. Call %s for a free quote." % (city, phone))

    who_cards = "\n".join(
        '      <div class="sr-card">\n        <h3>%s</h3>\n        <p>%s</p>\n      </div>' % (esc(t), esc(b))
        for t, b in cfg["who_cards"])
    rate_rows = "\n".join(
        '      <div class="rate-row"><span class="rate-lbl">%s</span><span class="rate-num">%s</span></div>'
        % (esc(l), esc(v)) for l, v in cfg["rate_rows"])
    rate_note = '      <p class="rate-note">%s</p>' % esc(cfg["rate_note"])
    tips = "\n".join('      <li>%s</li>' % esc(t) for t in cfg["tips"])
    res_cards = "\n".join(
        '      <div class="res-card">\n'
        '        <div class="res-head"><h3>%s</h3><span class="res-comm">%s</span></div>\n'
        '        <p>%s</p>\n'
        '        <a class="res-link" href="%s" target="_blank" rel="noopener">Visit official site &rarr;</a>\n'
        '      </div>' % (esc(n), esc(comm), esc(d), esc(u))
        for n, comm, d, u in cfg["residences"])
    faq_items = "\n".join(
        '      <div class="item"><h3>%s</h3><p>%s</p></div>' % (esc(q), esc(a))
        for q, a in cfg["faqs"])

    repl = {
        "{{TITLE}}": esc(title), "{{META}}": esc(meta), "{{CANONICAL}}": canonical, "{{GTM}}": GTM,
        "{{SHARED_STYLE}}": shared_style(), "{{SENIOR_CSS}}": SENIOR_CSS,
        "{{SCHEMA}}": build_schema(cfg, canonical),
        "{{CITY}}": esc(city), "{{CITY_SLUG}}": cfg["slug"], "{{LEAD_TYPE}}": esc(cfg["lead_type"]),
        "{{HERO_SUB}}": esc(cfg["hero_sub"]), "{{WHO_LEAD}}": esc(cfg["who_lead"]),
        "{{WHO_CARDS}}": who_cards, "{{RATES_LEAD}}": esc(cfg["rates_lead"]),
        "{{RATE_ROWS}}": rate_rows, "{{RATE_NOTE}}": rate_note,
        "{{RESOURCE_HEADING}}": esc(cfg["resource_heading"]), "{{RESOURCE_INTRO}}": esc(cfg["resource_intro"]),
        "{{RES_CARDS}}": res_cards, "{{TIPS}}": tips, "{{FAQ_ITEMS}}": faq_items,
        "{{RES_PLACEHOLDER}}": esc(cfg["residences"][0][0]),
        "{{PHONE_SVG}}": PHONE_SVG, "{{CHECK}}": CHECK,
    }
    page = PAGE_TEMPLATE
    for k, v in repl.items():
        page = page.replace(k, v)
    page = page.replace("[PHONE]", esc(phone))  # header/footer/CTA phone tokens
    return page


# Plain string (not an f-string) so CSS/JS braces and [PHONE] tokens pass through
# untouched; all substitution is done with .replace in render().
PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<meta name="description" content="{{META}}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{{CANONICAL}}">
<link rel="icon" type="image/png" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/favicon.png">

<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','{{GTM}}');</script>
<!-- End Google Tag Manager -->

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

<script type="application/ld+json">
{{SCHEMA}}
</script>

<style>{{SHARED_STYLE}}{{SENIOR_CSS}}</style>
</head>
<body>

<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={{GTM}}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->

<header class="site-header">
  <div class="header-inner">
    <a href="/" class="logo">
      <span class="logo-mark"><img src="/assets/logo-icon.png" alt=""></span>
      Small Movers Canada
    </a>
    <nav>
      <ul class="nav-links">
        <li><a href="/">Home</a></li>
        <li><a href="/locations">Locations</a></li>
        <li><a href="/blog">Blog</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </nav>
    <a href="tel:[PHONE]" class="header-cta">
      {{PHONE_SVG}}
      [PHONE]
    </a>
  </div>
</header>

<!-- ───────── HERO ───────── -->
<section class="hero">
  <div class="hero-inner">
    <div class="hero-text">
      <span class="hero-badge">Serving {{CITY}} &amp; nearby communities</span>
      <h1>Senior Moves&nbsp;in&nbsp;<span class="city-highlight">{{CITY}}</span></h1>
      <p class="hero-subtitle">{{HERO_SUB}}</p>
      <a href="tel:[PHONE]" class="hero-cta-btn">
        {{PHONE_SVG}}
        Call Now: [PHONE]
      </a>
      <div class="hero-pills">
        <span><span class="pill-dot"></span> Suite setup included</span>
        <span><span class="pill-dot"></span> We book the elevator</span>
        <span><span class="pill-dot"></span> Floors protected</span>
        <span><span class="pill-dot"></span> Free quote</span>
      </div>
    </div>

    <!-- Quote Form -->
    <div class="quote-form-card" id="quote">
      <h2>Get a Free Quote</h2>
      <p class="form-sub">No obligation. Takes about a minute.</p>
      <form action="/api/quote" method="POST">
        <div class="form-row">
          <div class="form-field">
            <label for="name">Full Name</label>
            <input type="text" id="name" name="name" placeholder="Your name" required>
          </div>
          <div class="form-field">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" placeholder="you@email.com" required>
          </div>
        </div>
        <div class="form-row">
          <div class="form-field">
            <label for="phone">Phone</label>
            <input type="tel" id="phone" name="phone" placeholder="(555) 123-4567">
          </div>
          <div class="form-field">
            <label for="date">Date of Move</label>
            <input type="text" id="date" name="date" placeholder="e.g. March 15">
          </div>
        </div>
        <div class="form-field" style="margin-bottom: 12px;">
          <label for="residence">Which residence are you moving into? (optional)</label>
          <input type="text" id="residence" name="residence" placeholder="e.g. {{RES_PLACEHOLDER}}">
        </div>
        <div class="form-field" style="margin-bottom: 12px;">
          <label for="city-field">City</label>
          <input type="text" id="city-field" name="city" value="{{CITY}}" readonly style="background:#eef0f3; cursor:default;">
        </div>
        <div class="form-field" style="margin-bottom: 16px;">
          <label for="details">What are you moving?</label>
          <textarea id="details" name="details" placeholder="e.g. one-bedroom suite, bed, dresser, boxes..." rows="2"></textarea>
        </div>
        <input type="hidden" name="lead_type" value="{{LEAD_TYPE}}">
        <input type="hidden" name="_subject" value="New Senior Move Request for {{CITY}}">
        <button type="submit" class="form-submit">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          Get My Free Quote
        </button>
      </form>
    </div>
  </div>
</section>

<!-- ───────── WHO IT'S FOR ───────── -->
<section class="sr-section">
  <div class="container">
    <div style="text-align:center;"><span class="section-label">Who It's For</span></div>
    <h2 class="section-heading" style="text-align:center;">Senior Moves, Made Gentle</h2>
    <p class="sr-lead">{{WHO_LEAD}}</p>
    <div class="sr-grid3">
{{WHO_CARDS}}
    </div>
  </div>
</section>

<!-- ───────── WHAT'S INCLUDED ───────── -->
<section class="sr-section alt">
  <div class="container">
    <div style="text-align:center;"><span class="section-label">What's Included</span></div>
    <h2 class="section-heading" style="text-align:center;">Everything the Day Needs</h2>
    <ul class="sr-check">
      <li>{{CHECK}}<span>A careful, patient crew used to working with seniors and families</span></li>
      <li>{{CHECK}}<span>Furniture placement and bed setup in the new suite</span></li>
      <li>{{CHECK}}<span>Coordinating with the residence's move-in day, elevator, and loading dock</span></li>
      <li>{{CHECK}}<span>Protecting floors, doorways, and hallways at both ends</span></li>
      <li>{{CHECK}}<span>Blankets and equipment to keep furniture safe in transit</span></li>
      <li>{{CHECK}}<span>Clear, honest pricing with the fees spelled out up front</span></li>
    </ul>
  </div>
</section>

<!-- ───────── RATES ───────── -->
<section class="sr-section">
  <div class="container">
    <div style="text-align:center;"><span class="section-label">Simple Rates</span></div>
    <h2 class="section-heading" style="text-align:center;">What a Suite Move Costs</h2>
    <p class="sr-lead">{{RATES_LEAD}}</p>
    <div class="sr-rate">
{{RATE_ROWS}}
{{RATE_NOTE}}
    </div>
  </div>
</section>

<!-- ───────── HOW IT WORKS ───────── -->
<section class="sr-section alt">
  <div class="container">
    <div style="text-align:center;"><span class="section-label">How It Works</span></div>
    <h2 class="section-heading" style="text-align:center;">Four Simple Steps</h2>
    <div class="sr-steps">
      <div class="sr-step"><span class="num">1</span><h3>Call or request a quote</h3><p>Tell us the pickup, the residence, the suite, and roughly what is moving. We give you a clear estimate.</p></div>
      <div class="sr-step"><span class="num">2</span><h3>Confirm the date</h3><p>We line up with the residence's move-in day and book the elevator or loading-dock window.</p></div>
      <div class="sr-step"><span class="num">3</span><h3>Move day</h3><p>Our crew loads, transports, and protects everything along the way, keeping to the schedule.</p></div>
      <div class="sr-step"><span class="num">4</span><h3>Suite setup</h3><p>We place the furniture, set up the bed, and make sure the suite is ready to settle into.</p></div>
    </div>
  </div>
</section>

<!-- ───────── RESIDENCE RESOURCE LIST ───────── -->
<section class="sr-section">
  <div class="container">
    <div style="text-align:center;"><span class="section-label">Local Resource</span></div>
    <h2 class="section-heading" style="text-align:center;">{{RESOURCE_HEADING}}</h2>
    <p class="sr-lead">{{RESOURCE_INTRO}}</p>
    <div class="res-list">
{{RES_CARDS}}
    </div>
    <p class="res-note">Please contact each residence directly for tours, pricing, and current suite availability.</p>
  </div>
</section>

<!-- ───────── TIPS ───────── -->
<section class="sr-section alt">
  <div class="container">
    <div style="text-align:center;"><span class="section-label">Helpful Tips</span></div>
    <h2 class="section-heading" style="text-align:center;">Moving a Parent Into a Residence</h2>
    <ul class="sr-tips">
{{TIPS}}
    </ul>
  </div>
</section>

<!-- ───────── FAQ ───────── -->
<section class="sr-section">
  <div class="container">
    <div style="text-align:center;"><span class="section-label">Questions</span></div>
    <h2 class="section-heading" style="text-align:center;">Senior Move FAQ</h2>
    <div class="sr-faq">
{{FAQ_ITEMS}}
    </div>
    <div class="sr-backlink"><a href="/{{CITY_SLUG}}/">See our full {{CITY}} small &amp; hourly movers page &rarr;</a></div>
  </div>
</section>

<!-- ───────── FINAL CTA ───────── -->
<section class="final-cta">
  <div class="container">
    <h2>Ready to Plan a Senior Move in&nbsp;{{CITY}}?</h2>
    <p>Get a free, no-obligation quote. Or call us now and we will walk you through it.</p>
    <div class="cta-buttons">
      <a href="#quote" class="btn-primary">Get a Free Quote
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </a>
      <a href="tel:[PHONE]" class="btn-outline">Call [PHONE]</a>
    </div>
  </div>
</section>

<footer class="site-footer">
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
        <li><a href="/locations">All Locations</a></li>
        <li><a href="/about">About</a></li>
        <li><a href="/{{CITY_SLUG}}/">{{CITY}} Movers</a></li>
        <li><a href="/blog">Blog</a></li>
      </ul>
    </div>
    <div class="footer-contact">
      <h4>Contact Us</h4>
      <a href="tel:[PHONE]">
        {{PHONE_SVG}}
        [PHONE]
      </a>
      <p>Serving cities across all of Canada</p>
    </div>
  </div>
  <div class="footer-bottom">
    <span>&copy; 2026 Jordan J. Caron Holdings LTD. All rights reserved.</span>
    <span>Serving cities across all of Canada</span>
  </div>
</footer>

<script>
(function () {
  var form = document.querySelector('.quote-form-card form');
  if (!form) return;
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var btn = form.querySelector('.form-submit');
    var original = btn ? btn.innerHTML : '';
    if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }
    fetch('/api/quote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.fromEntries(new FormData(form)))
    }).then(function (r) {
      if (!r.ok) throw new Error('bad status');
      window.location.href = '/thank-you/';
    }).catch(function () {
      if (btn) { btn.disabled = false; btn.innerHTML = original; }
      alert('Sorry, something went wrong sending your request. Please call us instead.');
    });
  });
})();
</script>

</body>
</html>
"""

CITIES = [HAMILTON, SURREY]


def main():
    for cfg in CITIES:
        out = render(cfg)
        leftover = set(re.findall(r"\{\{[A-Z_]+\}\}", out))
        if leftover:
            print("  WARNING unreplaced tokens:", leftover)
        rel = cfg["path"].strip("/") + "/index.html"
        path = os.path.join(REPO, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print("wrote", rel)


if __name__ == "__main__":
    main()
