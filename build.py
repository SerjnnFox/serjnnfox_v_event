#!/usr/bin/env python3
"""Builds the static site into _site/.

    python3 build.py            # build
    python3 build.py --serve    # build and serve on http://localhost:8000

Content lives in this file (texts) and in data/*.json (cases, photos).
No dependencies beyond the Python standard library.
"""
import html
import json
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "_site"
DOMAIN = "https://v-event.ru"

# Site served from a sub-folder (e.g. user.github.io/repo/) until the domain is connected.
BASE = os.environ.get("BASE_PATH", "").rstrip("/")


def with_base(doc):
    if not BASE:
        return doc
    doc = doc.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">', 1)  # preview copy
    doc = re.sub(r'((?:href|src|action)=")/(?!/)', r"\g<1>" + BASE + "/", doc)
    doc = re.sub(r'srcset="[^"]*"', lambda m: m.group(0).replace("/assets/", BASE + "/assets/"), doc)
    return doc


CASES = json.loads((ROOT / "data/cases.json").read_text())
CASE_BY_SLUG = {c["slug"]: c for c in CASES}
IMAGES_FILE = ROOT / "data/images.json"
IMAGES = json.loads(IMAGES_FILE.read_text()) if IMAGES_FILE.exists() else {"cases": {}, "site": {}, "instagram": []}

# Form handling: put a Formspree / Getform / Web3Forms URL here to receive
# leads by e-mail. Left empty, the form opens WhatsApp with the filled text.
FORM_ENDPOINT = ""
YANDEX_METRIKA = ""  # counter id, e.g. "12345678"

C = {
    "brand": "Vinogradova Event",
    "phone": "+7 (965) 321-56-60",
    "tel": "+79653215660",
    "wa": "79653215660",
    "email": "vinogradova.event@yandex.ru",
    "address": "Москва, 1-я Тверская-Ямская, 25с1",
    "map": "https://yandex.ru/maps/?text=%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%2C%201-%D1%8F%20%D0%A2%D0%B2%D0%B5%D1%80%D1%81%D0%BA%D0%B0%D1%8F-%D0%AF%D0%BC%D1%81%D0%BA%D0%B0%D1%8F%2025%D1%811",
    "hours": "Пн–пт 9:00–21:00, в выходные — звоните в любое удобное время",
    "dubai_phone": "+971 58 584 7627",
    "dubai_tel": "+971585847627",
    "dubai_wa": "971585847627",
    "dubai_email": "dubaiweddingandproposal@gmail.com",
    "dubai_address": "Dubai Marina, 66 Al Marsa St",
    "dubai_map": "https://maps.google.com/?q=66+Al+Marsa+St,+Dubai+Marina",
    "instagram": "https://instagram.com/vinogradova_event",
    "vk": "https://vk.com/vinogradova.event",
    "youtube": "sySyEJiA2Pg",
    "award": "Победители White Wedding Industry Awards 2024 в номинации «Лучшая свадьба в Дубае»",
}

CURRENT = ' aria-current="page"'
NAV = [
    ("/#about", "О нас", "about"),
    ("/portfolio/", "Портфолио", "portfolio"),
    ("/#price", "Услуги и цены", "price"),
    ("/dubai/", "Дубай", "dubai"),
    ("/education/", "Обучение", "education"),
    ("/reviews/", "Отзывы", "reviews"),
    ("/contacts/", "Контакты", "contacts"),
]

REGION_LABEL = {"moscow": "Россия", "dubai": "ОАЭ", "europe": "Европа"}

e = html.escape


# ---------------------------------------------------------------- icons
def icon(name, size=20):
    p = {
        "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
        "wa": '<path d="M3 21l1.65-3.8A9 9 0 1 1 8.4 20.3L3 21"/><path d="M9 10a.5.5 0 0 0 1 0V9a.5.5 0 0 0-1 0v1a5 5 0 0 0 5 5h1a.5.5 0 0 0 0-1h-1a.5.5 0 0 0 0 1"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
        "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
        "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "ig": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".6" fill="currentColor"/>',
        "vk": '<path d="M3 7h3.2c.4 3 1.9 5 3.3 5.4V7h3v3.2c1.4-.2 2.7-1.7 3.2-3.2h3c-.4 2-2 3.8-3.2 4.5 1.2.6 3 2 3.5 4.5h-3.3c-.5-1.6-1.8-2.8-3.2-3v3H12C7 16 3.6 12.5 3 7z"/>',
        "award": '<circle cx="12" cy="9" r="6"/><path d="M8.5 13.8L7 22l5-3 5 3-1.5-8.2"/>',
        "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
        "play": '<path d="M8 5v14l11-7z" fill="currentColor"/>',
    }[name]
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>')


# ---------------------------------------------------------------- images
def site_img(role, alt, cls="", sizes="100vw", eager=False):
    info = IMAGES["site"].get(role)
    if not info:
        return f'<div class="ph {cls}" role="img" aria-label="{e(alt)}">Vinogradova Event</div>'
    small = ROOT / "assets/img/site" / f"{role}-sm.webp"
    srcset = f' srcset="/assets/img/site/{role}-sm.webp 800w, /assets/img/site/{role}.webp {info["w"]}w" sizes="{sizes}"' if small.exists() else ""
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<img src="/assets/img/site/{role}.webp"{srcset} width="{info["w"]}" height="{info["h"]}" '
            f'alt="{e(alt)}" class="{cls}" {load}>')


def case_cover(case, sizes="(max-width: 560px) 100vw, (max-width: 900px) 50vw, 33vw", eager=False, full=False):
    info = IMAGES["cases"].get(case["slug"], {}).get("cover")
    if not info:
        return f'<div class="ph" role="img" aria-label="{e(case["title"])}">{e(case["venue"])}</div>'
    base = f'/assets/img/cases/{case["slug"]}'
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    src = f"{base}/cover.webp" if full else f"{base}/cover-sm.webp"
    return (f'<img src="{src}" srcset="{base}/cover-sm.webp 800w, {base}/cover.webp {info["w"]}w" sizes="{sizes}" '
            f'width="{info["w"]}" height="{info["h"]}" alt="{e(case["title"])}, {e(case["venue"])}" {load}>')


# ---------------------------------------------------------------- layout
def head(title, desc, path, og_image=None):
    url = DOMAIN + path
    og = og_image or "/assets/img/site/hero.webp"
    metrika = ""
    if YANDEX_METRIKA:
        metrika = (f'<script>(function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};'
                   f'm[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}})'
                   f'(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");ym({YANDEX_METRIKA},"init",{{webvisor:true}});</script>')
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="Vinogradova Event">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}{og}">
<meta name="theme-color" content="#fffdf9">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600&family=Playfair+Display:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/style.css?v={VERSION}">
<script>window.SITE={{whatsapp:"{C['wa']}",formEndpoint:"{FORM_ENDPOINT}",metrika:"{YANDEX_METRIKA}"}};</script>
{metrika}
</head>"""


def header(active):
    links = "".join(
        f'<a href="{href}"{CURRENT if key == active else ""}>{label}</a>' for href, label, key in NAV
    )
    mlinks = "".join(f'<a href="{href}">{label}</a>' for href, label, _ in NAV)
    return f"""<body>
<a class="skip" href="#main">Перейти к содержанию</a>
<header class="header">
  <div class="wrap header__in">
    <a class="logo" href="/" aria-label="Vinogradova Event — на главную"><b>Vinogradova</b><span>Wedding &amp; Event</span></a>
    <nav class="nav" aria-label="Основное меню">{links}</nav>
    <div class="header__contact">
      <a class="header__phone" href="tel:{C['tel']}">{C['phone']}</a>
      <a class="btn btn--gold" href="#lead">Обсудить свадьбу</a>
    </div>
    <button class="burger" aria-label="Меню" aria-expanded="false" aria-controls="mobile-menu"><span></span></button>
  </div>
</header>
<nav class="mobile-menu" id="mobile-menu" aria-label="Мобильное меню">
  {mlinks}
  <a class="btn btn--gold" href="#lead">Обсудить свадьбу</a>
  <a class="btn btn--ghost" href="tel:{C['tel']}">{icon('phone', 18)} {C['phone']}</a>
  <small>{C['hours']}</small>
</nav>
<main id="main">"""


def footer(wa=None):
    wa = wa or C["wa"]
    return f"""</main>
<footer class="footer">
  <div class="wrap">
    <div class="footer__grid">
      <div>
        <a class="logo" href="/"><b>Vinogradova</b><span>Wedding &amp; Event</span></a>
        <p style="margin-top:20px;max-width:320px">Свадебное агентство полного цикла. Организуем свадьбы в&nbsp;Москве, Дубае и&nbsp;Европе с&nbsp;2015&nbsp;года.</p>
        <div class="socials">
          <a href="{C['instagram']}" target="_blank" rel="noopener" aria-label="Instagram">{icon('ig')}</a>
          <a href="{C['vk']}" target="_blank" rel="noopener" aria-label="ВКонтакте">{icon('vk')}</a>
          <a href="https://wa.me/{wa}" target="_blank" rel="noopener" aria-label="WhatsApp">{icon('wa')}</a>
        </div>
      </div>
      <div>
        <h4>Разделы</h4>
        <ul>{"".join(f'<li><a href="{h}">{l}</a></li>' for h, l, _ in NAV)}</ul>
      </div>
      <div>
        <h4>Москва</h4>
        <ul>
          <li><a href="tel:{C['tel']}">{C['phone']}</a></li>
          <li><a href="mailto:{C['email']}">{C['email']}</a></li>
          <li><a href="{C['map']}" target="_blank" rel="noopener">{C['address']}</a></li>
          <li>Пн–пт 9:00–21:00</li>
        </ul>
      </div>
      <div>
        <h4>Дубай</h4>
        <ul>
          <li><a href="tel:{C['dubai_tel']}">{C['dubai_phone']}</a></li>
          <li><a href="mailto:{C['dubai_email']}">{C['dubai_email']}</a></li>
          <li><a href="{C['dubai_map']}" target="_blank" rel="noopener">{C['dubai_address']}</a></li>
        </ul>
      </div>
    </div>
    <div class="footer__bottom">
      <span>© 2015–2026 Vinogradova Event</span>
      <a href="/policy/">Политика конфиденциальности</a>
    </div>
  </div>
</footer>
<a class="fab" href="https://wa.me/{wa}" target="_blank" rel="noopener">{icon('wa', 22)} WhatsApp</a>
<script src="/assets/js/main.js?v={VERSION}" defer></script>
</body>
</html>"""


def ld_script(*objs):
    return "".join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in objs)


ORG_ID = DOMAIN + "/#org"
SECTION_NAMES = {"/portfolio/": "Портфолио", "/dubai/": "Свадьба в Дубае", "/education/": "Обучение",
                 "/reviews/": "Отзывы", "/contacts/": "Контакты", "/policy/": "Политика конфиденциальности",
                 "/en/dubai/": "Wedding in Dubai"}


def breadcrumbs_ld(path):
    if path in ("/", "/404.html"):
        return ""
    trail = [("Главная", "/")]
    if path in SECTION_NAMES:
        trail.append((SECTION_NAMES[path], path))
    elif path.strip("/") in CASE_BY_SLUG:
        trail += [("Портфолио", "/portfolio/"), (CASE_BY_SLUG[path.strip("/")]["title"], path)]
    else:
        return ""
    return ld_script({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": DOMAIN + u} for i, (n, u) in enumerate(trail, 1)]})


def page(path, title, desc, active, body, og_image=None, wa=None, extra_head=""):
    extra_head = breadcrumbs_ld(path) + extra_head
    doc = head(title, desc, path, og_image).replace("</head>", extra_head + "\n</head>") + header(active) + body + footer(wa)
    doc = re.sub(r'(<a href="mailto:[^"]+">)([^<@]+)@([^<]+)</a>', r"\1\2<wbr>@\3</a>", doc)  # wrap e-mails before "@"
    doc = with_base(doc)
    dest = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
    if path.endswith(".html"):
        dest = OUT / path.strip("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc)
    SITEMAP.append(path)


# ---------------------------------------------------------------- blocks
def lead_form(title="Расскажите о вашей свадьбе", note="Перезвоним в течение рабочего дня, ответим на вопросы и предложим время встречи.",
              lead_name="Заявка на организацию свадьбы", venue=None, city_default="Москва", wa=None, button="Жду звонка"):
    wa = wa or C["wa"]
    hidden = f'<input type="hidden" name="venue" data-label="Интересует площадка" value="{e(venue)}">' if venue else ""
    cities = "".join(
        f'<label><input type="radio" name="city" data-label="Где свадьба" value="{c}"{" checked" if c == city_default else ""}><span>{c}</span></label>'
        for c in ("Москва", "Дубай / ОАЭ", "Другая страна")
    )
    return f"""<form class="form" data-lead="{e(lead_name)}" data-wa="{wa}" novalidate>
  <h3>{title}</h3>
  <p>{note}</p>
  {hidden}
  <div class="field"><label for="f-name-{id(title)}">Как к вам обращаться</label>
    <input id="f-name-{id(title)}" name="name" data-label="Имя" autocomplete="name" placeholder="Имя"></div>
  <div class="field"><label for="f-phone-{id(title)}">Телефон или WhatsApp *</label>
    <input id="f-phone-{id(title)}" name="phone" data-label="Телефон" type="tel" autocomplete="tel" inputmode="tel" placeholder="+7 900 000-00-00" required>
    <span class="err">Пожалуйста, укажите номер телефона полностью</span></div>
  <div class="field--row">
    <div class="field"><label for="f-date-{id(title)}">Дата свадьбы</label>
      <input id="f-date-{id(title)}" name="date" data-label="Дата" placeholder="Например, август 2027"></div>
    <div class="field"><label for="f-guests-{id(title)}">Гостей</label>
      <input id="f-guests-{id(title)}" name="guests" data-label="Гостей" inputmode="numeric" placeholder="Около 60"></div>
  </div>
  <div class="field"><span style="font-size:13px;font-weight:600;color:var(--ink-2)">Где планируете</span>
    <div class="seg" role="radiogroup" aria-label="Где планируете свадьбу">{cities}</div></div>
  <input type="text" name="_gotcha" tabindex="-1" autocomplete="off" style="display:none">
  <button class="btn btn--gold btn--block" type="submit">{button}</button>
  <p class="form__legal">Нажимая кнопку, вы соглашаетесь с <a href="/policy/">политикой конфиденциальности</a>.</p>
</form>"""


def lead_section(title="Давайте обсудим вашу свадьбу", text=None, wa=None, phone=None, tel=None, email=None, address=None, map_url=None, form_kw=None, eyebrow="Первый шаг"):
    wa = wa or C["wa"]
    text = text or "Оставьте заявку — Полина или её ассистент перезвонят, ответят на вопросы и договорятся о личной встрече. Консультация ни к чему не обязывает."
    phone, tel = phone or C["phone"], tel or C["tel"]
    email, address, map_url = email or C["email"], address or C["address"], map_url or C["map"]
    return f"""<section class="section section--dark" id="lead">
  <div class="wrap lead-block">
    <div>
      <span class="eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      <p class="lead" style="color:rgba(243,235,225,.8);margin-top:20px">{text}</p>
      <ul class="contact-lines">
        <li>{icon('phone')}<div><a href="tel:{tel}">{phone}</a><small>{C['hours']}</small></div></li>
        <li>{icon('wa')}<div><a href="https://wa.me/{wa}" target="_blank" rel="noopener">Написать в WhatsApp</a><small>Если удобнее переписываться</small></div></li>
        <li>{icon('mail')}<div><a href="mailto:{email}">{email}</a></div></li>
        <li>{icon('pin')}<div><a href="{map_url}" target="_blank" rel="noopener">{address}</a></div></li>
      </ul>
    </div>
    {lead_form(wa=wa, **(form_kw or {}))}
  </div>
</section>"""


CARD_PHOTOS = 6  # cover + first gallery photos shown in each card's swipe slider


def case_cards(cases, with_region=True):
    out = []
    for c in cases:
        tag = f'<span class="case-card__tag">{REGION_LABEL[c["region"]]}</span>' if with_region else ""
        guests = f'{c["guests"]} {plural(c["guests"], "гость", "гостя", "гостей")}'
        href = f"/{c['slug']}/"
        gallery = IMAGES["cases"].get(c["slug"], {}).get("gallery", [])[: CARD_PHOTOS - 1]
        slides = [f'<a class="slide" href="{href}" tabindex="-1">{case_cover(c)}</a>']
        base = f'/assets/img/cases/{c["slug"]}'
        for k, p in enumerate(gallery, 2):
            h = round(p["h"] * min(p["w"], 800) / p["w"])
            slides.append(f'<a class="slide" href="{href}" tabindex="-1"><img src="{base}/{p["n"]}-sm.webp" width="{min(p["w"], 800)}" height="{h}" '
                          f'alt="{e(c["title"])} — фото {k}" loading="lazy" decoding="async"></a>')
        n = len(slides)
        controls = ""
        if n > 1:
            dots = "".join(f'<span{" class=\"on\"" if i == 0 else ""}></span>' for i in range(n))
            controls = (f'<button class="slider__btn slider__btn--prev" type="button" aria-label="Предыдущее фото">‹</button>'
                        f'<button class="slider__btn slider__btn--next" type="button" aria-label="Следующее фото">›</button>'
                        f'<div class="slider__dots" aria-hidden="true">{dots}</div>')
        out.append(f"""<article class="case-card reveal" data-region="{c['region']}">
  <div class="case-card__img slider">
    <div class="slider__track" data-slider>{''.join(slides)}</div>
    {tag}{controls}
  </div>
  <h3><a href="{href}">{e(c['title'])}</a></h3>
  <p>{e(c['city'])} · {guests} · {c['date'][-4:]}</p>
</article>""")
    return "\n".join(out)


def plural(n, one, few, many):
    n = abs(n) % 100
    if 11 <= n <= 19:
        return many
    n %= 10
    return one if n == 1 else few if 2 <= n <= 4 else many


def stats_block():
    return """<div class="stats reveal">
  <div class="stat"><b>520+</b><span>свадеб и событий организовано</span></div>
  <div class="stat"><b>11 лет</b><span>в свадебной индустрии — с&nbsp;2015 года</span></div>
  <div class="stat"><b>10–6000</b><span>гостей: от камерных ужинов до масштабных праздников</span></div>
  <div class="stat"><b>2 офиса</b><span>в&nbsp;Москве и&nbsp;Дубае, свадьбы по всему миру</span></div>
</div>"""


def pricing_block(region="moscow"):
    if region == "moscow":
        tiers = [("до 1,5 млн ₽", "95 000 ₽", ""), ("1,5–2,5 млн ₽", "130 000 ₽", "Чаще всего выбирают"),
                 ("2,5–3,5 млн ₽", "180 000 ₽", ""), ("от 3,5 млн ₽", "7%", "от бюджета свадьбы")]
        team = "3 организатора на подготовке и от 2 координаторов в день свадьбы"
        coord = ("15 000 ₽", "Готовите свадьбу сами?")
    else:
        tiers = [("до 150 000 AED", "8 500 AED", ""), ("150 000–250 000 AED", "12 500 AED", "Чаще всего выбирают"),
                 ("250 000–400 000 AED", "18 000 AED", ""), ("от 400 000 AED", "8%", "от бюджета свадьбы")]
        team = "2 организатора на подготовке и от 2 координаторов в день свадьбы"
        coord = ("1 500 AED", "Готовите свадьбу сами?")
    cards = []
    for budget, fee, note in tiers:
        hl = ' price--hl" data-label="Популярно' if note == "Чаще всего выбирают" else ""
        note_html = f'<p class="price__note">{note if note != "Чаще всего выбирают" else "гонорар агентства"}</p>' if note else '<p class="price__note">гонорар агентства</p>'
        cards.append(f"""<div class="price{hl}">
  <div class="price__budget">Бюджет свадьбы<b>{budget}</b></div>
  <div class="price__fee">{fee}</div>
  {note_html}
</div>""")
    return f"""<div class="pricing reveal">{''.join(cards)}</div>
<div class="price-extra reveal">
  <div class="price-box">
    <h3>Что входит в полную организацию</h3>
    <ul class="checks">
      <li>Подбор площадки и бронирование</li>
      <li>Команда: фотограф, видеограф, ведущий, DJ и артисты</li>
      <li>Декор, флористика и техническое оборудование</li>
      <li>Образ: визажист и стилист, а ещё торт и все детали</li>
      <li>Смета, тайминг и сценарий дня</li>
      <li>{team}</li>
    </ul>
  </div>
  <div class="price-box price-box--alt">
    <h3>{coord[1]}</h3>
    <p>Возьмите координатора на весь свадебный день. Он проконтролирует подрядчиков и тайминг, решит любые накладки — а вы просто будете отдыхать.</p>
    <div class="price__fee">{coord[0]}</div>
    <p class="price__note" style="color:rgba(243,235,225,.6)">координатор на весь день</p>
  </div>
</div>"""


def steps_block(steps):
    items = "".join(f'<li class="step reveal"><h3>{t}</h3><p>{d}</p></li>' for t, d in steps)
    return f'<ol class="steps" style="--n:{len(steps)}">{items}</ol>'


REVIEWS = [
    {
        "title": "Свадьба во французском особняке",
        "who": "Жених",
        "role": "сам больше 9 лет работает в свадебной индустрии",
        "text": [
            "В свадебном бизнесе я работаю уже больше 9 лет, провёл сотни торжеств и думал, что свою свадьбу организую с лёгкостью. Это была бы главная ошибка!",
            "Слава богу, я вовремя одумался, и нашим праздником занялась Vinogradova Event — всё было на высшем уровне. Если хотите получить удовольствие от собственной свадьбы, обязательно нанимайте организатора! Полина подобрала нам площадку и нашла очень крутую команду профессионалов, с которой я теперь буду работать и дальше.",
        ],
    },
    {
        "title": "Свадьба во французском особняке",
        "who": "Невеста",
        "role": "пришла по рекомендации фотографа и видеографа",
        "text": [
            "Наши друзья — видеограф и фотограф — рассказали мне про Vinogradova Event, и там я встретила Полину, которая сделала наш день незабываемым. Не знаю, как она это делает, но она прочитала меня, как книгу, и полностью поняла мой вкус! На все предложения, вплоть до цвета скатертей, я отвечала: «Да, то что нужно!»",
            "Я никогда бы не справилась сама. Зная, что рядом такой наставник, я была самой спокойной невестой. Смело могу сказать: ваше агентство — лучшее, с безупречным вкусом!",
        ],
    },
]


def reviews_block(full=True):
    out = []
    for r in REVIEWS:
        paras = r["text"] if full else r["text"][-1:]
        out.append(f"""<blockquote class="review reveal">
  <div class="review__mark" aria-hidden="true">“</div>
  {''.join(f'<p>{p}</p>' for p in paras)}
  <footer><div><b>{r['who']}</b>{r['role']}</div></footer>
</blockquote>""")
    return f'<div class="reviews">{"".join(out)}</div>'


FAQ = [
    ("Сколько стоят ваши услуги?",
     "Гонорар агентства фиксированный и зависит от общего бюджета свадьбы: от 95 000 ₽ при бюджете до 1,5 млн ₽. Для свадеб с бюджетом от 3,5 млн ₽ — 7% от бюджета. Точную сумму вы узнаете на первой встрече, ещё до подписания договора."),
    ("Что входит в организацию под ключ?",
     "Всё, что нужно для свадьбы: подбор площадки, фотографа, видеографа, ведущего, DJ, артистов, декора и оборудования, визажиста, торта, составление сметы и тайминга. В день свадьбы работают организаторы и координаторы агентства — вы ни о чём не думаете."),
    ("Можно заказать только координацию?",
     "Да. Если вы готовите свадьбу сами, координатор на весь день стоит 15 000 ₽ в Москве и 1 500 AED в Дубае. Он проследит за подрядчиками и таймингом, чтобы вы могли расслабиться."),
    ("Вы работаете только в Москве?",
     "Нет. У нас офисы в Москве и Дубае, мы проводим свадьбы в ОАЭ — в Дубае и Абу-Даби — и в Европе, например в Италии. Расскажите, где мечтаете отпраздновать, — подскажем, как это реализовать."),
    ("Свадьбы какого масштаба вы организуете?",
     "Любого: от камерной церемонии на 10 человек до праздника на сотни гостей. Наш самый крупный проект — событие на 6 000 человек."),
    ("С чего начать?",
     "Оставьте заявку или напишите в WhatsApp. Мы перезвоним, коротко обсудим ваши пожелания и договоримся о личной встрече за чашкой кофе — там и решим, какой будет ваша свадьба."),
]


def faq_block(items=FAQ):
    rows = "".join(f'<details><summary>{q}</summary><div class="faq__a">{a}</div></details>' for q, a in items)
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}
    return f'<div class="faq">{rows}</div><script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'


def video_block():
    return f"""<div class="video reveal">
  <button type="button" data-youtube="{C['youtube']}" aria-label="Смотреть бэкстейдж со свадьбы">
    <img src="https://i.ytimg.com/vi/{C['youtube']}/maxresdefault.jpg" alt="" loading="lazy">
    <span class="video__play">{icon('play', 30)}</span>
  </button>
</div>"""


HERO_CASE = ("dubai-wedding-6", "raw/023")  # e.g. ("wedding-kempinski", "raw/004")  # (case slug, gallery photo number or None for cover)


def hero_image():
    slug, n = HERO_CASE
    info = IMAGES["cases"].get(slug, {})
    if n:
        p = next((g for g in info.get("gallery", []) if g["n"] == n), None)
        if p:
            base = f"/assets/img/cases/{slug}/{n}"
            return (f'<img src="{base}.webp" srcset="{base}-sm.webp 800w, {base}.webp {p["w"]}w" sizes="100vw" '
                    f'width="{p["w"]}" height="{p["h"]}" alt="Свадьба, организованная Vinogradova Event" fetchpriority="high">')
    if info.get("cover"):
        return case_cover(CASE_BY_SLUG[slug], sizes="100vw", eager=True, full=True)
    return site_img("dubai-hero", "Свадьба, организованная Vinogradova Event", eager=True)


def press_strip():
    logos = [(r, a) for r, a in (("press-4", "Zankyou"), ("press-5", "Невеста Moscow"),
                                 ("press-1", "Публикация"), ("press-2", "Публикация")) if r in IMAGES["site"]]
    award = IMAGES["site"].get("award")
    if not logos and not award:
        return ""
    award_html = (f'<div class="press__award"><img src="/assets/img/site/award.webp" alt="White Wedding Industry Awards 2024" loading="lazy">'
                  f'<p><b>Лучшая свадьба в Дубае</b>White Wedding Industry Awards 2024</p></div>') if award else ""
    imgs = "".join(f'<img src="/assets/img/site/{r}.webp" alt="{a}" loading="lazy">' for r, a in logos)
    return f'<div class="press reveal">{award_html}<div class="press__logos"><span>О нас пишут</span>{imgs}</div></div>'


def org_ld():
    return {
        "@context": "https://schema.org", "@type": "ProfessionalService", "@id": ORG_ID,
        "name": "Vinogradova Event", "alternateName": "Виноградова Ивент",
        "description": "Свадебное агентство полного цикла: организация свадеб в Москве, Дубае и Европе с 2015 года.",
        "url": DOMAIN + "/", "image": DOMAIN + "/assets/img/site/hero.webp",
        "telephone": C["tel"], "email": C["email"], "foundingDate": "2015",
        "founder": {"@type": "Person", "name": "Полина Виноградова"},
        "address": {"@type": "PostalAddress", "streetAddress": "1-я Тверская-Ямская, 25с1",
                    "addressLocality": "Москва", "addressCountry": "RU"},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                                       "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                                       "opens": "09:00", "closes": "21:00"}],
        "areaServed": [{"@type": "City", "name": "Москва"}, {"@type": "City", "name": "Дубай"}],
        "priceRange": "от 95 000 ₽",
        "award": "White Wedding Industry Awards 2024 — «Лучшая свадьба в Дубае»",
        "sameAs": [C["instagram"], C["vk"]],
        "department": [{
            "@type": "ProfessionalService", "name": "Vinogradova Event Dubai",
            "telephone": C["dubai_tel"], "email": C["dubai_email"],
            "address": {"@type": "PostalAddress", "streetAddress": "66 Al Marsa St, Dubai Marina",
                        "addressLocality": "Dubai", "addressCountry": "AE"}}],
    }


def service_ld(name, area, currency, offers, lang="ru"):
    return {
        "@context": "https://schema.org", "@type": "Service", "name": name, "serviceType": "Организация свадьбы" if lang == "ru" else "Wedding planning",
        "provider": {"@id": ORG_ID}, "areaServed": {"@type": "City", "name": area},
        "offers": [{"@type": "Offer", "name": n, "price": str(v), "priceCurrency": currency} for n, v in offers],
    }


def case_ld(c, gallery):
    base = f"{DOMAIN}/assets/img/cases/{c['slug']}"
    d, m, y = c["date"].split(".")
    imgs = [f"{base}/cover.webp"] + [f"{base}/{p['n']}.webp" for p in gallery[:8]]
    return {
        "@context": "https://schema.org", "@type": "ImageGallery", "name": c["title"],
        "description": f"{c['title']}: {c['venue']}, {c['city']}, {c['guests']} {plural(c['guests'], 'гость', 'гостя', 'гостей')}.",
        "dateCreated": f"{y}-{m}-{d}", "inLanguage": "ru",
        "contentLocation": {"@type": "Place", "name": c["venue"], "address": c["city"]},
        "creator": {"@id": ORG_ID}, "image": imgs,
    }


DUBAI_HREFLANG = (f'<link rel="alternate" hreflang="ru" href="{DOMAIN}/dubai/">'
                  f'<link rel="alternate" hreflang="en" href="{DOMAIN}/en/dubai/">'
                  f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/dubai/">')


# ---------------------------------------------------------------- pages
def build_home():
    featured = [CASE_BY_SLUG[s] for s in ("wedding-kempinski", "wedding-villa-miketti", "wedding-italy",
                                          "dubai-wedding-6", "wedding-seneshal", "wedding-artiland")]
    steps = [
        ("Звонок", "Созваниваемся, узнаём о ваших пожеланиях и назначаем встречу."),
        ("Встреча", "Знакомимся лично за чашкой кофе и обсуждаем, какой вы видите свою свадьбу."),
        ("Предложение", "Готовим концепцию и подборку решений в рамках вашего бюджета."),
        ("Договор", "Утверждаем смету и подписываем договор — всё прозрачно и надёжно."),
        ("Подготовка", "Мы готовим праздник, вы — себя. Держим в курсе на каждом этапе."),
        ("День свадьбы", "Контролируем каждую деталь. Ваша единственная задача — наслаждаться."),
        ("Послевкусие", "Встречаемся через пару месяцев после свадьбы и передаём фото и видео."),
    ]
    insta = "".join(f'<img src="/assets/img/site/{n}.webp" alt="Фото из Instagram Vinogradova Event" loading="lazy">'
                    for n in IMAGES.get("instagram", [])[:12])
    insta_block = f'<div class="insta mt-l">{insta}</div>' if insta else ""
    ld = org_ld()
    service = service_ld("Организация свадьбы под ключ в Москве", "Москва", "RUB",
                         [("Бюджет свадьбы до 1,5 млн ₽", 95000), ("Бюджет свадьбы 1,5–2,5 млн ₽", 130000),
                          ("Бюджет свадьбы 2,5–3,5 млн ₽", 180000), ("Координатор на свадебный день", 15000)])
    body = f"""
<section class="hero">
  <div class="hero__bg">{hero_image()}</div>
  <div class="wrap hero__in">
    <span class="eyebrow">Свадебное агентство · Москва и Дубай</span>
    <h1>Свадьба, которую вы&nbsp;проживёте, а&nbsp;не&nbsp;организуете</h1>
    <p class="lead">Берём на себя всё — от выбора площадки и команды до координации в день торжества. 520+ свадеб с 2015 года в Москве, Дубае и Европе.</p>
    <div class="hero__actions">
      <a class="btn btn--gold" href="#lead">Обсудить свадьбу</a>
      <a class="btn btn--ghost" href="/portfolio/">Смотреть наши свадьбы</a>
    </div>
    <div class="hero__award">{icon('award', 34)}<span>{C['award']}</span></div>
  </div>
</section>

<section class="section section--tight">
  <div class="wrap">{stats_block()}{press_strip()}</div>
</section>

<section class="section section--cream" id="about">
  <div class="wrap split">
    <figure class="split__media reveal" style="margin:0">
      {site_img('founder', 'Полина Виноградова, основатель Vinogradova Event', sizes='(max-width: 860px) 100vw, 50vw')}
      <div class="media-badge"><b>с 2015</b>Полина лично ведёт каждый проект агентства</div>
    </figure>
    <div class="reveal">
      <span class="eyebrow">О нас</span>
      <h2>Красивая свадьба начинается с&nbsp;<em class="accent">правильного организатора</em></h2>
      <p class="lead" style="margin-top:22px">Не с примерки платья и не с визажиста — а с команды, которая услышит вас и возьмёт на себя всё остальное.</p>
      <p>Vinogradova Event — свадебное агентство с душой и большим опытом. Мы создаём свадьбы в Москве, Дубае и Европе: от камерных церемоний на 10 человек до масштабных праздников на 6 000 гостей.</p>
      <p>Мы входим в жюри TOP 100 Awards — одной из самых авторитетных свадебных премий. Поэтому лучшие фотографы, ведущие и декораторы для нас не строчки в каталоге, а коллеги, которых мы знаем лично.</p>
      <blockquote class="quote" style="margin-top:34px">
        <p>«Я лично вовлечена в каждый этап подготовки, потому что хочу, чтобы ваш день был особенным: с душой, вниманием к мелочам и уважением к вашей истории. Я рядом от первой встречи до передачи фотографий».</p>
        <footer><b>Полина Виноградова</b>основатель агентства и вдохновитель команды</footer>
      </blockquote>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div><span class="eyebrow">Почему мы</span><h2>Вы наслаждаетесь — мы&nbsp;отвечаем за&nbsp;результат</h2></div>
      <p>Шесть причин, по которым пары доверяют нам самый важный день — и часто становятся нашими друзьями.</p>
    </div>
    <div class="cards">
      <div class="card reveal"><span class="card__num">01</span><h3>Личное участие основателя</h3><p>Полина Виноградова ведёт каждый проект сама — от первой встречи до передачи фото и видео.</p></div>
      <div class="card reveal"><span class="card__num">02</span><h3>Команда, а не один человек</h3><p>Свадьбу готовят 3 организатора, а в сам день работают от 2 координаторов. Ни одна деталь не останется без присмотра.</p></div>
      <div class="card reveal"><span class="card__num">03</span><h3>Лучшие подрядчики</h3><p>Как члены жюри TOP 100 Awards, мы лично знаем сильнейших специалистов индустрии и подбираем тех, кто подходит именно вам.</p></div>
      <div class="card reveal"><span class="card__num">04</span><h3>Понятная стоимость</h3><p>Фиксированный гонорар, прозрачная смета и договор. Вы заранее знаете, за что и сколько платите.</p></div>
      <div class="card reveal"><span class="card__num">05</span><h3>Москва, Дубай и мир</h3><p>Офисы и команды в Москве и Дубае. Проводим свадьбы в ОАЭ, Италии и других странах.</p></div>
      <div class="card reveal"><span class="card__num">06</span><h3>Рядом и после свадьбы</h3><p>Закрытый чат для невест и уютные встречи по интересам — наше общение не заканчивается в день торжества.</p></div>
    </div>
    <div class="team-row mt-l">
      <figure class="reveal">{site_img('hero', 'Команда Vinogradova Event с молодожёнами', sizes='(max-width: 760px) 100vw, 50vw')}<figcaption>Команда Vinogradova Event в день свадьбы</figcaption></figure>
      <figure class="reveal">{site_img('dubai-teaser', 'В офисе Vinogradova Event', sizes='(max-width: 760px) 100vw, 50vw')}<figcaption>В офисе Vinogradova Event</figcaption></figure>
    </div>
  </div>
</section>

<section class="section section--cream" id="portfolio">
  <div class="wrap">
    <div class="section-head">
      <div><span class="eyebrow">Портфолио</span><h2>Свадьбы, которые мы создали</h2></div>
      <a class="link-arrow" href="/portfolio/">Все {len(CASES)} историй {icon('arrow', 16)}</a>
    </div>
    <div class="grid-cases">{case_cards(featured)}</div>
  </div>
</section>

<section class="section">
  <div class="wrap split split--wide-text">
    {video_block()}
    <div class="reveal">
      <span class="eyebrow">За кадром</span>
      <h2>Посмотрите, как мы работаем в&nbsp;день свадьбы</h2>
      <p class="lead" style="margin-top:20px">Бэкстейдж с реальной свадьбы: пока гости танцуют, команда держит под контролем каждую минуту тайминга.</p>
    </div>
  </div>
</section>

<section class="section section--cream" id="price">
  <div class="wrap">
    <div class="section-head">
      <div><span class="eyebrow">Услуги и цены</span><h2>Стоимость организации свадьбы в&nbsp;Москве</h2></div>
      <p>Гонорар агентства фиксирован и зависит от бюджета свадьбы. Вы знаете сумму до подписания договора. Цены для Дубая — <a href="/dubai/#price">на отдельной странице</a>.</p>
    </div>
    {pricing_block('moscow')}
    <div class="actions"><a class="btn btn--gold" href="#lead">Рассчитать мою свадьбу</a></div>
  </div>
</section>

<section class="section section--dark">
  <div class="wrap">
    <div class="section-head">
      <div><span class="eyebrow">Как мы работаем</span><h2>Семь шагов к&nbsp;идеальной свадьбе</h2></div>
      <p style="color:rgba(243,235,225,.7)">Понятный процесс без сюрпризов: вы всегда знаете, что происходит и что будет дальше.</p>
    </div>
    {steps_block(steps)}
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="banner reveal">
      {site_img('dubai-hero', 'Свадьба в Дубае на Bluewaters')}
      <div class="banner__in">
        <span class="eyebrow">Свадьба в Дубае</span>
        <h2>Мечтаете о свадьбе у моря?</h2>
        <p class="lead" style="margin-top:18px">У нас есть офис и своя команда в Дубае. Организуем свадьбу в ОАЭ под ключ — именно здесь мы получили премию «Лучшая свадьба в Дубае».</p>
        <div class="actions"><a class="btn btn--gold" href="/dubai/">Свадьба в Дубае</a></div>
      </div>
    </div>
  </div>
</section>

<section class="section section--cream">
  <div class="wrap">
    <div class="section-head">
      <div><span class="eyebrow">Отзывы</span><h2>Что говорят наши пары</h2></div>
      <a class="link-arrow" href="/reviews/">Все отзывы {icon('arrow', 16)}</a>
    </div>
    {reviews_block(full=False)}
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="reveal">
      <span class="eyebrow">Обучение</span>
      <h2>Хотите сами стать свадебным организатором?</h2>
      <p class="lead" style="margin-top:20px">Индивидуальный онлайн-курс от Полины Виноградовой: месяц занятий, готовые шаблоны документов и практика на реальной свадьбе.</p>
      <div class="actions"><a class="btn btn--ghost" href="/education/">Подробнее о курсе</a></div>
    </div>
    <div class="reveal">
      <span class="eyebrow">Вопросы и ответы</span>
      {faq_block(FAQ[:3])}
      <p style="margin-top:20px"><a class="link-arrow" href="/contacts/#faq">Все вопросы {icon('arrow', 16)}</a></p>
    </div>
  </div>
</section>

{lead_section()}

<section class="section section--tight">
  <div class="wrap center">
    <span class="eyebrow">Instagram</span>
    <h2>Больше свадеб — в&nbsp;наших соцсетях</h2>
    <div class="actions" style="justify-content:center">
      <a class="btn btn--ghost" href="{C['instagram']}" target="_blank" rel="noopener">{icon('ig', 18)} @vinogradova_event</a>
      <a class="btn btn--ghost" href="{C['vk']}" target="_blank" rel="noopener">{icon('vk', 18)} ВКонтакте</a>
    </div>
    {insta_block}
  </div>
</section>
"""
    page("/", "Vinogradova Event — свадебное агентство в Москве и Дубае",
         "Организация свадьбы под ключ в Москве, Дубае и Европе. 520+ свадеб с 2015 года, победители премии «Лучшая свадьба в Дубае». Гонорар от 95 000 ₽.",
         "home", body, extra_head=ld_script(ld, service))


def build_portfolio():
    counts = {r: sum(1 for c in CASES if c["region"] == r) for r in REGION_LABEL}
    chips = [("all", "Все", len(CASES)), ("moscow", "Москва и Россия", counts["moscow"]),
             ("dubai", "Дубай и ОАЭ", counts["dubai"]), ("europe", "Европа", counts["europe"])]
    chip_html = "".join(f'<button class="chip" type="button" data-filter="{k}" aria-pressed="{str(k == "all").lower()}">{l}<small>{n}</small></button>'
                        for k, l, n in chips)
    body = f"""
<section class="hero hero--plain">
  <div class="wrap hero__in">
    <div class="crumbs"><a href="/">Главная</a> / Портфолио</div>
    <span class="eyebrow">Портфолио</span>
    <h1>Свадьбы, которые мы&nbsp;создали</h1>
    <p class="lead">{len(CASES)} историй из Москвы, Дубая, Абу-Даби и Италии — от предложения руки и сердца вдвоём до праздника на 120 гостей. Выберите место, которое откликается, — и мы расскажем, как сделать там вашу свадьбу.</p>
  </div>
</section>
<section class="section" style="padding-top:48px">
  <div class="wrap">
    <div class="filters" role="group" aria-label="Фильтр по месту">{chip_html}</div>
    <div class="grid-cases">{case_cards(CASES)}</div>
  </div>
</section>
{lead_section(title="Понравилась площадка? Обсудим вашу свадьбу", eyebrow="Ваша история")}
"""
    page("/portfolio/", "Портфолио свадеб — Vinogradova Event",
         "Свадьбы, организованные Vinogradova Event в Москве, Подмосковье, Дубае, Абу-Даби и Италии: фото, площадки, количество гостей.",
         "portfolio", body)


def build_cases():
    for i, c in enumerate(CASES):
        prev_c, next_c = CASES[i - 1], CASES[(i + 1) % len(CASES)]
        g = IMAGES["cases"].get(c["slug"], {}).get("gallery", [])
        base = f'/assets/img/cases/{c["slug"]}'
        gallery = "".join(
            f'<a href="{base}/{p["n"]}.webp"><img src="{base}/{p["n"]}-sm.webp" width="{min(p["w"], 800)}" '
            f'height="{round(p["h"] * min(p["w"], 800) / p["w"])}" alt="{e(c["title"])} — фото {k + 1}" loading="lazy" decoding="async"></a>'
            for k, p in enumerate(g))
        if not gallery:
            gallery = '<p class="lead">Фотографии скоро появятся.</p>'
        is_dubai = c["region"] == "dubai"
        wa = C["dubai_wa"] if is_dubai else C["wa"]
        guests = f'{c["guests"]}'
        cover_info = IMAGES["cases"].get(c["slug"], {}).get("cover")
        hero_bg = case_cover(c, sizes="100vw", eager=True, full=True) if cover_info else ""
        kind = "Предложение" if "proposal" in c["slug"] else "Love story" if "love-story" in c["slug"] else "Роспись" if "engaging" in c["slug"] else "Свадьба"
        body = f"""
<section class="hero hero--page">
  <div class="hero__bg">{hero_bg}</div>
  <div class="wrap hero__in">
    <div class="crumbs"><a href="/">Главная</a> / <a href="/portfolio/">Портфолио</a> / {e(c['title'])}</div>
    <span class="eyebrow">{kind} · {e(c['city'])}</span>
    <h1>{e(c['title'])}</h1>
  </div>
</section>
<section class="section section--tight section--cream">
  <div class="wrap">
    <dl class="facts" style="margin:0">
      <div><dt>Место</dt><dd>{e(c['venue'])}</dd></div>
      <div><dt>Локация</dt><dd>{e(c['city'])}</dd></div>
      <div><dt>Гостей</dt><dd>{guests}</dd></div>
      <div><dt>Дата</dt><dd>{c['date']}</dd></div>
    </dl>
  </div>
</section>
<section class="section" style="padding-top:56px">
  <div class="wrap">
    <div class="gallery">{gallery}</div>
    <div class="actions" style="justify-content:center;margin-top:48px">
      <a class="btn btn--gold" href="#lead">Хочу свадьбу в этом месте</a>
      <a class="btn btn--ghost" href="/portfolio/">Все свадьбы</a>
    </div>
  </div>
</section>
<section class="section section--tight">
  <div class="wrap case-nav">
    <a href="/{prev_c['slug']}/"><small>← Предыдущая</small><b>{e(prev_c['title'])}</b></a>
    <a href="/{next_c['slug']}/"><small>Следующая →</small><b>{e(next_c['title'])}</b></a>
  </div>
</section>
{lead_section(
    title="Хотите свадьбу в&nbsp;этом месте?",
    text=f"Расскажите о ваших планах — подскажем, свободна ли площадка «{e(c['venue'])}» на вашу дату, и рассчитаем бюджет.",
    wa=wa,
    phone=C['dubai_phone'] if is_dubai else None, tel=C['dubai_tel'] if is_dubai else None,
    email=C['dubai_email'] if is_dubai else None, address=C['dubai_address'] if is_dubai else None,
    map_url=C['dubai_map'] if is_dubai else None,
    eyebrow=e(c['venue']),
    form_kw=dict(title="Узнать о дате и бюджете", lead_name=f"Заявка со страницы «{c['title']}»", venue=c['venue'],
                 city_default="Дубай / ОАЭ" if is_dubai else "Москва" if c['region'] == 'moscow' else "Другая страна", button="Отправить заявку"))}
"""
        og = f"/assets/img/cases/{c['slug']}/cover.webp" if cover_info else None
        page(f"/{c['slug']}/", f"{c['title']} — Vinogradova Event",
             f"{c['title']}: {c['venue']}, {c['city']}, {c['guests']} {plural(c['guests'], 'гость', 'гостя', 'гостей')}. Фото и детали проекта свадебного агентства Vinogradova Event.",
             "portfolio", body, og_image=og, wa=wa, extra_head=ld_script(case_ld(c, g)))


def build_dubai():
    dubai_cases = [c for c in CASES if c["region"] == "dubai"]
    steps = [
        ("Звонок или WhatsApp", "Связываемся, обсуждаем детали и договариваемся о встрече — лично или онлайн."),
        ("Встреча", "Показываем варианты площадок, программы и декора, составляем бюджет."),
        ("Договор", "Утверждаем смету и подписываем договор — чтобы вам было спокойно."),
        ("Общий чат", "Создаём чат проекта: все решения, согласования и новости — в одном месте."),
        ("День свадьбы", "Контролируем весь процесс на площадке. Вы просто наслаждаетесь."),
        ("Послевкусие", "Встречаемся через пару месяцев и передаём фото и видео."),
    ]
    body = f"""
<section class="hero">
  <div class="hero__bg">{site_img('dubai-hero', 'Свадьба в Дубае от Vinogradova Event', eager=True)}</div>
  <div class="wrap hero__in">
    <div class="crumbs"><a href="/">Главная</a> / Дубай</div>
    <span class="eyebrow">Свадьбы в Дубае и ОАЭ</span>
    <h1>Свадьба в&nbsp;Дубае под&nbsp;ключ — с&nbsp;командой, которая живёт здесь</h1>
    <p class="lead">Офис в Dubai Marina, проверенные площадки и подрядчики. Возьмём на себя всё — от выбора отеля до последнего танца, а вы просто прилетите на свою свадьбу.</p>
    <div class="hero__actions">
      <a class="btn btn--gold" href="#lead">Обсудить свадьбу в Дубае</a>
      <a class="btn btn--wa" href="https://wa.me/{C['dubai_wa']}" target="_blank" rel="noopener">{icon('wa', 18)} WhatsApp</a>
      <a class="btn btn--ghost" href="/en/dubai/" lang="en" hreflang="en">English version</a>
    </div>
    <div class="hero__award">{icon('award', 34)}<span>{C['award']}</span></div>
  </div>
</section>

<section class="section section--tight"><div class="wrap">{stats_block()}</div></section>

<section class="section section--cream">
  <div class="wrap">
    <div class="section-head">
      <div><span class="eyebrow">Почему с нами</span><h2>Свадьба за границей — без&nbsp;стресса и&nbsp;перелётов на&nbsp;встречи</h2></div>
    </div>
    <div class="cards">
      <div class="card reveal"><span class="card__num">01</span><h3>Своя команда в Дубае</h3><p>Организаторы и координаторы работают на месте: смотрят площадки, встречаются с подрядчиками и контролируют подготовку вместо вас.</p></div>
      <div class="card reveal"><span class="card__num">02</span><h3>Знаем лучшие площадки</h3><p>Kempinski The Palm, Bluewaters, Hyatt Regency, Anantara в Абу-Даби, частные виллы — подберём место под ваш стиль и бюджет.</p></div>
      <div class="card reveal"><span class="card__num">03</span><h3>Признанное качество</h3><p>Наша свадьба в Дубае получила премию White Wedding Industry Awards 2024 в номинации «Лучшая свадьба в Дубае».</p></div>
      <div class="card reveal"><span class="card__num">04</span><h3>Удобно на расстоянии</h3><p>Общий чат проекта и согласования онлайн — вы в курсе каждого решения, где бы ни находились.</p></div>
      <div class="card reveal"><span class="card__num">05</span><h3>Свадьба или предложение</h3><p>Организуем не только свадьбу, но и романтичное предложение руки и сердца в самых красивых местах Дубая.</p></div>
      <div class="card reveal"><span class="card__num">06</span><h3>Опыт с 2015 года</h3><p>Более 520 свадеб в России и ОАЭ — от камерных церемоний до праздников на сотни гостей.</p></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div><span class="eyebrow">Портфолио</span><h2>Наши свадьбы в ОАЭ</h2></div>
      <a class="link-arrow" href="/portfolio/#dubai">Смотреть все {icon('arrow', 16)}</a>
    </div>
    <div class="grid-cases">{case_cards(dubai_cases, with_region=False)}</div>
  </div>
</section>

<section class="section section--cream" id="price">
  <div class="wrap">
    <div class="section-head">
      <div><span class="eyebrow">Услуги и цены</span><h2>Стоимость организации свадьбы в&nbsp;Дубае</h2></div>
      <p>Фиксированный гонорар агентства в зависимости от бюджета свадьбы. Итоговую сумму вы знаете до подписания договора.</p>
    </div>
    {pricing_block('dubai')}
    <div class="actions"><a class="btn btn--gold" href="#lead">Рассчитать мою свадьбу</a></div>
  </div>
</section>

<section class="section section--dark">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">Как мы работаем</span><h2>Шесть шагов к&nbsp;свадьбе в&nbsp;Дубае</h2></div></div>
    {steps_block(steps)}
  </div>
</section>

{lead_section(
    title="Обсудим вашу свадьбу в&nbsp;Дубае?",
    text="Оставьте заявку или напишите в WhatsApp — расскажем о площадках, датах и бюджете. Консультация ни к чему не обязывает.",
    wa=C['dubai_wa'], phone=C['dubai_phone'], tel=C['dubai_tel'], email=C['dubai_email'],
    address=C['dubai_address'], map_url=C['dubai_map'], eyebrow="Офис в Dubai Marina",
    form_kw=dict(title="Заявка на свадьбу в Дубае", lead_name="Заявка: свадьба в Дубае", city_default="Дубай / ОАЭ"))}
"""
    page("/dubai/", "Свадьба в Дубае под ключ — Vinogradova Event",
         "Организация свадьбы и предложения руки и сердца в Дубае и Абу-Даби. Офис в Dubai Marina, победители премии «Лучшая свадьба в Дубае». Гонорар от 8 500 AED.",
         "dubai", body, og_image="/assets/img/site/dubai-hero.webp", wa=C["dubai_wa"],
         extra_head=ld_script(service_ld("Организация свадьбы под ключ в Дубае", "Дубай", "AED",
                                         [("Бюджет свадьбы до 150 000 AED", 8500), ("Бюджет свадьбы 150 000–250 000 AED", 12500),
                                          ("Бюджет свадьбы 250 000–400 000 AED", 18000), ("Координатор на свадебный день", 1500)])) + DUBAI_HREFLANG)


EDU_MODULES = [
    ("Работа с парой и первые этапы организации", [
        "Секреты успешной первой встречи: как расположить к себе пару и заключить договор",
        "Готовые шаблоны: первичный бюджет, планировщик, анкета молодожёнов, рассадка гостей",
        "Как составить первичную смету и грамотно распределить бюджет",
        "База свадебных площадок Москвы: цены, условия аренды и особенности",
        "Идеи для welcome-зоны: развлечения для гостей с примерами и ценами",
        "На чём молодожёны могут сэкономить без потери качества",
        "Как презентовать свои услуги и обосновать стоимость работы организатора",
        "Ответы на частые вопросы невест: дождь, число координаторов, форс-мажоры",
    ]),
    ("Работа с подрядчиками: от выбора до договора", [
        "Что спросить у площадки до подписания договора, чтобы избежать штрафов и претензий",
        "Как выбрать профессионального ведущего",
        "Как подобрать кавер-группу и разобраться в технических и бытовых райдерах",
        "Нюансы выбора визажиста и стилиста для невесты",
        "Фотографы и видеографы: обязательные вопросы и ключевые пункты договоров",
        "Договоры подрядчиков и система оплат",
        "Где искать проверенных подрядчиков и как собрать свою базу",
        "Главные ошибки начинающих организаторов",
        "Чем организатор отличается от координатора",
    ]),
    ("Техническое оснащение мероприятий", [
        "Виды оборудования: что как называется и для чего используется",
        "Свет, звук, экраны и спецэффекты: как создать WOW-эффект",
        "Тяжёлый дым или сценический туман — в чём разница",
        "Как подобрать оборудование под концепцию и площадку",
        "Как составить техническое задание для подрядчиков",
        "Как читать технические сметы и не переплачивать",
        "Как контролировать монтаж и работу технической команды",
    ]),
    ("День свадьбы: координация и тайминг", [
        "Рабочие документы: тайминги, чек-листы, монтажные планы, внутренняя смета, годовой финансовый отчёт",
        "Порядок свадьбы: велком, церемония, банкет, шоу-программа и финал",
        "Как составить идеальный тайминг свадебного дня",
        "«Волшебный чемоданчик» организатора: вещи, которые спасают в непредвиденных ситуациях",
        "Все нюансы проведения свадебной церемонии",
        "Сколько нужно координаторов, где найти команду и как распределять задачи",
        "Форс-мажоры: реальные случаи из практики и их решения",
        "Как контролировать подрядчиков и соблюдать тайминг",
        "Внешний вид, этикет и правила поведения команды на площадке",
    ]),
    ("От концепции до реализации: ваш собственный проект", [
        "Выпускная работа — собственная свадебная концепция",
        "Как создать уникальную концепцию и красиво презентовать её паре",
        "Расчёты с подрядчиками и контроль платежей",
        "Монтажный план: что учитывать",
        "Как принимать фото- и видеоматериалы после свадьбы",
        "Как сформировать стоимость своих услуг",
        "Как продвигать себя и найти первых клиентов",
        "С чего начать собственное свадебное агентство",
    ]),
]


def build_education():
    modules = "".join(
        f'<details class="module"{" open" if i == 0 else ""}><summary><h3>{t}</h3></summary><ul>{"".join(f"<li>{x}</li>" for x in items)}</ul></details>'
        for i, (t, items) in enumerate(EDU_MODULES))
    body = f"""
<section class="hero hero--plain">
  <div class="wrap hero__in split">
    <div>
      <div class="crumbs"><a href="/">Главная</a> / Обучение</div>
      <span class="eyebrow">Индивидуальный онлайн-курс</span>
      <h1>Свадебный организатор: профессия за&nbsp;месяц</h1>
      <p class="lead" style="margin-top:22px">Персональные занятия с основателем Vinogradova Event, готовая база документов и практика на реальной свадьбе. Без воды — только инструменты, которые работают на сотнях наших мероприятий.</p>
      <div class="hero__actions"><a class="btn btn--gold" href="#lead">Записаться на курс</a><a class="btn btn--ghost" href="#program">Программа</a></div>
    </div>
    <div class="course-card reveal">
      <span class="eyebrow">Стоимость</span>
      <div class="price__fee" style="margin-top:0;border:0;padding:0;font-size:52px">35 000 ₽</div>
      <ul class="checks">
        <li>Персональные онлайн-занятия с руководителем агентства</li>
        <li>1 месяц обучения в удобное для вас время</li>
        <li>Готовая база документов и шаблонов</li>
        <li>Бонус: практика на реальной свадьбе</li>
        <li>Сертификат по окончании курса</li>
      </ul>
      <div class="actions"><a class="btn btn--gold btn--block" href="#lead">Оставить заявку</a></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">Для кого</span><h2>Курс подойдёт, если вы</h2></div></div>
    <div class="cards" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">
      <div class="card reveal"><span class="card__num">01</span><h3>Начинающий организатор</h3><p>Хотите выстроить работу системно и уверенно взять первые проекты.</p></div>
      <div class="card reveal"><span class="card__num">02</span><h3>Невеста</h3><p>Решили организовать собственную свадьбу сами — и сделать это без ошибок.</p></div>
      <div class="card reveal"><span class="card__num">03</span><h3>Ищете себя в ивентах</h3><p>Сфера интересна, но непонятно, с чего начать.</p></div>
      <div class="card reveal"><span class="card__num">04</span><h3>Студент event-менеджмента</h3><p>Хотите получить практику, которой нет в учебных программах.</p></div>
    </div>
  </div>
</section>

<section class="section section--cream" id="program">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">Программа</span><h2>Пять блоков — от первой встречи до своего агентства</h2></div></div>
    <div class="modules">{modules}</div>
    <div class="actions"><a class="btn btn--gold" href="#lead">Записаться на курс</a></div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">Результат</span><h2>После курса вы&nbsp;сможете</h2></div></div>
    <div class="cards">
      <div class="card reveal"><h3>Выстроить рабочий процесс</h3><p>Чётко планировать этапы, составлять чек-листы и грамотно подбирать подрядчиков.</p></div>
      <div class="card reveal"><h3>Понимать желания пары</h3><p>Узнавать, чего на самом деле хотят клиенты, — это главная гарантия успеха свадьбы.</p></div>
      <div class="card reveal"><h3>Решать форс-мажоры</h3><p>Не паниковать, а с холодной головой справляться с конфликтами и неожиданностями.</p></div>
      <div class="card reveal"><h3>Читать договоры</h3><p>Понимать каждый пункт и защищать себя от неустоек и недобросовестных подрядчиков.</p></div>
      <div class="card reveal"><h3>Знать цену своей работы</h3><p>Обоснованно формировать стоимость услуг и уверенно объяснять её клиентам.</p></div>
      <div class="card reveal"><h3>Конкурировать на рынке</h3><p>Получить сильный старт и уверенность в своих силах — даже без портфолио.</p></div>
    </div>
  </div>
</section>

<section class="section section--cream">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">Бонусы</span><h2>Что ещё вас ждёт</h2></div></div>
    <div class="cards">
      <div class="card reveal"><h3>Практика на свадьбе</h3><p>Работа на реальной свадьбе под руководством профессиональных организаторов.</p></div>
      <div class="card reveal"><h3>Полный пакет документов</h3><p>Шаблоны, чек-листы и тайминги, которые агентство использует в работе каждый день.</p></div>
      <div class="card reveal"><h3>Свадьбы в Дубае</h3><p>Особенности работы с площадками и подрядчиками в ОАЭ.</p></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <figure class="split__media reveal" style="margin:0">{site_img('founder', 'Полина Виноградова, автор курса', sizes='(max-width: 860px) 100vw, 50vw')}</figure>
    <div class="reveal">
      <span class="eyebrow">Автор курса</span>
      <h2>Полина Виноградова</h2>
      <p class="lead" style="margin-top:16px">Основатель Vinogradova Event, свадебный организатор и автор образовательных программ.</p>
      <ul class="checks">
        <li>520+ мероприятий в России и ОАЭ</li>
        <li>В индустрии с 2015 года</li>
        <li>Премия White Wedding Industry Awards 2024, «Лучшая свадьба в Дубае»</li>
        <li>Член жюри TOP 100 Awards</li>
        <li>Публикации в Wedding, Star Hit и международных свадебных изданиях</li>
      </ul>
      <blockquote class="quote" style="margin-top:32px">
        <p>«Когда я начинала, мне не хватало человека, который объяснил бы, как всё устроено на практике. Поэтому в курсе я делюсь не абстрактными советами, а реальными инструментами, документами и опытом сотен мероприятий».</p>
      </blockquote>
    </div>
  </div>
</section>

{lead_section(title="Запишитесь на&nbsp;курс",
              text="Оставьте контакты — расскажем о ближайшем старте, ответим на вопросы и подберём удобное расписание.",
              eyebrow="Обучение",
              form_kw=dict(title="Заявка на курс", note="Свяжемся с вами в ближайшее время.", lead_name="Заявка на курс «Свадебный организатор»", button="Записаться"))}
"""
    page("/education/", "Курс «Свадебный организатор» — обучение от Vinogradova Event",
         "Индивидуальный онлайн-курс для свадебных организаторов от Полины Виноградовой: 1 месяц, шаблоны документов, практика на свадьбе, сертификат. 35 000 ₽.",
         "education", body, extra_head=ld_script({
             "@context": "https://schema.org", "@type": "Course", "name": "Свадебный организатор",
             "description": "Индивидуальный онлайн-курс по организации свадеб: работа с парой и подрядчиками, техническое оснащение, координация свадебного дня, собственный проект.",
             "provider": {"@id": ORG_ID, "@type": "Organization", "name": "Vinogradova Event", "sameAs": DOMAIN + "/"},
             "inLanguage": "ru",
             "offers": [{"@type": "Offer", "category": "Paid", "price": "35000", "priceCurrency": "RUB"}],
             "hasCourseInstance": [{"@type": "CourseInstance", "courseMode": "Online", "courseWorkload": "P1M",
                                    "instructor": {"@type": "Person", "name": "Полина Виноградова"}}]}))


def build_reviews():
    body = f"""
<section class="hero hero--plain">
  <div class="wrap hero__in">
    <div class="crumbs"><a href="/">Главная</a> / Отзывы</div>
    <span class="eyebrow">Отзывы</span>
    <h1>Нам доверяют самый важный день</h1>
    <p class="lead">Счастливые глаза пар — наша главная награда. Многие из них становятся нашими друзьями и возвращаются к нам с семейными праздниками.</p>
  </div>
</section>
<section class="section"><div class="wrap">{reviews_block(full=True)}</div></section>
<section class="section section--cream">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">Портфолио</span><h2>Посмотрите на наши свадьбы</h2></div>
      <a class="link-arrow" href="/portfolio/">Все свадьбы {icon('arrow', 16)}</a></div>
    <div class="grid-cases">{case_cards([CASE_BY_SLUG[s] for s in ('wedding-kempinski', 'wedding-tayny-rubleva', 'wedding-jan-remi')])}</div>
  </div>
</section>
{lead_section()}
"""
    page("/reviews/", "Отзывы о свадебном агентстве Vinogradova Event",
         "Отзывы пар о работе свадебного агентства Vinogradova Event в Москве и Дубае.", "reviews", body)


def build_contacts():
    body = f"""
<section class="hero hero--plain">
  <div class="wrap hero__in">
    <div class="crumbs"><a href="/">Главная</a> / Контакты</div>
    <span class="eyebrow">Контакты</span>
    <h1>Приходите на кофе — обсудим вашу свадьбу</h1>
    <p class="lead">Два офиса — в Москве и Дубае. Позвоните, напишите в WhatsApp или оставьте заявку: перезвоним и договоримся о встрече.</p>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="price-extra offices">
      <div class="price-box">
        <span class="eyebrow">Москва</span>
        <ul class="contact-lines" style="margin-top:8px">
          <li>{icon('phone')}<div><a href="tel:{C['tel']}">{C['phone']}</a><small>{C['hours']}</small></div></li>
          <li>{icon('wa')}<div><a href="https://wa.me/{C['wa']}" target="_blank" rel="noopener">Написать в WhatsApp</a></div></li>
          <li>{icon('mail')}<div><a href="mailto:{C['email']}">{C['email']}</a></div></li>
          <li>{icon('pin')}<div><a href="{C['map']}" target="_blank" rel="noopener">{C['address']}</a></div></li>
        </ul>
      </div>
      <div class="price-box">
        <span class="eyebrow">Дубай</span>
        <ul class="contact-lines" style="margin-top:8px">
          <li>{icon('phone')}<div><a href="tel:{C['dubai_tel']}">{C['dubai_phone']}</a><small>9:00–21:00 по времени Дубая</small></div></li>
          <li>{icon('wa')}<div><a href="https://wa.me/{C['dubai_wa']}" target="_blank" rel="noopener">Написать в WhatsApp</a></div></li>
          <li>{icon('mail')}<div><a href="mailto:{C['dubai_email']}">{C['dubai_email']}</a></div></li>
          <li>{icon('pin')}<div><a href="{C['dubai_map']}" target="_blank" rel="noopener">{C['dubai_address']}</a></div></li>
        </ul>
      </div>
    </div>
  </div>
</section>
<section class="section section--cream" id="faq">
  <div class="wrap split" style="align-items:start">
    <div><span class="eyebrow">Вопросы и ответы</span><h2>Частые вопросы</h2>
      <p class="lead" style="margin-top:18px">Не нашли ответа? Напишите нам — ответим лично.</p></div>
    {faq_block()}
  </div>
</section>
{lead_section()}
"""
    page("/contacts/", "Контакты — Vinogradova Event, свадебное агентство",
         f"Свадебное агентство Vinogradova Event: {C['phone']}, {C['email']}, {C['address']}. Офис в Дубае: {C['dubai_phone']}.",
         "contacts", body)


def build_policy():
    src = (ROOT / "data/policy.txt").read_text().strip().split("\n")
    parts = []
    for line in src:
        line = line.strip()
        if not line:
            continue
        if line[:2].rstrip(".").isdigit() and ". " in line[:4]:
            parts.append(f"<h2>{e(line)}</h2>")
        else:
            parts.append(f"<p>{e(line)}</p>")
    body = f"""
<section class="hero hero--plain"><div class="wrap hero__in">
  <div class="crumbs"><a href="/">Главная</a> / Политика конфиденциальности</div>
  <h1>Политика в&nbsp;отношении обработки персональных данных</h1>
</div></section>
<section class="section"><div class="wrap prose">{''.join(parts)}</div></section>
"""
    page("/policy/", "Политика конфиденциальности — Vinogradova Event",
         "Политика в отношении обработки персональных данных пользователей сайта v-event.ru.", "", body)


def build_404():
    body = f"""
<section class="hero hero--plain"><div class="wrap hero__in center">
  <span class="eyebrow">Ошибка 404</span>
  <h1>Такой страницы нет</h1>
  <p class="lead">Возможно, она переехала. Начните с главной или посмотрите наши свадьбы.</p>
  <div class="hero__actions" style="justify-content:center"><a class="btn btn--gold" href="/">На главную</a><a class="btn btn--ghost" href="/portfolio/">Портфолио</a></div>
</div></section>
{lead_section()}
"""
    page("/404.html", "Страница не найдена — Vinogradova Event", "Страница не найдена.", "", body)
    SITEMAP.remove("/404.html")



# ---------------------------------------------------------------- English Dubai page
def build_dubai_en():
    path = "/en/dubai/"
    wa = C["dubai_wa"]
    cases = [c for c in CASES if c["region"] == "dubai"]

    def cards():
        out = []
        for c in cases:
            href = f"/{c['slug']}/"
            gallery = IMAGES["cases"].get(c["slug"], {}).get("gallery", [])[: CARD_PHOTOS - 1]
            base = f'/assets/img/cases/{c["slug"]}'
            title = c.get("title_en", c["title"])
            slides = [f'<a class="slide" href="{href}" tabindex="-1">{case_cover(c).replace(e(c["title"]), e(title))}</a>']
            for k, p in enumerate(gallery, 2):
                h = round(p["h"] * min(p["w"], 800) / p["w"])
                slides.append(f'<a class="slide" href="{href}" tabindex="-1"><img src="{base}/{p["n"]}-sm.webp" width="{min(p["w"], 800)}" '
                              f'height="{h}" alt="{e(title)} — photo {k}" loading="lazy" decoding="async"></a>')
            dots = "".join(f'<span{" class=\"on\"" if i == 0 else ""}></span>' for i in range(len(slides)))
            city = "Abu Dhabi" if "Абу" in c["city"] else "Dubai"
            out.append(f"""<article class="case-card reveal">
  <div class="case-card__img slider">
    <div class="slider__track" data-slider>{''.join(slides)}</div>
    <button class="slider__btn slider__btn--prev" type="button" aria-label="Previous photo">‹</button>
    <button class="slider__btn slider__btn--next" type="button" aria-label="Next photo">›</button>
    <div class="slider__dots" aria-hidden="true">{dots}</div>
  </div>
  <h3><a href="{href}">{e(title)}</a></h3>
  <p>{city} · {c['guests']} {'guest' if c['guests'] == 1 else 'guests'} · {c['date'][-4:]}</p>
</article>""")
        return "\n".join(out)

    tiers = [("up to 150,000 AED", "8,500 AED", False), ("150,000–250,000 AED", "12,500 AED", True),
             ("250,000–400,000 AED", "18,000 AED", False), ("from 400,000 AED", "8%", False)]
    price_cards = "".join(f"""<div class="price{' price--hl" data-label="Most popular' if hl else ''}">
  <div class="price__budget">Wedding budget<b>{b}</b></div>
  <div class="price__fee">{fee}</div>
  <p class="price__note">{'of the wedding budget' if fee.endswith('%') else 'agency fee'}</p>
</div>""" for b, fee, hl in tiers)

    steps = [
        ("Call or WhatsApp", "Tell us about your plans and we'll set up a meeting — in person or online."),
        ("Meeting", "We show you venue options, programme and décor ideas, and draft a budget."),
        ("Contract", "We agree the estimate and sign a contract, so you know exactly what to expect."),
        ("Project chat", "One shared chat for every decision, approval and update."),
        ("Wedding day", "Our team runs the day on site. Your only job is to enjoy it."),
        ("Afterglow", "A couple of months later we meet again and hand over your photos and video."),
    ]
    faq = [
        ("How much does a wedding planner in Dubai cost?",
         "Our fee is fixed and depends on the total wedding budget: from 8,500 AED for budgets up to 150,000 AED, and 8% for budgets from 400,000 AED. You know the exact fee before signing the contract."),
        ("What is included in full planning?",
         "Venue search and booking, photographer, videographer, host, DJ and performers, décor, florals and technical equipment, hair and make-up, the cake, the budget and the day's timeline — plus 2 planners during preparation and at least 2 coordinators on the wedding day."),
        ("Can we book day-of coordination only?",
         "Yes. If you are planning the wedding yourselves, a coordinator for the whole wedding day costs 1,500 AED."),
        ("Do you also plan proposals?",
         "Yes — we organise marriage proposals in some of the most beautiful spots in Dubai."),
    ]
    faq_html = "".join(f'<details><summary>{q}</summary><div class="faq__a">{a}</div></details>' for q, a in faq)
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

    form = f"""<form class="form" data-lead="Request from the English Dubai page" data-wa="{wa}" novalidate>
  <h3>Tell us about your wedding</h3>
  <p>We'll get back to you within one business day.</p>
  <div class="field"><label for="en-name">Your name</label><input id="en-name" name="name" data-label="Name" autocomplete="name" placeholder="Name"></div>
  <div class="field"><label for="en-phone">Phone or WhatsApp *</label>
    <input id="en-phone" name="phone" data-label="Phone" type="tel" autocomplete="tel" inputmode="tel" placeholder="+971 50 000 0000" required>
    <span class="err">Please enter your full phone number</span></div>
  <div class="field--row">
    <div class="field"><label for="en-date">Wedding date</label><input id="en-date" name="date" data-label="Date" placeholder="e.g. March 2027"></div>
    <div class="field"><label for="en-guests">Guests</label><input id="en-guests" name="guests" data-label="Guests" inputmode="numeric" placeholder="About 60"></div>
  </div>
  <input type="text" name="_gotcha" tabindex="-1" autocomplete="off" style="display:none">
  <button class="btn btn--gold btn--block" type="submit">Send request</button>
  <p class="form__legal">By sending this form you agree to our <a href="/policy/">privacy policy</a> (in Russian).</p>
</form>"""

    nav = [("#why", "Why us"), ("#weddings", "Weddings"), ("#price", "Prices"), ("#process", "How we work"), ("#faq", "FAQ")]
    nav_html = "".join(f'<a href="{h}">{l}</a>' for h, l in nav)
    body_top = f"""<body>
<a class="skip" href="#main">Skip to content</a>
<header class="header">
  <div class="wrap header__in">
    <a class="logo" href="/en/dubai/" aria-label="Vinogradova Event Dubai"><b>Vinogradova</b><span>Wedding &amp; Event</span></a>
    <nav class="nav" aria-label="Main menu">{nav_html}<a href="/dubai/" lang="ru" hreflang="ru">RU</a></nav>
    <div class="header__contact">
      <a class="header__phone" href="tel:{C['dubai_tel']}">{C['dubai_phone']}</a>
      <a class="btn btn--gold" href="#lead">Plan my wedding</a>
    </div>
    <button class="burger" aria-label="Menu" aria-expanded="false" aria-controls="mobile-menu"><span></span></button>
  </div>
</header>
<nav class="mobile-menu" id="mobile-menu" aria-label="Mobile menu">
  {nav_html}
  <a href="/dubai/" lang="ru" hreflang="ru">Русская версия</a>
  <a class="btn btn--gold" href="#lead">Plan my wedding</a>
  <a class="btn btn--ghost" href="tel:{C['dubai_tel']}">{icon('phone', 18)} {C['dubai_phone']}</a>
</nav>
<main id="main">"""

    body = f"""
<section class="hero">
  <div class="hero__bg">{site_img('dubai-hero', 'Wedding on Bluewaters Island, Dubai, by Vinogradova Event', eager=True)}</div>
  <div class="wrap hero__in">
    <span class="eyebrow">Wedding planner in Dubai &amp; the UAE</span>
    <h1>Your Dubai wedding, planned end-to-end by&nbsp;a&nbsp;team based here</h1>
    <p class="lead">An office in Dubai Marina, trusted venues and vendors. We take care of everything — from the hotel to the last dance — so all you have to do is arrive.</p>
    <div class="hero__actions">
      <a class="btn btn--gold" href="#lead">Plan my wedding</a>
      <a class="btn btn--wa" href="https://wa.me/{wa}" target="_blank" rel="noopener">{icon('wa', 18)} WhatsApp</a>
    </div>
    <div class="hero__award">{icon('award', 34)}<span>Winners of the White Wedding Industry Awards 2024 — Best Wedding in Dubai</span></div>
  </div>
</section>

<section class="section section--tight"><div class="wrap">
<div class="stats reveal">
  <div class="stat"><b>520+</b><span>weddings and events planned</span></div>
  <div class="stat"><b>11 years</b><span>in the wedding industry, since 2015</span></div>
  <div class="stat"><b>10–6,000</b><span>guests: from intimate dinners to grand celebrations</span></div>
  <div class="stat"><b>2 offices</b><span>in Dubai and Moscow</span></div>
</div>{press_strip().replace('О нас пишут', 'As featured in').replace('Лучшая свадьба в Дубае', 'Best Wedding in Dubai')}
</div></section>

<section class="section section--cream" id="why">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">Why us</span><h2>A destination wedding without the stress</h2></div>
      <p>Six reasons couples trust us with the most important day of their lives — and often become our friends.</p></div>
    <div class="cards">
      <div class="card reveal"><span class="card__num">01</span><h3>Our own team in Dubai</h3><p>Planners and coordinators on the ground visit venues, meet vendors and oversee every detail for you.</p></div>
      <div class="card reveal"><span class="card__num">02</span><h3>The best venues</h3><p>Kempinski The Palm, Bluewaters, Hyatt Regency, Anantara in Abu Dhabi, private villas — we'll find the place that fits your style and budget.</p></div>
      <div class="card reveal"><span class="card__num">03</span><h3>Award-winning</h3><p>One of our Dubai weddings won the White Wedding Industry Awards 2024 in the Best Wedding in Dubai category.</p></div>
      <div class="card reveal"><span class="card__num">04</span><h3>Easy from anywhere</h3><p>A shared project chat and online approvals keep you in the loop wherever you are.</p></div>
      <div class="card reveal"><span class="card__num">05</span><h3>Weddings and proposals</h3><p>Beyond weddings, we create romantic marriage proposals in Dubai's most beautiful locations.</p></div>
      <div class="card reveal"><span class="card__num">06</span><h3>Experience since 2015</h3><p>More than 520 weddings in Russia and the UAE, from intimate ceremonies to celebrations for hundreds of guests.</p></div>
    </div>
  </div>
</section>

<section class="section" id="weddings">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">Portfolio</span><h2>Our weddings in the UAE</h2></div>
      <p>Swipe through the photos on each card. Tap a card to open the full gallery.</p></div>
    <div class="grid-cases">{cards()}</div>
  </div>
</section>

<section class="section section--cream" id="price">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">Prices</span><h2>Wedding planning fees in&nbsp;Dubai</h2></div>
      <p>A fixed agency fee based on your total wedding budget. You know the exact amount before signing the contract.</p></div>
    <div class="pricing reveal">{price_cards}</div>
    <div class="price-extra reveal">
      <div class="price-box">
        <h3>What full planning includes</h3>
        <ul class="checks">
          <li>Venue search and booking</li>
          <li>Your team: photographer, videographer, host, DJ and performers</li>
          <li>Décor, florals and technical equipment</li>
          <li>Hair and make-up, the cake and every other detail</li>
          <li>Budget, timeline and run of show</li>
          <li>2 planners during preparation and at least 2 coordinators on the day</li>
        </ul>
      </div>
      <div class="price-box price-box--alt">
        <h3>Planning it yourselves?</h3>
        <p>Book a coordinator for the whole wedding day. They'll manage vendors and timing and handle any hiccups — so you can simply enjoy it.</p>
        <div class="price__fee">1,500 AED</div>
        <p class="price__note" style="color:rgba(243,235,225,.6)">day-of coordinator</p>
      </div>
    </div>
    <div class="actions"><a class="btn btn--gold" href="#lead">Get a quote</a></div>
  </div>
</section>

<section class="section section--dark" id="process">
  <div class="wrap">
    <div class="section-head"><div><span class="eyebrow">How we work</span><h2>Six steps to your Dubai wedding</h2></div></div>
    <ol class="steps" style="--n:6">{''.join(f'<li class="step reveal"><h3>{t}</h3><p>{d}</p></li>' for t, d in steps)}</ol>
  </div>
</section>

<section class="section" id="faq">
  <div class="wrap split" style="align-items:start">
    <div><span class="eyebrow">FAQ</span><h2>Questions couples ask</h2>
      <p class="lead" style="margin-top:18px">Didn't find your answer? Message us — we'll reply personally.</p></div>
    <div class="faq">{faq_html}</div>
  </div>
</section>

<section class="section section--dark" id="lead">
  <div class="wrap lead-block">
    <div>
      <span class="eyebrow">Dubai Marina office</span>
      <h2>Let's talk about your wedding</h2>
      <p class="lead" style="color:rgba(243,235,225,.8);margin-top:20px">Leave a request or message us on WhatsApp — we'll tell you about venues, dates and budgets. No obligation.</p>
      <ul class="contact-lines">
        <li>{icon('phone')}<div><a href="tel:{C['dubai_tel']}">{C['dubai_phone']}</a><small>9:00–21:00 Dubai time</small></div></li>
        <li>{icon('wa')}<div><a href="https://wa.me/{wa}" target="_blank" rel="noopener">Message us on WhatsApp</a></div></li>
        <li>{icon('mail')}<div><a href="mailto:{C['dubai_email']}">{C['dubai_email']}</a></div></li>
        <li>{icon('pin')}<div><a href="{C['dubai_map']}" target="_blank" rel="noopener">{C['dubai_address']}</a></div></li>
      </ul>
    </div>
    {form}
  </div>
</section>
"""
    foot = f"""</main>
<footer class="footer">
  <div class="wrap">
    <div class="footer__grid" style="grid-template-columns:1.4fr 1fr 1fr">
      <div>
        <a class="logo" href="/en/dubai/"><b>Vinogradova</b><span>Wedding &amp; Event</span></a>
        <p style="margin-top:20px;max-width:340px">Full-service wedding agency. Weddings in Dubai, Moscow and Europe since 2015.</p>
      </div>
      <div><h4>Dubai</h4><ul>
        <li><a href="tel:{C['dubai_tel']}">{C['dubai_phone']}</a></li>
        <li><a href="mailto:{C['dubai_email']}">{C['dubai_email']}</a></li>
        <li><a href="{C['dubai_map']}" target="_blank" rel="noopener">{C['dubai_address']}</a></li></ul></div>
      <div><h4>Language</h4><ul><li><a href="/dubai/" lang="ru" hreflang="ru">Русская версия</a></li><li><a href="/" lang="ru" hreflang="ru">Главная (RU)</a></li></ul></div>
    </div>
    <div class="footer__bottom"><span>© 2015–2026 Vinogradova Event</span><a href="/policy/">Privacy policy (RU)</a></div>
  </div>
</footer>
<a class="fab" href="https://wa.me/{wa}" target="_blank" rel="noopener">{icon('wa', 22)} WhatsApp</a>
<script src="/assets/js/main.js?v={VERSION}" defer></script>
</body>
</html>"""
    title = "Wedding Planner in Dubai — Vinogradova Event"
    desc = ("Full-service wedding planning and marriage proposals in Dubai and Abu Dhabi. Office in Dubai Marina, "
            "winners of the Best Wedding in Dubai award 2024. Fees from 8,500 AED.")
    hd = head(title, desc, path, "/assets/img/site/dubai-hero.webp")
    hd = hd.replace('<html lang="ru">', '<html lang="en">').replace('content="ru_RU"', 'content="en_US"')
    hd = hd.replace("</head>", DUBAI_HREFLANG + breadcrumbs_ld(path) + ld_script(
        service_ld("Wedding planning in Dubai", "Dubai", "AED",
                   [("Wedding budget up to 150,000 AED", 8500), ("Wedding budget 150,000–250,000 AED", 12500),
                    ("Wedding budget 250,000–400,000 AED", 18000), ("Day-of coordinator", 1500)], lang="en"), faq_ld) + "\n</head>")
    doc = hd + body_top + body + foot
    doc = re.sub(r'(<a href="mailto:[^"]+">)([^<@]+)@([^<]+)</a>', r"\1\2<wbr>@\3</a>", doc)
    doc = with_base(doc)
    dest = OUT / "en/dubai/index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc)
    SITEMAP.append(path)


# ---------------------------------------------------------------- main
SITEMAP = []
VERSION = "1"


def main():
    global VERSION
    import hashlib
    VERSION = hashlib.md5(((ROOT / "src/assets/css/style.css").read_bytes() + (ROOT / "src/assets/js/main.js").read_bytes())).hexdigest()[:8]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "src/assets", OUT / "assets")
    if (ROOT / "assets/img").exists():
        shutil.copytree(ROOT / "assets/img", OUT / "assets/img", dirs_exist_ok=True)
    for f in ("CNAME",):
        if (ROOT / f).exists():
            shutil.copy(ROOT / f, OUT / f)
    (OUT / ".nojekyll").write_text("")

    build_home()
    build_portfolio()
    build_cases()
    build_dubai()
    build_dubai_en()
    build_education()
    build_reviews()
    build_contacts()
    build_policy()
    build_404()

    urls = "".join(f"<url><loc>{DOMAIN}{p}</loc></url>" for p in SITEMAP)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    print(f"built {len(SITEMAP)} pages into {OUT}")

    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("serving on http://localhost:8000")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()


if __name__ == "__main__":
    main()
