#!/usr/bin/env python3
"""Build the KDP full-wrap paperback cover from the house cover style.

Geometry follows KDP's published rules:
  Cover width  = bleed + back + spine + front + bleed
  Cover height = bleed + trim height + bleed
  Spine        = pages x per-page (white .002252in, cream .0025in)
Spine text is legal at >=79 pages; keep 1.6mm clear top/bottom of the spine.

Everything visual comes from styles/cover-canonical.json, so the union is
reusable: a new book only needs book.json (trim/paper/target_pages/cover_image)
and an emblem image. The Svatantrya logo on the back is house-constant.

Writes <book-dir>/cover.html; render it with:
  chrome --headless --print-to-pdf=cover.pdf http://127.0.0.1:8000/<book>/cover.html
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def ensure_white(src: pathlib.Path) -> pathlib.Path:
    """Cache a white-ink / transparent-ground twin of the emblem for the black cover."""
    out = src.with_name(src.stem + "_white.png")
    if out.is_file() and out.stat().st_mtime >= src.stat().st_mtime:
        return out
    from PIL import Image
    im = Image.open(src).convert("L")
    rgba = Image.new("RGBA", im.size, (0, 0, 0, 0))
    px, dst = im.load(), rgba.load()
    for y in range(im.height):
        for x in range(im.width):
            dst[x, y] = (243, 237, 224, 255 - px[x, y])
    rgba.save(out)
    return out


def mm(v):
    return round(v, 3)


def build(d):
    d = pathlib.Path(d)
    book = json.loads((d / "book.json").read_text(encoding="utf-8"))
    meta = book["meta"]
    style = json.loads((ROOT / "styles" / "cover-canonical.json").read_text(encoding="utf-8"))
    geo, col, front, spine_cfg, back_cfg = (
        style["geometry"], style["colors"], style["front"], style["spine"], style["back"])

    trim = book.get("trim", "6x9")
    paper = book.get("paper", "cream")
    pages = book.get("target_pages")
    if pages is None:
        raise ValueError("book.json needs target_pages (interior page count for the spine)")
    tw, th = geo["trim_sizes_mm"][trim]
    bleed = geo["bleed_mm"]
    spine = pages * geo["spine_per_page_in"][paper] * 25.4
    full_w = bleed + tw + spine + tw + bleed
    full_h = th + 2 * bleed
    safe = geo["safe_mm"]
    if pages < geo["spine_text_min_pages"]:
        raise ValueError(f"spine text needs >= {geo['spine_text_min_pages']} pages, got {pages}")

    emblem_html = ""
    art = meta.get("cover_image", {}).get("path")
    if art:
        emblem = ensure_white((d / art).resolve())
        emblem_rel = emblem.relative_to(d.resolve()).as_posix()
        emblem_html = f'<img class="mark" src="{emblem_rel}" alt="">'

    logo = ROOT / "prints" / back_cfg["logo_asset"]
    logo_href = "../" + logo.relative_to(ROOT / "prints").as_posix()

    lay = front["layout_mm"]
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{meta['title']} — cover</title>
<style>
@font-face{{font-family:'Tiro';src:url('{style['fonts']['files']['tiro']}');}}
@font-face{{font-family:'Cormorant';src:url('{style['fonts']['files']['cormorant']}');font-weight:400 700;}}
@page{{size:{mm(full_w)}mm {mm(full_h)}mm;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{mm(full_w)}mm;height:{mm(full_h)}mm;background:{col['ground']};color:{col['ink']};
  font-family:'Cormorant',Georgia,serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.wrap{{display:flex;width:100%;height:100%}}
.bleed{{width:{mm(bleed)}mm}}
.back,.front{{width:{mm(tw)}mm;height:100%;position:relative}}
.spine{{width:{mm(spine)}mm;height:100%;position:relative;
  border-left:.2mm solid {col['spine_rule']};border-right:.2mm solid {col['spine_rule']}}}
/* front — fixed positions from the style pack */
.front .om{{position:absolute;left:0;right:0;top:{mm(lay['om_top'])}mm;text-align:center;
  font-family:'Tiro';font-size:{front['om_pt']}pt;line-height:1}}
.front h1{{position:absolute;left:0;right:0;top:{mm(lay['title_top'])}mm;text-align:center;
  font-size:{front['title_pt']}pt;font-weight:600;letter-spacing:{front['title_tracking']};text-transform:uppercase}}
.front .sub{{position:absolute;left:0;right:0;top:{mm(lay['subtitle_top'])}mm;text-align:center;
  font-size:{front['subtitle_pt']}pt;font-style:italic;color:{col['muted']};padding:0 16mm}}
.front .rule{{position:absolute;left:50%;top:{mm(lay['rule_top'])}mm;transform:translateX(-50%);
  width:{front['rule_mm']}mm;height:.25mm;background:{col['ink']}}}
.front .mark{{position:absolute;left:50%;top:{mm(lay['emblem_top'])}mm;transform:translateX(-50%);
  width:{front['emblem_mm']}mm;height:auto}}
/* spine */
.spine .t{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  writing-mode:vertical-rl;font-size:{spine_cfg['text_pt']}pt;font-weight:600;
  letter-spacing:{spine_cfg['tracking']};text-transform:uppercase;white-space:nowrap}}
/* back — house logo only, always centred */
.back{{display:flex;align-items:center;justify-content:center}}
.back img{{width:{back_cfg['logo_mm']}mm;height:auto;opacity:{back_cfg['logo_opacity']}}}
</style></head><body><div class="wrap">
<div class="bleed"></div>
<div class="back"><img src="{logo_href}" alt="Svatantrya"></div>
<div class="spine"><div class="t">{meta['title']}</div></div>
<div class="front">
  <div class="om">ॐ</div>
  <h1>{meta['title']}</h1>
  <div class="sub">{meta['subtitle']}</div>
  <div class="rule"></div>
  {emblem_html}
</div>
<div class="bleed"></div>
</div></body></html>"""
    (d / "cover.html").write_text(html, encoding="utf-8")
    print(f"cover {d.name}: {trim} {paper} {pages}pp -> spine {spine:.2f}mm; "
          f"wrap {full_w:.2f} x {full_h:.2f} mm; style={style['id']}")


if __name__ == "__main__":
    build(sys.argv[1])
