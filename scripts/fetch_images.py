#!/usr/bin/env python3
"""Download the photos from the old Tilda site, resize them and save them as WebP.

Run (safe to re-run: files already on disk are skipped):
    python3 scripts/fetch_images.py

Writes:
    assets/img/cases/<slug>/raw/NNN.webp + NNN-sm.webp   gallery of each case
    assets/img/cases/<slug>/cover.webp + cover-sm.webp
    assets/img/site/<role>.webp                          photos used on the main pages
    data/images.json                                     index of saved photos (read by build.py)
"""
import concurrent.futures as cf
import io
import json
import pathlib
import time
import urllib.request

from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "data/image-manifest.json").read_text())
CASES = json.loads((ROOT / "data/cases.json").read_text())
OUT = ROOT / "assets/img"
MAX_GALLERY = 24
FULL, SMALL = 1600, 800
MIN_SIDE = 500  # smaller files are icons/logos, not photos
WORKERS = 3

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
NO_SMALL = ("press", "award", "insta")


def get(url, tries=8):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 site-migration"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(min(30, 3 * (i + 1)))


def save(img, path, width, keep_alpha=False):
    im = img.copy()
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    if not keep_alpha:
        im = im.convert("RGB")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".part.webp")
    im.save(tmp, "WEBP", quality=78, method=6)
    tmp.replace(path)


def job(url, dest, width=FULL, small=True, alpha=False, min_side=0):
    """Download url into dest (+ dest-sm). Returns 'ok', 'small' or an error string."""
    try:
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(get(url))))
    except Exception as e:
        return f"error {e}"
    if min_side and min(im.size) < min_side:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.with_suffix(".skip").write_text(url)  # remember: not a photo
        return "small"
    keep = alpha and im.mode in ("RGBA", "LA", "P")
    if small:
        save(im, dest.with_name(dest.stem + "-sm.webp"), SMALL)
    save(im, dest, width, keep_alpha=keep)
    return "ok"


def find(page, tail):
    return next((u for u in MANIFEST["pages"].get(page, []) if u.endswith("/" + tail)), None)


def plan():
    jobs = []
    for role, (page, tail) in SITE_ROLES.items():
        url = find(page, tail)
        if url:
            nosm = role.startswith(NO_SMALL)
            jobs.append((url, OUT / "site" / f"{role}.webp", dict(small=not nosm, alpha=nosm)))
    insta = [u for u in MANIFEST["pages"]["index"] if u.rsplit("/", 1)[-1] in INSTAGRAM]
    for i, u in enumerate(insta, 1):
        jobs.append((u, OUT / "site" / f"insta-{i:02d}.webp", dict(width=600, small=False)))
    for case in CASES:
        d = OUT / "cases" / case["slug"]
        jobs.append((case["cover_src"], d / "cover.webp", {}))
        urls = [u for u in MANIFEST["pages"].get(case["slug"], []) if u != case["cover_src"]]
        for k, u in enumerate(urls[: MAX_GALLERY + 6]):
            jobs.append((u, d / "raw" / f"{k:03d}.webp", dict(min_side=MIN_SIDE)))
    return jobs


def dims(p):
    with Image.open(p) as im:
        return {"w": im.width, "h": im.height}


def ahash(p):
    """Perceptual hash: 64-bit, close values mean visually identical photos."""
    with Image.open(p) as im:
        px = list(im.convert("L").resize((8, 8), Image.LANCZOS).getdata())
    avg = sum(px) / 64
    return sum(1 << i for i, v in enumerate(px) if v > avg)


def index():
    """Write data/images.json from what is on disk."""
    res = {"site": {}, "cases": {}, "instagram": []}
    for p in sorted((OUT / "site").glob("*.webp")):
        if p.stem.endswith("-sm") or ".part" in p.name:
            continue
        if p.stem.startswith("insta-"):
            res["instagram"].append(p.stem)
        else:
            res["site"][p.stem] = dims(p)
    for case in CASES:
        d = OUT / "cases" / case["slug"]
        info = {"gallery": []}
        if (d / "cover.webp").exists():
            info["cover"] = dims(d / "cover.webp")
        raws = sorted(p for p in (d / "raw").glob("*.webp")
                      if not p.stem.endswith("-sm") and ".part" not in p.name) if (d / "raw").exists() else []
        seen = []
        for p in raws:
            if len(info["gallery"]) >= MAX_GALLERY:
                break
            h = ahash(p)
            dist = [bin(h ^ x).count("1") for x in seen]
            # same shot uploaded twice anywhere, or a near-identical burst frame right next to it
            if any(d <= 6 for d in dist) or any(d <= 12 for d in dist[-2:]):
                continue
            seen.append(h)
            info["gallery"].append({"n": "raw/" + p.stem, **dims(p)})
        res["cases"][case["slug"]] = info
    (ROOT / "data/images.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    return res


def main():
    jobs = plan()
    todo = [j for j in jobs if not j[1].exists() and not j[1].with_suffix(".skip").exists()]
    print(f"{len(jobs)} files, {len(todo)} to download", flush=True)
    failed = 0
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(job, u, d, **kw): d for u, d, kw in todo}
        for i, f in enumerate(cf.as_completed(futs), 1):
            r = f.result()
            if r.startswith("error"):
                failed += 1
                print("!", futs[f].relative_to(ROOT), r, flush=True)
            if i % 25 == 0:
                print(f"progress {i}/{len(todo)} failed {failed}", flush=True)
                index()
    res = index()
    n = sum(len(c["gallery"]) for c in res["cases"].values())
    print(f"done: {n} gallery photos, {len(res['site'])} page photos, {failed} failed", flush=True)


if __name__ == "__main__":
    main()
