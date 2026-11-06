#!/usr/bin/env python3
"""print_template.py — Etsy/Prodigi print canvases (the sizing template).

Generates the five master-ratio canvases at 300 DPI with guides:
trim border, 3mm bleed line, 1" safe margin, centre cross, label.
Design ONCE at the largest size; Prodigi scales down (see
references/prodigi/sizing.md).

Usage:
  python3 prints/print_template.py                      # all five -> outputs/print_templates/
  python3 prints/print_template.py --ratio 4:5 --out DIR
  python3 prints/print_template.py --print              # guides removed (clean canvas)
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont

DPI = 300
BLEED_IN = 3 / 25.4            # 3mm
SAFE_IN = 1.0                  # 1" safe margin (our type stays inside this)
# ratio -> (max inches) master; px = inches * 300
# ONLY POSTCARD (vertical) — 4×6″ = 101×152mm @ 300 DPI
RATIOS = {
    "POSTCARD": (4, 6, "POSTCARD — Prodigi CLASSIC-POST-GLOS-4X6 101x152mm (portrait, cheapest)"),
}
# per-ratio safe margin (inches) — small prints can't afford a full inch
SAFE_OVERRIDE = {"POSTCARD": 0.4}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "outputs", "print_templates")


def font(sz):
    for p in ("/root/.fonts/CormorantGaramond[wght].ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def make(ratio, clean=False):
    w_in, h_in, label = RATIOS[ratio]
    w, h = int(round(w_in * DPI)), int(round(h_in * DPI))
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    if clean:
        return img, label, w, h
    bleed = int(round(BLEED_IN * DPI))
    safe = int(round(SAFE_OVERRIDE.get(ratio, SAFE_IN) * DPI))
    guide_c = (0, 145, 180)      # cyan guides (guide layers — strip before print)
    trim_c = (220, 60, 60)
    # outer trim
    d.rectangle([0, 0, w - 1, h - 1], outline=trim_c, width=4)
    # bleed line
    d.rectangle([bleed, bleed, w - 1 - bleed, h - 1 - bleed],
                outline=(255, 150, 150), width=2)
    # safe margin
    d.rectangle([safe, safe, w - 1 - safe, h - 1 - safe],
                outline=guide_c, width=3)
    # centre cross
    cx, cy = w // 2, h // 2
    d.line([cx - safe // 3, cy, cx + safe // 3, cy], fill=guide_c, width=2)
    d.line([cx, cy - safe // 3, cx, cy + safe // 3], fill=guide_c, width=2)
    # labels (guide layer — remove before print)
    f = font(max(18, int(DPI * 0.11)))
    d.text((safe + 20, safe - int(DPI * 0.42)),
           f"{label}  ·  {w}×{h}px @300dpi  ·  bleed 3mm  ·  safe {round(safe/DPI, 2)}\"",
           font=f, fill=(90, 90, 90))
    return img, label, w, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratio", choices=list(RATIOS) + ["all"], default="all")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--print", dest="clean", action="store_true",
                    help="clean canvas, no guides")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    ratios = list(RATIOS) if args.ratio == "all" else [args.ratio]
    for r in ratios:
        img, label, w, h = make(r, clean=args.clean)
        suffix = "print" if args.clean else "template"
        path = os.path.join(args.out, f"{r.replace(':', 'x')}_{suffix}_{w}x{h}.png")
        img.save(path, optimize=True)
        print(f"{r:7} {w}×{h} -> {path}  ({os.path.getsize(path)//1024} KB)")


if __name__ == "__main__":
    main()
