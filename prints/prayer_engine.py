#!/usr/bin/env python3
"""prayer_engine.py — POSTCARD vertical 4×6″ (1200×1800 px @ 300 DPI).

The layout reproduces the house "beautiful type" page:
  - white ground, everything centered
  - Devanagari is the hero: longest line fills ~70% of the width
  - English sits under it at ~53% of the Devanagari size
  - one short phrase per English line, no trailing punctuation
  - whole stack vertically centered, generous breath between stanzas

Tune the ratios below to change the look. Nothing is hard-coded to a size;
every card auto-fits its own longest lines at the SAME ratios, so any prayer
comes out with the same typographic voice.

Usage:
  python3 prints/prayer_engine.py prints/prayers/brahmarpanam.json
"""
import json, os, sys, argparse
from PIL import Image, ImageDraw, ImageFont
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ============================================================
#  HOUSE TYPE RATIOS  — the "beautiful" numbers, measured
#  Now fit to BOTH width and height: Devanagari is grown as large
#  as the page allows (fill the page), never overflowing.
# ============================================================
DEV_W_FRAC   = 0.90     # Devanagari hero line fills this share of width
DEV_MAX      = 320      # upper search bound (height is the real cap)
DEV_MIN      = 36
EN_RATIO     = 0.53     # English size = dev size * this  (3.2x smaller visually)
EN_W_FRAC    = 0.70     # hard cap: English line may not exceed this share
DEV_LEAD     = 1.62     # Devanagari line pitch = size * this
EN_LEAD      = 1.45     # English line pitch   = size * this
GAP_DEV_EN   = 0.060    # gap Dev block -> English block, share of height
STANZA_GAP   = 0.090    # gap between stanzas, share of height
MARGIN_TOP   = 0.060    # top safe margin, share of height
MARGIN_BOT   = 0.060    # bottom safe margin, share of height
LEAD_FILL_MAX = 1.55    # spread lines (leading) up to this to fill the page
# ============================================================

INK = (23, 20, 15)
TIO = "/root/.fonts/TiroDevanagariSanskrit-Regular.ttf"
COR = "/root/.fonts/CormorantGaramond[wght].ttf"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRAYERS = os.path.join(ROOT, "prints", "prayers")

W, H = 1200, 1800       # POSTCARD 4×6″ vertical @ 300 DPI


def has_dev(s):
    return any("\u0900" <= c <= "\u097f" for c in s)


def load_spec(path):
    spec = json.load(open(path, encoding="utf-8"))
    for st in spec["stanzas"]:
        if not any(has_dev(l) for l in st["dev"]):
            st["dev"] = [transliterate(l, sanscript.IAST, sanscript.DEVANAGARI)
                         for l in st["dev"]]
        st["dev"] = [l.strip() for l in st["dev"]]
        # English: lowercase phrase style, no trailing punctuation
        st["en"] = [l.strip().rstrip(". ,;") for l in st["en"] if l.strip()]
    return spec


def fnt(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def fit_size(font_path, lines, target_w, weight=None, lo=None, hi=None):
    """Largest integer size whose longest line fits target_w."""
    lo = lo or 10
    hi = hi or 400
    best = lo
    for s in range(lo, hi):
        f = fnt(font_path, s, weight)
        if max(f.getlength(l) for l in lines) <= target_w:
            best = s
        else:
            break
    return best


def block_height(f, lines, lead):
    if not lines:
        return 0
    asc, desc = f.getmetrics()
    return (len(lines) - 1) * lead + (asc + desc)


def layout(spec, en_lines_all, dev_size, k=1.0):
    """Return (en_size, fd, fe, dev_lh, en_lh, gap_de, gap_st, total).
    k scales the line leading (1.0 = house spacing)."""
    en_size = min(int(round(dev_size * EN_RATIO)),
                  fit_size(COR, en_lines_all, EN_W_FRAC * W, weight=500))
    en_size = max(12, en_size)
    fd = fnt(TIO, dev_size)
    fe = fnt(COR, en_size, 500)
    dev_lh = DEV_LEAD * dev_size * k
    en_lh = EN_LEAD * en_size * k
    gap_de = GAP_DEV_EN * H
    gap_st = STANZA_GAP * H
    total = 0
    n = len(spec["stanzas"])
    for i, st in enumerate(spec["stanzas"]):
        total += block_height(fd, st["dev"], dev_lh) + gap_de \
                 + block_height(fe, st["en"], en_lh)
        if i < n - 1:
            total += gap_st
    return en_size, fd, fe, dev_lh, en_lh, gap_de, gap_st, total


def render(spec):
    dev_lines_all = [l for st in spec["stanzas"] for l in st["dev"]]
    en_lines_all = [l for st in spec["stanzas"] for l in st["en"]]
    avail_h = H * (1 - MARGIN_TOP - MARGIN_BOT)

    # --- grow Devanagari as large as width AND height allow -----------
    dev_size = DEV_MIN
    en_size = None
    for s in range(DEV_MAX, DEV_MIN - 1, -1):
        fdt = fnt(TIO, s)
        if max(fdt.getlength(l) for l in dev_lines_all) > DEV_W_FRAC * W:
            continue
        r = layout(spec, en_lines_all, s)
        if r[7] <= avail_h:
            dev_size, en_size = s, r[0]
            break

    # --- spread lines to fill the page (leading only, size stays max) --
    t1 = layout(spec, en_lines_all, dev_size, k=1.0)[7]
    t2 = layout(spec, en_lines_all, dev_size, k=2.0)[7]
    A = t2 - t1
    B = t1 - A
    k = (avail_h - B) / A if A > 0 else 1.0
    k = max(1.0, min(LEAD_FILL_MAX, k))
    en_size, fd, fe, dev_lh, en_lh, gap_de, gap_st, total = \
        layout(spec, en_lines_all, dev_size, k=k)

    # --- measure per-stanza heights, then vertically center -----------
    stanzas = []
    for st in spec["stanzas"]:
        stanzas.append((st, block_height(fd, st["dev"], dev_lh),
                        block_height(fe, st["en"], en_lh)))

    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    cx = W / 2
    y = (H - total) / 2.0

    for i, (st, dh, eh) in enumerate(stanzas):
        dev_top = y
        for dl in st["dev"]:
            d.text((cx - fd.getlength(dl) / 2, y), dl, font=fd, fill=INK)
            y += dev_lh
        en_top = dev_top + dh + gap_de
        y = en_top
        for ln in st["en"]:
            d.text((cx - fe.getlength(ln) / 2, y), ln, font=fe, fill=INK)
            y += en_lh
        y = en_top + eh + (gap_st if i < len(stanzas) - 1 else 0)

    return img, dev_size, en_size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    args = ap.parse_args()
    spec = load_spec(args.spec)
    out_dir = os.path.join(ROOT, "outputs", "print_products", spec["id"])
    os.makedirs(out_dir, exist_ok=True)
    img, dev_size, en_size = render(spec)
    p = os.path.join(out_dir, f"{spec['id']}_postcard_{W}x{H}.png")
    img.save(p, optimize=True)
    print(f"{spec['id']:14} POSTCARD {W}×{H} dev={dev_size} en={en_size} -> {os.path.basename(p)}")


if __name__ == "__main__":
    main()
