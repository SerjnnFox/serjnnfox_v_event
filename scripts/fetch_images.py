#!/usr/bin/env python3
"""Download the photos from the old Tilda site, resize them and save them as WebP.

Run once (it skips files that already exist):
    python3 scripts/fetch_images.py

Writes:
    assets/img/cases/<slug>/NN.webp + NN-sm.webp    gallery of each case
    assets/img/cases/<slug>/cover.webp + cover-sm.webp
    assets/img/site/<role>.webp                     photos used on the main pages
    data/images.json                                what was saved (read by build.py)
"""
import io
import json
import pathlib
import sys
import urllib.request

from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "data/image-manifest.json").read_text())
CASES = json.loads((ROOT / "data/cases.json").read_text())
OUT = ROOT / "assets/img"
MAX_GALLERY = 24
FULL, SMALL = 1600, 800
MIN_SIDE = 500  # smaller files are icons/logos, not photos

# Photos used on the main pages, matched by the end of the original URL.
SITE_ROLES = {
    "hero": ("index", "IMG_6289-2.JPG"),
    "about": ("index", "02-2.jpg"),
    "founder": ("index", "IMG_6463-2.JPG"),
    "dubai-teaser": ("index", "WhatsApp_Image_2020-.jpeg"),
    "award": ("index", "__2024png.webp"),
    "press-1": ("index", "02.png"),
    "press-2": ("index", "03.png"),
    "press-3": ("index", "04.png"),
    "press-4": ("index", "05.png"),
    "press-5": ("index", "06.png"),
    "dubai-hero": ("dubai", "Photo-124.jpg"),
    "dubai-hero-2": ("dubai", "Photo-169_.jpg"),
    "edu-hero": ("education", "BAYD_0029_websize.jpg"),
    "edu-founder": ("education", "__by_roman_ivanov_we.jpg"),
    "edu-press": ("education", "2342.jpg"),
    "review-1": ("reviews", "dWPPsUCHA4o.jpg"),
    "review-2": ("reviews", "photo_2023-03-11_122.jpeg"),
}
INSTAGRAM = [f"{i:02d}.jpg" for i in range(1, 17)] + ["07.JPG"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 site-migration"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def save(img, path, width, keep_alpha=False):
    im = img.copy()
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    if not keep_alpha:
        im = im.convert("RGB")
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "WEBP", quality=78, method=6)
    return im.size


def load(url):
    data = get(url)
    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im)
    return im


def main():
    result = {"cases": {}, "site": {}, "instagram": []}
    prev = ROOT / "data/images.json"
    if prev.exists():
        result.update(json.loads(prev.read_text()))

    for role, (page, tail) in SITE_ROLES.items():
        dest = OUT / "site" / f"{role}.webp"
        if role in result["site"] and dest.exists():
            continue
        urls = [u for u in MANIFEST["pages"].get(page, []) if u.endswith("/" + tail)]
        if not urls:
            print("! no url for", role)
            continue
        try:
            im = load(urls[0])
            alpha = im.mode in ("RGBA", "LA", "P") and role.startswith(("press", "award"))
            w, h = save(im, dest, FULL, keep_alpha=alpha)
            if not role.startswith(("press", "award")):
                save(im, OUT / "site" / f"{role}-sm.webp", SMALL)
            result["site"][role] = {"w": w, "h": h}
            print("site", role, w, h)
        except Exception as e:  # keep going, report at the end
            print("! failed", role, e)

    if not result["instagram"]:
        for u in MANIFEST["pages"]["index"]:
            name = u.rsplit("/", 1)[-1]
            if name in INSTAGRAM and "/tild" in u:
                i = len(result["instagram"]) + 1
                try:
                    im = load(u)
                    save(im, OUT / "site" / f"insta-{i:02d}.webp", 600)
                    result["instagram"].append(f"insta-{i:02d}")
                except Exception as e:
                    print("! insta", e)

    for case in CASES:
        slug = case["slug"]
        if slug in result["cases"] and result["cases"][slug].get("gallery"):
            continue
        d = OUT / "cases" / slug
        info = {"gallery": []}
        try:
            im = load(case["cover_src"])
            info["cover"] = dict(zip("wh", save(im, d / "cover.webp", FULL)))
            save(im, d / "cover-sm.webp", SMALL)
        except Exception as e:
            print("! cover", slug, e)
        for u in MANIFEST["pages"].get(slug, []):
            if len(info["gallery"]) >= MAX_GALLERY:
                break
            if u == case["cover_src"]:
                continue
            try:
                im = load(u)
            except Exception as e:
                print("! img", slug, e)
                continue
            if min(im.size) < MIN_SIDE:
                continue
            n = len(info["gallery"]) + 1
            w, h = save(im, d / f"{n:02d}.webp", FULL)
            save(im, d / f"{n:02d}-sm.webp", SMALL)
            info["gallery"].append({"n": f"{n:02d}", "w": w, "h": h})
        result["cases"][slug] = info
        print("case", slug, len(info["gallery"]))
        prev.write_text(json.dumps(result, ensure_ascii=False, indent=1))

    prev.write_text(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sys.exit(main())
