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
import json, html, pathlib, sys

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
.page{background:#fff;width:148mm;min-height:210mm;margin:0 auto 10mm;padding:20mm 18mm;
  box-shadow:0 2px 14px rgba(0,0,0,.12);position:relative;page-break-after:always;overflow-wrap:anywhere;}
.spread{display:flex;gap:8mm;justify-content:center;flex-wrap:wrap;margin:0 auto 10mm;}
.spread .page{margin:0;}
.cover{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;}
.cover .om{font-family:'Tiro';font-size:60pt;line-height:1;margin-bottom:16mm;}
.cover h1{font-family:'Cormorant';font-weight:600;font-size:36pt;letter-spacing:.05em;margin:0;text-transform:uppercase;}
.cover .sub{font-size:16pt;font-style:italic;color:var(--grey);margin-top:4mm;}
.cover .rule{width:40mm;height:1px;background:var(--ink);margin:10mm auto;}
.cover .blurb{font-size:11pt;text-transform:uppercase;letter-spacing:.14em;color:var(--grey);}
.epi{display:flex;flex-direction:column;justify-content:center;}
.epi.center{align-items:center;text-align:center;}
.epi .lines{font-size:14pt;line-height:1.7;}
.epi .src{font-size:9.5pt;letter-spacing:.15em;text-transform:uppercase;color:var(--grey);margin-top:8mm;}
h2.blk{font-family:'Cormorant';font-weight:600;font-size:15pt;letter-spacing:.08em;text-transform:uppercase;margin:6mm 0 3mm;color:var(--ink);}
.epi h2.blk+p,.epi p{font-size:11.5pt;line-height:1.5;margin:0 0 3mm;}
.epi .sr{display:block;font-size:10pt;color:#76736e;line-height:1.45;margin-top:.8mm;}
.opening-image{display:flex;align-items:center;justify-content:center;}
.opening-image img{display:block;max-width:100%;max-height:165mm;object-fit:contain;}
.opening-image .draft-mark{position:absolute;top:8mm;right:10mm;font:8pt sans-serif;color:#a22;}
.epi table{border-collapse:collapse;font-size:12pt;width:100%;}
.epi th{text-align:left;font-size:9.5pt;letter-spacing:.14em;text-transform:uppercase;color:var(--grey);border-bottom:1px solid var(--ink);padding:2mm 2mm 2mm 0;font-weight:400;}
.epi td{padding:1.8mm 2mm 1.8mm 0;border-bottom:1px solid var(--hair);}
.epi td.s{font-style:italic;color:var(--grey);}
.bib ul{list-style:none;padding:0;margin:4mm 0 0;}
.bib li{margin:0 0 1.5mm;font-size:9.5pt;line-height:1.35;}
.bib li a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--hair);word-break:break-all;}
.toc h2,.sec-div h2,.bib h2{font-family:'Cormorant';font-weight:600;letter-spacing:.12em;text-transform:uppercase;font-size:13pt;color:var(--grey);}
.toc ol{list-style:none;padding:0;margin:5mm 0 0;column-count:2;column-gap:7mm;}
.toc li,.toc .sec{break-inside:avoid;-webkit-column-break-inside:avoid;}
.toc .sec{margin-top:3.5mm;font-size:9.5pt;letter-spacing:.18em;text-transform:uppercase;color:var(--grey);line-height:1.2;}
.toc li{margin:.5mm 0;font-size:11pt;line-height:1.35;}
.toc .n{color:var(--grey);display:inline-block;width:7mm;}
.sec-div{display:flex;flex-direction:column;justify-content:center;text-align:center;}
.sec-div .glyph{line-height:0;margin-bottom:5mm;}
.sec-div .num{font-family:'Cormorant';font-size:11pt;letter-spacing:.3em;color:var(--grey);}
.sec-div h2{font-size:26pt;letter-spacing:.06em;margin:4mm 0 0;color:var(--ink);text-transform:none;font-weight:600;}
.sec-div .sub{font-style:italic;color:var(--grey);font-size:13pt;margin-top:3mm;}
.sec-div .gloss{font-size:10pt;color:var(--grey);margin-top:2.5mm;letter-spacing:.01em;}
.sec-div .rule{width:30mm;height:1px;background:var(--ink);margin:7mm auto 0;}
.sec-div .doc{font-size:11pt;line-height:1.5;color:#241f19;max-width:108mm;margin:7mm auto 0;font-style:italic;}
.src{font-size:9.5pt;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);}
.prayer h3,.guide h3{font-family:'Cormorant';font-weight:600;font-size:17pt;margin:2mm 0 4mm;text-align:center;}
.prayer .dev{font-family:'Tiro';text-align:center;white-space:pre-line;margin:6mm 0 0;}
.prayer .iast{font-style:italic;color:var(--grey);text-align:center;font-size:11pt;line-height:1.5;margin-top:3mm;}
.prayer .en{margin:8mm 0 0;text-align:center;line-height:1.65;color:#241f19;}
.prayer .en .ln{display:block;}
.guide .label{font-size:9pt;letter-spacing:.24em;text-transform:uppercase;color:var(--grey);margin-bottom:3mm;}
.guide h3{text-align:left;font-size:19pt;margin:0 0 3mm;}
.guide .src{text-align:left;margin-bottom:4mm;}
.guide .brief{font-style:italic;color:var(--grey);font-size:11.5pt;line-height:1.45;padding-bottom:3mm;margin-bottom:4mm;border-bottom:1px solid var(--hair);}
.guide .blk{margin-bottom:3mm;}
.guide .bl{font-size:8.5pt;letter-spacing:.2em;text-transform:uppercase;color:var(--grey);display:block;margin-bottom:1mm;}
.guide .body{font-size:11pt;line-height:1.5;color:#241f19;}
.guide .body p{margin:0;}
.guide .foot{margin-top:auto;border-top:1px solid var(--hair);padding-top:3mm;font-size:9pt;color:var(--grey);}
.guide .foot a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--hair);}
.pnum{position:absolute;bottom:10mm;left:0;right:0;text-align:center;font-size:9pt;color:var(--grey);letter-spacing:.1em;}
@media print{html,body{background:#fff}.page{margin:0;box-shadow:none;width:auto;min-height:auto}.spread{display:block;margin:0}@page{size:A5;margin:0}}
"""


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


def dev_size(e):
    L = len(e.get("devanagari", ""))
    if L <= 90: return "40pt", "2.0"
    if L <= 150: return "32pt", "1.9"
    if L <= 240: return "25pt", "1.8"
    if L <= 340: return "20pt", "1.75"
    return "16pt", "1.7"


def en_size(e):
    L = sum(len(x) for x in e["en"].split("\n"))
    if L <= 140: return "15pt"
    if L <= 240: return "13.5pt"
    return "12.5pt"


def build(d):
    d = pathlib.Path(d)
    book = json.load(open(d / "book.json"))
    meta, sections, glyph = book["meta"], book["sections"], book.get("glyph")
    entries = load_entries(d, json.load(open(d / "entries.json")))
    front = (d / "front.html").read_text(encoding="utf-8") if (d / "front.html").exists() else ""
    back = (d / "back.html").read_text(encoding="utf-8") if (d / "back.html").exists() else ""

    pages = []
    pages.append(f"""<section class="page cover">
<div class="om">ॐ</div>
<h1>{esc(meta['title'])}</h1>
<div class="sub">{esc(meta['subtitle'])}</div>
<div class="rule"></div>
<div class="blurb">{esc(meta['blurb'])}</div>
{('<div class="yantra" style="margin-top:10mm">' + rasa_rosette(0, 24) + '</div>') if glyph == 'rasa' else ''}
</section>""")

    pages.append(f"""<section class="page epi center"><div class="lines">{esc(deva(meta['epi_iast']))}</div>
<div class="src">{esc(meta['epi_src'])}</div></section>""")

    # Optional, explicitly chosen artwork. Existing books without this field
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

    toc = ['<section class="page toc"><h2>Contents</h2><ol>']
    for s in sections:
        toc.append(f'<div class="sec">{esc(s["numeral"])} &nbsp; {esc(s["title"])} '
                   f'<span style="opacity:.6">{esc(s.get("sub",""))}</span></div>')
        for e in [x for x in entries if x["section"] == s["id"]]:
            toc.append(f'<li><span class="n">·</span>{esc(e["title"])}</li>')
    toc.append("</ol></section>")
    pages.append("".join(toc))

    n = 0
    for si, s in enumerate(sections, 1):
        g = ""
        if glyph == "rasa":
            g = rasa_rosette(si, 22)
        elif glyph == "activity":
            g = activity_glyph(s["id"], 18)
        div = f'<div class="glyph">{g}</div>' if g else ""
        doc = f'<div class="doc">{esc(s["doctrine"])}</div>' if s.get("doctrine") else ""
        gls = f'<div class="gloss">{esc(s["gloss"])}</div>' if s.get("gloss") else ""
        pages.append(f"""<section class="page sec-div">{div}<div class="num">{esc(s['numeral'])}</div>
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
                   f'<span style="color:#76736e;font-size:9.5pt">{esc(", ".join(refs))}</span></li>')
    bib.append("</ul></section>")
    pages.append("".join(bib))

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(meta['title'])} — {esc(meta['subtitle'])}</title>
<style>{CSS}</style></head><body>{''.join(pages)}</body></html>"""
    (d / "index.html").write_text(doc, encoding="utf-8")
    print(f"built {d.name}: entries={len(entries)} sections={len(sections)}")


if __name__ == "__main__":
    build(sys.argv[1])
