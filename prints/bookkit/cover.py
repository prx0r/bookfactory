#!/usr/bin/env python3
"""Build the KDP full-wrap paperback cover (back + spine + front + bleed).

Geometry follows KDP's published rules:
  Cover width  = bleed + back + spine + front + bleed
  Cover height = bleed + trim height + bleed
  Spine        = pages x per-page (white .002252in, cream .0025in)
Spine text is legal at >=79 pages; keep 1.6mm clear top/bottom of the spine.

Writes <book-dir>/cover.html and prints the geometry. Render it with:
  chrome --headless --print-to-pdf=cover.pdf http://127.0.0.1:8000/<book>/cover.html
"""
import json
import pathlib
import sys

TRIMS = {"A5": (148.0, 210.0), "6x9": (152.4, 228.6), "5.5x8.5": (139.7, 215.9)}
PER_PAGE_IN = {"white": 0.002252, "cream": 0.0025, "groundwood": 0.00235}
BLEED_MM = 3.175

BLURB = (
    "Thirty-six prayers for the moments of the day — eight moments and a "
    "clockless pocket for anytime. Each verse faces its explanation: when to "
    "say it, how, and how to know it is working. Nothing here needs belief; "
    "the verses were built to be said — at the sink, at the desk, in the "
    "queue, in the dark."
)


def mm(v):
    return round(v, 3)


def build(d):
    d = pathlib.Path(d)
    book = json.loads((d / "book.json").read_text(encoding="utf-8"))
    meta = book["meta"]
    trim = book.get("trim", "A5")
    paper = book.get("paper", "white")
    pages = book.get("target_pages")
    if pages is None:
        raise ValueError("book.json needs target_pages (interior page count for the spine)")
    tw, th = TRIMS[trim]
    spine = pages * PER_PAGE_IN[paper] * 25.4
    full_w = BLEED_MM + tw + spine + tw + BLEED_MM
    full_h = th + 2 * BLEED_MM
    art = meta.get("cover_image", {}).get("path", "")
    cover_rel = pathlib.Path(art).with_suffix(".png").as_posix() if art else ""
    back_cover = meta.get("back_cover") or BLURB
    safe = 6.0  # KDP: keep live content 6.4mm inside trim

    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{meta['title']} — cover</title>
<style>
@font-face{{font-family:'Tiro';src:url('fonts/TiroDevanagariSanskrit-Regular.ttf');}}
@font-face{{font-family:'Cormorant';src:url('fonts/CormorantGaramond[wght].ttf');font-weight:400 700;}}
@page{{size:{mm(full_w)}mm {mm(full_h)}mm;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{mm(full_w)}mm;height:{mm(full_h)}mm;background:#f6f1e6;color:#17140f;
  font-family:'Cormorant',Georgia,serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.wrap{{display:flex;width:100%;height:100%}}
.bleed{{width:{mm(BLEED_MM)}mm}}
.back,.front{{width:{mm(tw)}mm;height:100%;position:relative}}
.spine{{width:{mm(spine)}mm;height:100%;position:relative;background:#efe8d8;
  border-left:.2mm solid #ded5c2;border-right:.2mm solid #ded5c2}}
/* front */
.front{{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
  padding:{mm(safe)}mm}}
.front .om{{font-family:'Tiro';font-size:44pt;line-height:1;margin-bottom:14mm}}
.front h1{{font-size:38pt;font-weight:600;letter-spacing:.05em;text-transform:uppercase}}
.front .sub{{font-size:16pt;font-style:italic;color:#76736e;margin-top:4mm;max-width:110mm}}
.front .rule{{width:44mm;height:.3mm;background:#17140f;margin:9mm 0}}
.front img{{width:62mm;height:auto}}
/* spine */
.spine .t{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  writing-mode:vertical-rl;font-size:8pt;font-weight:600;letter-spacing:.18em;
  text-transform:uppercase;white-space:nowrap}}
/* back */
.back{{display:flex;flex-direction:column;padding:{mm(safe)}mm {mm(safe + 4)}mm}}
.back .head{{font-size:19pt;font-weight:600;letter-spacing:.03em}}
.back .sub{{font-size:10.5pt;font-style:italic;color:#76736e;margin-top:2mm;
  padding-bottom:5mm;border-bottom:.2mm solid #d9d5cc}}
.back p{{font-size:12pt;line-height:1.45;margin-top:6mm;max-width:112mm}}
.back .art{{margin:auto 0 0;width:34mm;opacity:.7}}
.back .barcode{{position:absolute;right:{mm(safe + 4)}mm;bottom:{mm(safe)}mm;
  width:50.8mm;height:30.5mm}}
</style></head><body><div class="wrap">
<div class="bleed"></div>
<div class="back">
  <div class="head">{meta['title']}</div>
  <div class="sub">{meta['subtitle']}</div>
  <p>{back_cover}</p>
  {f'<img class="art" src="{cover_rel}" alt="">' if cover_rel else ''}
  <div class="barcode"></div>
</div>
<div class="spine"><div class="t">{meta['title']}</div></div>
<div class="front">
  <div class="om">ॐ</div>
  <h1>{meta['title']}</h1>
  <div class="sub">{meta['subtitle']}</div>
  <div class="rule"></div>
  {f'<img src="{cover_rel}" alt="">' if cover_rel else ''}
</div>
<div class="bleed"></div>
</div></body></html>"""
    (d / "cover.html").write_text(html, encoding="utf-8")
    print(f"cover {d.name}: {trim} {paper} {pages}pp -> spine {spine:.2f}mm; "
          f"wrap {full_w:.2f} x {full_h:.2f} mm")


if __name__ == "__main__":
    build(sys.argv[1])
