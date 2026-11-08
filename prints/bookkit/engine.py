#!/usr/bin/env python3
"""bookkit engine — shared builder for all prayer books.

A book = a directory with:
  book.json    { meta:{title,subtitle,blurb,epi_iast,epi_en,epi_src},
                 sections:[{id,numeral,title,sub,doctrine?}],
                 glyph: "rasa" | "activity" | null }
  entries.json [ {id, section, title, source, source_ref, source_path,
                  brief, logic, howto, en(\n-lineated),
                  iast+devanagari | corpus:[ch,verse]} ... ]
  front.html   raw <section> blocks rendered AFTER the epigraph, BEFORE contents
  back.html    raw <section> blocks rendered AFTER the spreads, BEFORE sources
  sources/     linked source files (copy them in; guides link relatively)
  fonts/       Tiro + Cormorant (OFL)

Usage:  python3 bookkit/engine.py <book-dir>
Corpus refs resolve against <book-dir>/sources/shivastotravali_corpus.json.
Preflight gate: ../kdp_preflight.py <pdf>   (A5 custom trim, >=7pt, fonts embedded)
"""
import json, html, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from stencils import rasa_rosette, activity_glyph

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as _tr
except Exception:
    _tr = None

CSS = """
@font-face{font-family:'Tiro';src:url('fonts/TiroDevanagariSanskrit-Regular.ttf');}
@font-face{font-family:'Cormorant';src:url('fonts/CormorantGaramond[wght].ttf');font-weight:400 700;}
:root{--ink:#17140f;--grey:#76736e;--hair:#d9d5cc;}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#efece5;color:var(--ink);}
body{font-family:'Cormorant',Georgia,serif;font-size:15pt;line-height:1.5;}
.page{background:#fff;width:148mm;min-height:210mm;margin:0 auto 10mm;padding:12mm 18mm;
  box-shadow:0 2px 14px rgba(0,0,0,.12);position:relative;page-break-after:always;overflow-wrap:anywhere;}
.spread{display:flex;gap:8mm;justify-content:center;flex-wrap:wrap;margin:0 auto 10mm;}
.spread .page{margin:0;}
.cover{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;}
.cover .om{font-family:'Tiro';font-size:60pt;line-height:1;margin-bottom:16mm;}
.cover h1{font-family:'Cormorant';font-weight:600;font-size:36pt;letter-spacing:.05em;margin:0;text-transform:uppercase;}
.cover .sub{font-size:16pt;font-style:italic;color:var(--grey);margin-top:4mm;}
.cover .rule{width:40mm;height:1px;background:var(--ink);margin:10mm auto;}
.cover .blurb{font-size:11pt;text-transform:uppercase;letter-spacing:.14em;color:var(--grey);}
.cover .cover-mark{display:block;width:52mm;max-width:62%;height:auto;margin:9mm auto 0;}
.epi{display:flex;flex-direction:column;justify-content:center;}
.epi.center{align-items:center;text-align:center;}
.epi .lines{font-size:14pt;line-height:1.7;}
.epi .src{font-size:9.5pt;letter-spacing:.15em;text-transform:uppercase;color:var(--grey);margin-top:8mm;}
h2.blk{font-family:'Cormorant';font-weight:600;font-size:15pt;letter-spacing:.08em;text-transform:uppercase;margin:4mm 0 2mm;color:var(--ink);}
.epi h2.blk+p,.epi p{font-size:11pt;line-height:1.36;margin:0 0 2mm;}
.epi .sr{display:block;font-size:9.5pt;color:#76736e;line-height:1.38;margin-top:.6mm;}
.opening-image{display:flex;align-items:center;justify-content:center;}
.opening-image img{display:block;max-width:100%;max-height:165mm;object-fit:contain;}
.opening-image .draft-mark{position:absolute;top:8mm;right:10mm;font:8pt sans-serif;color:#a22;}
.epi table{border-collapse:collapse;font-size:10pt;width:100%;}
.epi th{text-align:left;font-size:9pt;line-height:1.25;letter-spacing:.1em;text-transform:uppercase;color:var(--grey);border-bottom:1px solid var(--ink);padding:2mm 2mm 2mm 0;font-weight:400;}
.epi td{line-height:1.25;padding:.45mm 2mm .45mm 0;border-bottom:1px solid var(--hair);}
.epi td.s{font-style:italic;color:var(--grey);}
.bib ul{list-style:none;padding:0;margin:4mm 0 0;}
.bib li{margin:0 0 .5mm;font-size:8.5pt;line-height:1.18;}
.bib li a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--hair);word-break:break-all;}
.toc h2,.sec-div h2,.bib h2{font-family:'Cormorant';font-weight:600;letter-spacing:.12em;text-transform:uppercase;font-size:12pt;color:var(--grey);margin:0 0 2mm;}
.toc h2{text-align:center;font-size:13pt;letter-spacing:.22em;color:var(--ink);margin:0 0 3mm;}
.toc .head-rule{width:22mm;height:1px;background:var(--ink);margin:0 auto 9mm;}
.toc ol{list-style:none;padding:0;margin:0;column-count:2;column-gap:11mm;}
.toc li,.toc .sec{break-inside:avoid;-webkit-column-break-inside:avoid;}
.toc .sec{margin:5.5mm 0 1.8mm;font-family:'Cormorant';font-size:10pt;font-weight:600;
  letter-spacing:.2em;text-transform:uppercase;color:var(--ink);line-height:1.2;}
.toc .sec:first-child{margin-top:0;}
.toc .sec .num{display:inline-block;width:9mm;font-weight:400;color:var(--grey);letter-spacing:0;margin-right:1.6mm;}
.toc li{margin:0 0 .9mm;padding-left:5mm;text-indent:-5mm;font-size:10.5pt;line-height:1.3;color:#241f19;}
.notes{display:flex;flex-direction:column;}
.notes h2{font-family:'Cormorant';font-weight:600;letter-spacing:.22em;text-transform:uppercase;font-size:11pt;color:var(--grey);margin:0 0 8mm;text-align:center;}
.notes .ruled{flex:1;background:repeating-linear-gradient(to bottom,transparent 0 8.4mm,var(--hair) 8.4mm 8.5mm);}
.half{display:flex;align-items:center;justify-content:center;}
.half .t{font-family:'Cormorant';font-size:16pt;letter-spacing:.3em;text-transform:uppercase;color:var(--ink);}
.orn{display:flex;align-items:center;justify-content:center;}
.orn img{width:14mm;max-width:30%;height:auto;opacity:.45;}
.titlepage{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;}
.titlepage .om{font-family:'Tiro';font-size:40pt;line-height:1;margin-bottom:12mm;}
.titlepage h1{font-family:'Cormorant';font-weight:600;font-size:30pt;letter-spacing:.05em;margin:0;text-transform:uppercase;}
.titlepage .sub{font-size:14pt;font-style:italic;color:var(--grey);margin-top:4mm;}
.titlepage .rule{width:34mm;height:1px;background:var(--ink);margin:10mm auto;}
.titlepage img{width:44mm;max-width:60%;height:auto;}
.copy{display:flex;flex-direction:column;justify-content:flex-end;font-size:9.5pt;line-height:1.5;color:var(--grey);}
.copy b{color:var(--ink);font-weight:600;}
.copy .qr{margin-top:8mm;border:1px dashed var(--hair);padding:5mm;text-align:center;font-size:8.5pt;letter-spacing:.08em;text-transform:uppercase;color:var(--grey);}
.sec-div{display:flex;flex-direction:column;justify-content:center;text-align:center;}
.sec-div .glyph{line-height:0;margin-bottom:5mm;}
.sec-div .num{font-family:'Cormorant';font-size:11pt;letter-spacing:.3em;color:var(--grey);}
.sec-div h2{font-size:26pt;letter-spacing:.06em;margin:4mm 0 0;color:var(--ink);text-transform:none;font-weight:600;}
.sec-div .sub{font-style:italic;color:var(--grey);font-size:13pt;margin-top:3mm;}
.sec-div .gloss{font-size:10pt;color:var(--grey);margin-top:2.5mm;letter-spacing:.01em;}
.sec-div .rule{width:30mm;height:1px;background:var(--ink);margin:7mm auto 0;}
.sec-div .doc{font-size:11pt;line-height:1.5;color:#241f19;max-width:108mm;margin:7mm auto 0;font-style:italic;}
.src{font-size:9.5pt;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);}
.prayer h3,.guide h3{font-family:'Cormorant';font-weight:600;font-size:15pt;margin:1mm 0 2mm;text-align:center;}
.prayer .dev{font-family:'Tiro';text-align:center;white-space:pre-line;margin:3mm 0 0;}
.prayer .iast{font-style:italic;color:var(--grey);text-align:center;font-size:11pt;line-height:1.35;margin-top:1.5mm;}
.prayer .en{margin:4mm 0 0;text-align:center;line-height:1.3;color:#241f19;}
.prayer .en .ln{display:block;}
.guide .label{font-size:9pt;letter-spacing:.24em;text-transform:uppercase;color:var(--grey);margin-bottom:3mm;}
.guide h3{text-align:left;font-size:19pt;margin:0 0 3mm;}
.guide .src{text-align:left;margin-bottom:4mm;}
.guide .brief{font-style:italic;color:var(--grey);font-size:11.5pt;line-height:1.4;padding-bottom:2mm;margin-bottom:3mm;border-bottom:1px solid var(--hair);}
.guide .blk{margin-bottom:1.5mm;}
.guide .bl{font-size:8.5pt;letter-spacing:.2em;text-transform:uppercase;color:var(--grey);display:block;margin-bottom:1mm;}
.guide .body{font-size:11pt;line-height:1.3;color:#241f19;}
.guide .body p{margin:0;}
.guide .foot{margin-top:auto;border-top:1px solid var(--hair);padding-top:1.5mm;font-size:8.5pt;color:var(--grey);}
.guide .foot a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--hair);}
.pnum{position:absolute;bottom:10mm;left:0;right:0;text-align:center;font-size:9pt;color:var(--grey);letter-spacing:.1em;}
@media print{html,body{background:#fff}.page{margin:0;box-shadow:none;width:auto;min-height:auto}.spread{display:block;margin:0}@page{size:TRIM;margin:0}}
"""

# Trim sizes KDP prints (mm). "6x9" is the standard global default; A5 is kept
# for the older renders. The interior trim is book-wide, never per page.
TRIMS = {"A5": (148.0, 210.0), "6x9": (152.4, 228.6), "5.5x8.5": (139.7, 215.9)}


def css_for(trim, layout=None):
    """Trim CSS + optional per-book layout.json overrides (visual editor)."""
    pw, ph = TRIMS[trim]
    out = CSS.replace("width:148mm;min-height:210mm", f"width:{pw}mm;min-height:{ph}mm")
    out = out.replace("size:TRIM", f"size:{pw}mm {ph}mm")
    if not layout:
        # try loads from book dir if provided via thread-local? caller passes layout
        pass
    if layout:
        out += "\n/* layout.json (visual editor) */\n" + _layout_css(layout)
    return out


def load_layout(book_dir):
    lp = pathlib.Path(book_dir) / "layout.json"
    if lp.is_file():
        try:
            return json.loads(lp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _layout_css(L):
    """Map layout tokens -> CSS. Unknown keys ignored. All values strings already in CSS units."""
    def g(k, default=""):
        return str(L.get(k, default))
    rules = []
    # body type
    if "body_font" in L or "body_pt" in L:
        fam = g("body_font", "Cormorant,Georgia,serif")
        pt = g("body_pt", "15")
        lh = g("line_height", "1.5")
        rules.append(f"body{{font-family:'{fam.split(',')[0].strip().strip(chr(39))}',Georgia,serif;font-size:{pt}pt;line-height:{lh};}}")
    elif "line_height" in L:
        rules.append(f"body{{line-height:{g('line_height','1.5')};}}")
    # page box
    pad_y = g("page_pad_y", "")
    pad_x = g("page_pad_x", "")
    if pad_y or pad_x:
        rules.append(f".page{{padding:{pad_y or '12mm'} {pad_x or '18mm'};}}")
    if "page_margin_bottom" in L:
        rules.append(f".page{{margin-bottom:{g('page_margin_bottom','10mm')};}}")
    # type scale
    pairs = [
        ("h1_pt", ".titlepage h1{font-size:%spt;}"),
        ("sub_pt", ".titlepage .sub{font-size:%spt;}"),
        ("sec_h2_pt", ".sec-div h2{font-size:%spt;}"),
        ("prayer_h3_pt", ".prayer h3,.guide h3{font-size:%spt;}"),
        ("dev_pt", ".prayer .dev{font-size:%spt;}"),
        ("iast_pt", ".prayer .iast{font-size:%spt;}"),
        ("en_pt", ".prayer .en{font-size:%spt;}"),
        ("guide_h3_pt", ".guide h3{font-size:%spt;}"),
        ("guide_brief_pt", ".guide .brief{font-size:%spt;}"),
        ("guide_body_pt", ".guide .body{font-size:%spt;}"),
        ("pnum_pt", ".pnum{font-size:%spt;}"),
        ("toc_pt", ".toc li{font-size:%spt;}"),
    ]
    for key, tmpl in pairs:
        if key in L:
            rules.append(tmpl % g(key))
    # guide block spacing / positioning
    if "guide_gap_mm" in L:
        rules.append(f".guide .blk{{margin-bottom:{g('guide_gap_mm','1.5')}mm;}}")
    if "guide_h3_margin_mm" in L:
        rules.append(f".guide h3{{margin-bottom:{g('guide_h3_margin_mm','3')}mm;}}")
    if "prayer_dev_margin_mm" in L:
        rules.append(f".prayer .dev{{margin-top:{g('prayer_dev_margin_mm','3')}mm;}}")
    if "guide_align" in L and L["guide_align"] in ("left", "center", "right"):
        rules.append(f".guide h3,.guide .body,.guide .brief{{text-align:{L['guide_align']};}}")
    if "prayer_align" in L and L["prayer_align"] in ("left", "center", "right"):
        rules.append(f".prayer h3,.prayer .dev,.prayer .iast,.prayer .en{{text-align:{L['prayer_align']};}}")
    return "\n".join(rules) + "\n"


def esc(s):
    return html.escape(s or "")


def deva(iast):
    if not iast:
        raise ValueError("cannot transliterate an empty IAST source")
    if _tr is None:
        raise RuntimeError("indic-transliteration is required to build Devanagari")
    try:
        out = _tr(iast, sanscript.IAST, sanscript.DEVANAGARI)
    except Exception as exc:
        raise ValueError("cannot transliterate IAST") from exc
    return out.replace("\U0000A8F3", "\u0902").replace("\U0000A8F2", "\u0901")


def load_entries(d, entries):
    # Resolve the corpus declared by this entry, not a similarly named copy.
    # This keeps the printed citation tied to the same bytes as its source.
    indexes = {}
    root = pathlib.Path(d).resolve()
    out = []
    for e in entries:
        e = dict(e)
        if "corpus" in e:
            if e.get("iast"):
                raise ValueError(f"ambiguous IAST and corpus for {e.get('id', '?')}")
            source = e.get("source_path")
            if not isinstance(source, str) or pathlib.Path(source).is_absolute():
                raise ValueError(f"missing relative corpus source for {e.get('id', '?')}")
            corp = (root / source).resolve()
            if not corp.is_relative_to(root) or not corp.is_file():
                raise ValueError(f"corpus source missing or outside book for {e.get('id', '?')}")
            if corp not in indexes:
                c = json.loads(corp.read_text(encoding="utf-8"))
                idx = {}
                for ch in c["chapters"]:
                    for verse in ch["verses"]:
                        key = (ch["number"], verse["number"])
                        if key in idx:
                            raise ValueError(f"duplicate corpus reference {key}")
                        idx[key] = verse
                indexes[corp] = idx
            key = tuple(e["corpus"])
            if key not in indexes[corp]:
                raise ValueError(f"unresolved corpus reference for {e.get('id', '?')}")
            e["iast"] = indexes[corp][key]["iast"]
        if not e.get("iast"):
            raise ValueError(f"missing IAST for {e.get('id', '?')}")
        e["devanagari"] = deva(e["iast"])
        out.append(e)
    return out


def _dev_units(s):
    """Visual-width units: akshara=1, matra/virama/sign=0.25, space/newline=0."""
    u = 0.0
    for ch in s:
        o = ord(ch)
        if ch in " \n/|":
            continue
        if 0x0900 <= o <= 0x0903 or 0x093A <= o <= 0x094D \
                or 0x0951 <= o <= 0x0954 or 0x0962 <= o <= 0x0963 \
                or 0x0981 <= o <= 0x0981:
            u += 0.25
        else:
            u += 1.0
    return u


def dev_size(e):
    """Largest tier whose estimated wrapped block fits the prayer-sheet
    Devanagari budget (~250pt) — raw char counts lie (matras, line breaks)."""
    import math
    dev = e.get("devanagari", "")
    segs = [seg for seg in dev.split("\n") if seg.strip()] or [dev]
    for size, lh in ((40, 1.55), (32, 1.5), (25, 1.45), (20, 1.4), (16, 1.35)):
        cpl = max(6, int(317 / (0.65 * size)))   # 112mm text column, ~.65em/akshara
        lines = sum(max(1, math.ceil(_dev_units(seg) / cpl)) for seg in segs)
        if lines * size * lh <= 250:
            return f"{size}pt", str(lh)
    return "16pt", "1.35"


def en_size(e):
    L = sum(len(x) for x in e["en"].split("\n"))
    if L <= 140: return "13pt"
    if L <= 240: return "12pt"
    return "11pt"


def build(d):
    d = pathlib.Path(d)
    book = json.load(open(d / "book.json"))
    meta, sections, glyph = book["meta"], book["sections"], book.get("glyph")
    entries = load_entries(d, json.load(open(d / "entries.json")))
    front = (d / "front.html").read_text(encoding="utf-8") if (d / "front.html").exists() else ""
    back = (d / "back.html").read_text(encoding="utf-8") if (d / "back.html").exists() else ""

    pages = []
    cover_art = meta.get("cover_image")
    if cover_art is not None:
        if not isinstance(cover_art, dict) or not isinstance(cover_art.get("path"), str) or not cover_art.get("alt"):
            raise ValueError("cover_image requires path and alt")
        relative = pathlib.Path(cover_art["path"])
        image = (d / relative).resolve()
        if relative.is_absolute() or not image.is_relative_to(d.resolve()) or not image.is_file():
            raise ValueError("cover_image must be a file inside the book directory")
        if image.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            raise ValueError("cover_image must be PNG or JPEG")
        mark = (f'<img class="cover-mark" src="{html.escape(relative.as_posix(), quote=True)}" '
                f'alt="{html.escape(cover_art["alt"], quote=True)}">')
        cover_rel = relative.as_posix()
    else:
        mark = f'<div class="blurb">{esc(meta["blurb"])}</div>'
        cover_rel = None
    cover_page = f"""<section class="page cover">
<div class="om">ॐ</div>
<h1>{esc(meta['title'])}</h1>
<div class="sub">{esc(meta['subtitle'])}</div>
<div class="rule"></div>
{mark}
{('<div class="yantra" style="margin-top:10mm">' + rasa_rosette(0, 24) + '</div>') if glyph == 'rasa' else ''}
</section>"""

    if book.get("front_matter"):
        pages.append(f'<section class="page half"><div class="t">{esc(meta["title"])}</div></section>')
        pages.append('<section class="page blank"></section>')
        pages.append(f"""<section class="page titlepage">
<div class="om">ॐ</div>
<h1>{esc(meta['title'])}</h1>
<div class="sub">{esc(meta['subtitle'])}</div>
<div class="rule"></div>
{('<img src="' + html.escape(cover_rel, quote=True) + '" alt="">') if cover_rel else ''}
</section>""")
        pages.append(f"""<section class="page copy">
<div><b>{esc(meta['title'])}</b> — {esc(meta['subtitle'])}.</div>
<div>First edition.</div>
<div style="margin-top:3mm">Texts drawn from the Śaiva corpus, with translations for this edition.</div>
<div style="margin-top:3mm">Set in Cormorant Garamond and Tiro Devanagari Sanskrit.</div>
<div class="qr">Audio companion<br>scan to listen to every prayer</div>
</section>""")

    pages.append(f"""<section class="page epi center"><div class="lines">{esc(deva(meta['epi_iast']))}</div>
<div class="src">{esc(meta['epi_src'])}</div></section>""")
    # Optional, explicitly chosen artwork. Existing books without this field    # Optional, explicitly chosen artwork. Existing books without this field
    # are unchanged. File access is constrained to the book directory.
    art = book.get("opening_image")
    if art is not None:
        if not isinstance(art, dict) or not isinstance(art.get("path"), str) or not art.get("alt"):
            raise ValueError("opening_image requires path and alt")
        relative = pathlib.Path(art["path"])
        image = (d / relative).resolve()
        if relative.is_absolute() or not image.is_relative_to(d.resolve()) or not image.is_file():
            raise ValueError("opening_image must be a file inside the book directory")
        if image.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            raise ValueError("opening_image must be PNG or JPEG")
        mark = '<span class="draft-mark">DRAFT · NOT FOR SALE</span>' if art.get('draft_only', True) else ''
        pages.append(f'<section class="page opening-image">{mark}<img src="{html.escape(relative.as_posix(), quote=True)}" alt="{html.escape(art["alt"], quote=True)}"></section>')

    if front:
        pages.append(front)

    toc = ['<section class="page toc"><h2>Contents</h2><div class="head-rule"></div><ol>']
    for s in sections:
        num = f'<span class="num">{esc(s["numeral"])}</span>' if s.get("numeral") else ''
        toc.append(f'<div class="sec">{num}{esc(s["title"])}</div>')
        for e in [x for x in entries if x["section"] == s["id"]]:
            toc.append(f'<li>{esc(e["title"])}</li>')
    toc.append("</ol></section>")
    pages.append("".join(toc))

    n = 0
    def pagecount():
        return sum(len(re.findall(r'<section class="page', p)) for p in pages)

    for si, s in enumerate(sections, 1):
        # A section opens on a recto (odd page number); add an ornament verso if needed.
        if pagecount() % 2:
            pages.append(f'<section class="page orn"><img src="{html.escape(cover_rel, quote=True)}" alt=""></section>'
                         if cover_rel else '<section class="page blank"></section>')
        g = ""
        if glyph == "rasa":
            g = rasa_rosette(si, 22)
        elif glyph == "activity":
            g = activity_glyph(s["id"], 18)
        div = f'<div class="glyph">{g}</div>' if g else ""
        doc = f'<div class="doc">{esc(s["doctrine"])}</div>' if s.get("doctrine") else ""
        gls = f'<div class="gloss">{esc(s["gloss"])}</div>' if s.get("gloss") else ""
        num = f'<div class="num">{esc(s["numeral"])}</div>' if s.get("numeral") else ""
        pages.append(f"""<section class="page sec-div">{div}{num}
<h2>{esc(s['title'])}</h2><div class="sub">{esc(s.get('sub',''))}</div>{gls}<div class="rule"></div>{doc}</section>""")
        for e in [x for x in entries if x["section"] == s["id"]]:
            n += 1
            ds, dlh = dev_size(e)
            es = en_size(e)
            en_lines = "".join(f'<span class="ln">{esc(l)}</span>' for l in e["en"].split("\n"))
            pages.append(f"""<div class="spread">
<section class="page prayer">
<div class="src">{esc(e['source'])}</div>
<h3>{esc(e['title'])}</h3>
<div class="dev" style="font-size:{ds};line-height:{dlh}">{esc(e['devanagari'])}</div>
<div class="iast">{esc(e['iast'])}</div>
<div class="en" style="font-size:{es}">{en_lines}</div>
<div class="pnum">{n}</div></section>
<section class="page guide">
<div class="label">The Guide</div>
<h3>{esc(e['title'])}</h3>
<div class="src">{esc(e['source'])} · {esc(e.get('source_ref',''))}</div>
<div class="brief">{esc(e['brief'])}</div>
<div class="body">
<div class="blk"><span class="bl">What is it</span><p>{esc(e.get('what') or e.get('logic',''))}</p></div>
<div class="blk"><span class="bl">How to perform it</span><p>{esc(e.get('how') or e.get('howto',''))}</p></div>
{f'<div class="blk"><span class="bl">How to know it\'s working</span><p>{esc(e["sign"])}</p></div>' if e.get('sign') else ''}
{f'<div class="blk"><span class="bl">What to feel / visualise</span><p>{esc(e["feel"])}</p></div>' if e.get('feel') else ''}
</div>
<div class="foot">Source: <a href="{esc(e.get('source_path',''))}">{esc(e.get('source_path','').replace('sources/',''))} · {esc(e.get('source_ref',''))}</a></div>
<div class="pnum">{n} · guide</div></section>
</div>""")

    pages.append(f"""<section class="page epi center"><div class="lines" style="font-family:'Tiro'">ॐ शान्तिः शान्तिः शान्तिः</div>
<div class="src">{esc(meta['title'])}</div></section>""")

    if back:
        pages.append(back)

    seen, blist = set(), []
    for e in entries:
        p = e.get("source_path")
        if p and p not in seen:
            seen.add(p)
            refs = [x.get("source_ref", "") for x in entries if x.get("source_path") == p]
            blist.append((p, refs))
    bib = ['<section class="page bib"><h2>Sources</h2><ul>']
    for p, refs in blist:
        bib.append(f'<li><b>{esc(p.replace("sources/","").replace("-"," "))}</b><br>'
                   f'<a href="{esc(p)}">{esc(p)}</a><br>'
                   f'<span style="color:#76736e;font-size:8pt">{esc(", ".join(refs))}</span></li>')
    bib.append("</ul></section>")
    pages.append("".join(bib))

    trim = book.get("trim", "A5")
    if trim not in TRIMS:
        raise ValueError(f"unknown trim {trim!r}; choose one of {sorted(TRIMS)}")
    interior = "".join(pages)
    count = len(re.findall(r'<section class="page', interior))
    target = book.get("target_pages")
    if isinstance(target, int):
        if target % 2:
            raise ValueError(f"target_pages must be even for print, got {target}")
        if count > target:
            raise ValueError(f"interior is {count} pages, over target {target} — tighten layout first")
        pad = ""
        while count < target:
            pad += '<section class="page notes"><h2>Notes</h2><div class="ruled"></div></section>'
            count += 1
        interior += pad
    css = css_for(trim, load_layout(d))
    head = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{esc(meta["title"])} — {esc(meta["subtitle"])}</title>\n'
            f'<style>{css}</style></head><body>')
    (d / "index.html").write_text(head + cover_page + interior + "</body></html>", encoding="utf-8")
    (d / "interior.html").write_text(head + interior + "</body></html>", encoding="utf-8")
    print(f"built {d.name}: entries={len(entries)} sections={len(sections)} "
          f"interior={count}pp trim={trim}")


if __name__ == "__main__":
    build(sys.argv[1])
