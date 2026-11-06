#!/usr/bin/env python3
"""render_brahmarpanam.py — Etsy print: Brahmarpanam prayer (Gītā 4.24).

Layout v4 (owner): two paired stanzas, REDUCED middle gap, whole-canvas
vertical presence, English all lowercase, last line "all activity is śiva".
Renders the five ratios + the Prodigi Classic postcard (cheapest, £0.40).
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from print_template import RATIOS, SAFE_IN, SAFE_OVERRIDE, DPI
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# --- sources ----------------------------------------------------------------
IAST = ("brahmārpaṇaṁ brahma havir brahmāgnau brahmaṇā hutam / "
        "brahmaiva tena gantavyaṁ brahmakarmasamādhinā //")
DEV = transliterate(IAST, sanscript.IAST, sanscript.DEVANAGARI)
DEV_LINES = [l.strip() for l in DEV.replace("//", "।।").split("/") if l.strip()]
EN_LINES = [
    "whatever i take is offered to śiva;",
    "what i offer is itself śiva;",
    "in the fire that is śiva,",
    "offered by śiva,",
    "śiva alone, by himself, attains the goal,",
    "all activity is śiva",
]
PAIRS = [(DEV_LINES[0], EN_LINES[0:4]), (DEV_LINES[1], EN_LINES[4:6])]
INK = (23, 20, 15)
TIO = "/root/.fonts/TiroDevanagariSanskrit-Regular.ttf"
COR = "/root/.fonts/CormorantGaramond[wght].ttf"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "outputs", "print_products", "brahmarpanam")

# layout constants (v4: tight middle, roomy line rhythm)
DEV_LH, EN_LH = 1.72, 1.60
INTRA = 0.90          # dev block → its english, × dev size
EN_GAP = 0.30         # between english lines, × en size
PAIR_BASE = 1.90      # between stanzas, × dev size
# small canvases compress the gaps so the type stays readable
GAP_SCALE = {"POSTCARD": 0.55}

def safe_of(ratio):
    return int(round(SAFE_OVERRIDE.get(ratio, SAFE_IN) * DPI))

def fnt(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f

def width_ok(lines, f, max_w):
    return max(f.getlength(l) for l in lines) <= max_w

def natural_h(sd, se, g=1.0):
    h = 0.0
    for i, (d, els) in enumerate(PAIRS):
        h += DEV_LH * sd + INTRA * g * sd + EN_LH * se * len(els) \
             + EN_GAP * g * se * (len(els) - 1)
        if i < len(PAIRS) - 1:
            h += PAIR_BASE * g * sd
    return h

def pick_sizes(max_w, max_h, dev_sizes, en_sizes, g=1.0):
    for sd in dev_sizes:
        fd = fnt(TIO, sd)
        if not width_ok(DEV_LINES, fd, max_w):
            continue
        for se in en_sizes:
            fe = fnt(COR, se, 500)
            if not width_ok([l for _, els in PAIRS for l in els], fe, max_w):
                continue
            if natural_h(sd, se, g) <= max_h:
                return fd, sd, fe, se, natural_h(sd, se, g)
    return None

def render(ratio):
    w_in, h_in, _ = RATIOS[ratio]
    W, H = int(round(w_in * DPI)), int(round(h_in * DPI))
    SAFE = safe_of(ratio)
    g = GAP_SCALE.get(ratio, 1.0)
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    max_w = W - 2 * SAFE
    max_h = H - 2 * SAFE
    dev_sizes = list(range(int(W * 0.085), 34, -3))
    en_sizes = list(range(int(W * 0.045), 14, -2))
    picked = pick_sizes(max_w, max_h, dev_sizes, en_sizes, g)
    if not picked:
        raise SystemExit(f"{ratio}: no size fits")
    fd, sd, fe, se, natural = picked

    leftover = max_h - natural
    pair_gap = PAIR_BASE * g * sd + leftover * 0.35
    top = SAFE + leftover * 0.30
    y = top
    x0 = W / 2
    for i, (dev_line, ens) in enumerate(PAIRS):
        d.text((x0 - fd.getlength(dev_line) / 2, y), dev_line, font=fd, fill=INK)
        y += DEV_LH * sd + INTRA * g * sd
        lh_e = EN_LH * se
        for j, ln in enumerate(ens):
            d.text((x0 - fe.getlength(ln) / 2, y), ln, font=fe, fill=INK)
            y += lh_e + (EN_GAP * g * se if j < len(ens) - 1 else 0)
        if i < len(PAIRS) - 1:
            y += pair_gap
    return img, W, H, sd, se, natural, pair_gap

def main():
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for r in RATIOS:
        if only and r != only:
            continue
        img, W, H, sd, se, nat, gap = render(r)
        tag = "postcard" if r == "POSTCARD" else r.replace(":", "x")
        p = os.path.join(OUT, f"brahmarpanam_{tag}_{W}x{H}.png")
        img.save(p, optimize=True)
        print(f"{r:9} {W}×{H}  dev={sd}px en={se}px natural={nat:.0f} "
              f"pairgap={gap:.0f} -> {os.path.basename(p)}")

if __name__ == "__main__":
    main()
