#!/usr/bin/env python3
"""Fine-art postcards from book entries, styled by a swappable data pack.

Content is fixed (a verse entry); a style pack decides everything visual.
Adding a style = dropping a `styles/postcard-*.json`; the renderer never changes.

Usage:
  python3 prints/bookkit/postcard.py --book practical-prayers --all
  python3 prints/bookkit/postcard.py --book practical-prayers \
      --entries gita-424,somananda --styles postcard-paper,postcard-night
  python3 prints/bookkit/postcard.py --list-styles

Output per style: <book>/postcards/<style>/set.pdf (front/back pages),
front-NN.png / back-NN.png previews, and <book>/postcards/index.html.
"""
import argparse
import html
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def mm(v):
    return round(float(v), 3)


def hex_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def lum(hex_color):
    r, g, b = (c / 255 for c in hex_rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ensure_ink(src: pathlib.Path, color: str) -> pathlib.Path:
    """Cache an ink-coloured twin of the white logo for light grounds."""
    out = src.with_name(src.stem.replace("_white", "") + "_ink.png")
    if out.is_file() and out.stat().st_mtime >= src.stat().st_mtime:
        return out
    from PIL import Image
    im = Image.open(src).convert("RGBA")
    px = im.load()
    r, g, b = hex_rgb(color)
    for y in range(im.height):
        for x in range(im.width):
            a = px[x, y][3]
            px[x, y] = (r, g, b, a)
    im.save(out)
    return out


def devanagari(iast: str) -> str:
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        d = transliterate(iast, sanscript.IAST, sanscript.DEVANAGARI)
    except Exception:
        return ""
    d = d.replace("||", "॥").replace("|", "।").replace("ꣳ", "ं")
    return re.sub(r"\s+", " ", d).strip()


def br(text: str) -> str:
    return html.escape(text).replace(" / ", "<br>").replace("\n", "<br>")


def serif(v):
    return f"{mm(v)}mm"


def block_html(b, entry):
    kind = b["kind"]
    if kind == "spacer":
        return f'<div style="height:{serif(b.get("mm", 4))}"></div>'
    if kind == "rule":
        w = b.get("width_mm", 16)
        th = b.get("thickness_mm", 0.3)
        col = b.get("color", "accent")
        after = b.get("space_after_mm", 0)
        return (f'<div style="width:{serif(w)};height:{serif(th)};background:var(--{col});'
                f'border-radius:1px;margin-bottom:{serif(after)}"></div>')
    glyph = b.get("glyph", "")
    if kind == "sanskrit":
        text = devanagari(entry.get("iast", "")) if glyph == "" else glyph
    elif kind == "iast":
        text = entry.get("iast", "")
    elif kind == "english":
        text = entry.get("en", "")
    elif kind == "title":
        text = entry.get("title", "")
    elif kind == "source":
        text = entry.get("source", "")
    elif kind == "ornament":
        text = glyph
    else:
        text = ""
    if not text:
        return ""
    if kind in ("english", "iast"):
        inner = br(text)
    else:
        inner = html.escape(text)
    fam = "var(--display)" if kind in ("sanskrit", "ornament") else "var(--text)"
    size = b.get("size_pt", 10)
    lh = b.get("line_height", 1.4)
    col = b.get("color", "ink")
    style = [f"font-family:{fam}", f"font-size:{size}pt", f"line-height:{lh}",
             f"color:var(--{col})", f"margin-bottom:{serif(b.get('space_after_mm', 0))}"]
    if b.get("italic"):
        style.append("font-style:italic")
    if b.get("uppercase"):
        style.append("text-transform:uppercase")
    if b.get("weight"):
        style.append(f"font-weight:{b['weight']}")
    if b.get("tracking"):
        style.append(f"letter-spacing:{b['tracking']}")
    if kind == "english":
        style.append("max-width:78%")
    return f'<div style="{";".join(style)}">{inner}</div>'


def card_html(entry, style, book, rel_fonts, logo_rel, series):
    geo, col, front = style["geometry"], style["colors"], style["front"]
    trim_w, trim_h = geo["trim_mm"]
    bleed = geo["bleed_mm"]
    full_w, full_h = trim_w + 2 * bleed, trim_h + 2 * bleed
    frame = front.get("frame") or None
    inner_style = [
        f"position:absolute;left:{serif(bleed)};top:{serif(bleed)}",
        f"width:{serif(trim_w)};height:{serif(trim_h)}",
        f"padding:{' '.join(serif(x) for x in front['padding_mm'])}",
        f"display:flex;flex-direction:column;gap:{serif(front['gap_mm'])}",
        f"align-items:{front['align']};justify-content:{front['justify']}",
        f"text-align:{'center' if front['align']=='center' else 'left'}",
    ]
    if frame:
        inner_style.append(
            f"border:{serif(frame['width_mm'])} solid var(--{frame['color']});"
            f"outline:0;box-shadow:inset 0 0 0 {serif(frame['inset_mm'])} transparent")

    front_blocks = "\n".join(block_html(b, entry) for b in front["blocks"])

    back = style["back"]
    cap = back["caption"]
    dx = back["divider_x_pct"]
    series_line = html.escape(series)
    addr = "".join('<div class="addr-line"></div>' for _ in range(back["address_lines"]))
    stamp = ('<div class="stamp"></div>' if back["stamp_box"] else "")
    back_pad = " ".join(serif(x) for x in back["padding_mm"])

    return f"""<section class="card front">
  <div class="inner" style="{';'.join(inner_style)}">
    {front_blocks}
  </div>
</section>
<section class="card back">
  <div class="back-pad" style="padding:{back_pad}">
    <div class="back-left">
      <div class="wm">{html.escape(back['wordmark'])}</div>
      <div class="bt">{html.escape(entry.get('title',''))}</div>
      <div class="bsrc">{html.escape(entry.get('source',''))}</div>
      <div class="bbrief">{br(entry.get('brief',''))}</div>
      <div class="bseries">{series_line}</div>
    </div>
    <div class="divider" style="left:{dx}%"></div>
    <div class="back-right" style="left:{dx}%">
      <img class="logo" src="{logo_rel}" alt="Svatantrya">
      {stamp}
      <div class="addr">{addr}</div>
    </div>
  </div>
</section>"""


def build_html(entries, style, book, book_dir, out_dir, series):
    geo, col, fonts = style["geometry"], style["colors"], style["fonts"]
    full_w = geo["trim_mm"][0] + 2 * geo["bleed_mm"]
    full_h = geo["trim_mm"][1] + 2 * geo["bleed_mm"]
    display = (book_dir / "fonts" / fonts["display_file"]).resolve()
    text = (book_dir / "fonts" / fonts["text_file"]).resolve()
    f_disp = os.path.relpath(display, out_dir.resolve()).replace(os.sep, "/")
    f_text = os.path.relpath(text, out_dir.resolve()).replace(os.sep, "/")

    logo = ROOT / "prints" / "bookkit" / "assets" / "svatantra_white.png"
    mode = style["back"]["logo_mode"]
    if mode == "auto":
        mode = "ink" if lum(col["ground"]) > 0.5 else "white"
    logo_use = ensure_ink(logo, col["ink"]) if mode == "ink" else logo
    logo_rel = os.path.relpath(logo_use.resolve(), out_dir.resolve()).replace(os.sep, "/")

    cards = "\n".join(card_html(e, style, None, None, logo_rel, series) for e in entries)
    back = style["back"]
    cap = back["caption"]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{html.escape(series)} — {html.escape(style['name'])}</title>
<style>
@font-face{{font-family:'Tiro';src:url('{f_disp}');}}
@font-face{{font-family:'Cormorant';src:url('{f_text}');font-weight:400 700;}}
@page{{size:{mm(full_w)}mm {mm(full_h)}mm;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{mm(full_w)}mm;background:{col['ground']};color:{col['ink']}}}
:root{{--ground:{col['ground']};--ink:{col['ink']};--muted:{col['muted']};--accent:{col['accent']};
  --display:'Tiro';--text:'Cormorant'}}
.card{{position:relative;width:{mm(full_w)}mm;height:{mm(full_h)}mm;overflow:hidden;
  background:var(--ground);color:var(--ink);page-break-after:always;break-after:page}}
.card:last-child{{page-break-after:auto;break-after:auto}}
.back-pad{{position:absolute;left:0;top:0;width:100%;height:100%}}
.back-left{{position:absolute;inset:0 {100-back['divider_x_pct']}% 0 0;display:flex;flex-direction:column}}
.divider{{position:absolute;top:4%;bottom:4%;width:0.2mm;background:var(--muted);opacity:.45}}
.back-right{{position:absolute;top:0;bottom:0;right:0;display:flex;flex-direction:column;
  align-items:flex-start;justify-content:flex-end;padding:8mm 6mm}}
.wm{{font-family:var(--text);font-size:6pt;letter-spacing:.22em;color:var(--muted);
  text-transform:uppercase;margin-bottom:4mm}}
.bt{{font-family:var(--text);font-size:{mm(cap['title_pt'])}pt;font-weight:600;line-height:1.15;
  margin-bottom:1.5mm}}
.bsrc{{font-family:var(--text);font-size:{mm(cap['source_pt'])}pt;color:var(--muted);
  text-transform:uppercase;letter-spacing:.08em;margin-bottom:3mm}}
.bbrief{{font-family:var(--text);font-size:{mm(cap['brief_pt'])}pt;line-height:1.4;color:var(--ink)}}
.bseries{{margin-top:auto;font-family:var(--text);font-size:{mm(cap['series_pt'])}pt;
  color:var(--muted);text-transform:uppercase;letter-spacing:.14em}}
.logo{{width:{mm(back['logo_mm'])}mm;height:auto;opacity:.9;margin-bottom:auto}}
.stamp{{position:absolute;top:8mm;right:6mm;width:12mm;height:15mm;
  border:.25mm solid var(--muted);opacity:.5}}
.addr{{width:100%;display:flex;flex-direction:column;gap:6mm;margin-top:6mm}}
.addr-line{{height:.2mm;background:var(--muted);opacity:.5}}
</style></head><body>
{cards}
</body></html>"""


def render(pdf_html: pathlib.Path, pdf: pathlib.Path):
    cmd = ["google-chrome-stable", "--headless=new", "--disable-gpu", "--no-sandbox",
           "--no-pdf-header-footer", "--virtual-time-budget=15000",
           f"--print-to-pdf={pdf}", pdf_html.resolve().as_uri()]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def previews(pdf: pathlib.Path, out_dir: pathlib.Path, dpi=150):
    import fitz
    doc = fitz.open(pdf)
    names = []
    for i, page in enumerate(doc):
        side = "front" if i % 2 == 0 else "back"
        n = i // 2 + 1
        name = f"{side}-{n:02d}.png"
        page.get_pixmap(dpi=dpi).save(out_dir / name)
        names.append(name)
    return names


def gallery(styles_done, out_root: pathlib.Path, book_title, count):
    cards = []
    for st in styles_done:
        thumbs = "".join(
            f'<a href="{st["id"]}/front-{i:02d}.png"><img src="{st["id"]}/front-{i:02d}.png" alt=""></a>'
            for i in range(1, count + 1))
        cards.append(f"""<section><h2>{html.escape(st['name'])}</h2>
<p class="d">{html.escape(st.get('description',''))}</p>
<div class="grid">{thumbs}</div>
<p><a href="{st['id']}/set.pdf">set.pdf</a></p></section>""")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{html.escape(book_title)} — postcards</title>
<style>
body{{margin:0;padding:32px;background:#fff;color:#17140f;font:16px/1.4 Georgia,serif}}
h1{{font-weight:600;margin:0 0 4px}} h2{{margin:32px 0 2px;font-weight:600}}
.d{{color:#6f6b63;margin:0 0 12px}} .grid{{display:flex;gap:12px;flex-wrap:wrap}}
.grid img{{width:216px;height:auto;box-shadow:0 1px 6px rgba(0,0,0,.18)}}
a{{color:#9a3b2e}}
</style></head><body><h1>{html.escape(book_title)} — postcards</h1>
<p class="d">Same content, {len(styles_done)} style packs. 4×6 in + 3 mm bleed.</p>
{''.join(cards)}</body></html>"""
    (out_root / "index.html").write_text(page, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book")
    ap.add_argument("--entries", help="comma-separated entry ids")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--styles", help="comma-separated style ids (default: all postcard-*)")
    ap.add_argument("--out")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--list-styles", action="store_true")
    a = ap.parse_args()

    styles = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "styles").glob("postcard-*.json"))]
    if a.list_styles:
        for s in styles:
            print(f"{s['id']:22} {s['name']:14} {s.get('description','')}")
        return
    if not a.book:
        ap.error("--book is required (or use --list-styles)")

    book_dir = (ROOT / "prints" / a.book).resolve()
    book = json.loads((book_dir / "book.json").read_text(encoding="utf-8"))
    entries = json.loads((book_dir / "entries.json").read_text(encoding="utf-8"))
    lookup = {e["id"]: e for e in entries}
    if a.entries:
        wanted = [x.strip() for x in a.entries.split(",") if x.strip()]
        missing = [x for x in wanted if x not in lookup]
        if missing:
            sys.exit(f"unknown entries: {missing}")
        chosen = [lookup[x] for x in wanted]
    elif a.all:
        chosen = entries
    else:
        chosen = entries[: (a.limit or 4)]
    if a.limit:
        chosen = chosen[:a.limit]

    if a.styles:
        wanted = [x.strip() for x in a.styles.split(",") if x.strip()]
        styles = [s for s in styles if s["id"] in wanted]
        if not styles:
            sys.exit(f"no style matched {wanted}")

    out_root = pathlib.Path(a.out).resolve() if a.out else book_dir / "postcards"
    out_root.mkdir(parents=True, exist_ok=True)
    title = book.get("meta", {}).get("title", a.book)
    series = f"{title} · postcard"

    done = []
    for st in styles:
        out = out_root / st["id"]
        out.mkdir(parents=True, exist_ok=True)
        page_html = build_html(chosen, st, book, book_dir, out, series)
        (out / "set.html").write_text(page_html, encoding="utf-8")
        if not a.no_render:
            render(out / "set.html", out / "set.pdf")
            previews(out / "set.pdf", out, st.get("render", {}).get("preview_dpi", 150))
        done.append(st)
        print(f"postcards {a.book}: {len(chosen)} cards · {st['id']} -> {out}")

    if not a.no_render:
        gallery(done, out_root, title, len(chosen))
        print(f"gallery http://127.0.0.1:8000/{a.book}/postcards/")


if __name__ == "__main__":
    main()
