#!/usr/bin/env python3
"""Poems I — The Surrender: Abhinavagupta's short hymns, poem / craft-notebook spreads.
Sources: translation-work L4 DRAFT files (crafted lines + craft notes) and L2.v2 (plain reading).
Run with the patala venv python (needs indic_transliteration)."""

import json, html, pathlib, re, glob, sys

HERE = pathlib.Path(__file__).parent
TW = pathlib.Path("/home/box/repos/translation-work")
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as _tr
except Exception:
    _tr = None

WORKS = [
    dict(id="bhairavastava", dir="bhairavastava", l2="sources/bhairavastava-L2.md",
         numeral="I", title="Bhairavastava", sub="The Bhairava Hymn — 10 verses",
         note="Abhinavagupta's hymn of surrender: consciousness pervades, and the mind becomes it."),
    dict(id="pancashloki", dir="pancashloki", l2="sources/pancashloki-L2.md",
         numeral="II", title="Pañcaślokī", sub="Five Verses of offering",
         note="Abhinavagupta's five-verse surrender: pride offered, speech offered, doubt lifted."),
    dict(id="anuttarastika", dir="anuttarastika", l2="sources/anuttarastika-L2.md",
         numeral="III", title="Anuttarāṣṭikā", sub="Eight Verses on the No-Method",
         note="Abhinavagupta's eight verses: every method denied, recognition left standing."),
]

META = dict(title="The Surrender", subtitle="The Poems of Abhinavagupta, Volume I",
            blurb="Bhairavastava · Pañcaślokī · Anuttarāṣṭikā",
            epi_lines=["Enough of difference-talk — chewing the sap",
                       "of devotion to you: all this is one, at peace;",
                       "and even to say so feels shy."],
            epi_src="Mahopadeśaviṃśatikā v.8 — house voice of the poems")


def deva(iast):
    if _tr is None:
        return ""
    try:
        out = _tr(iast, sanscript.IAST, sanscript.DEVANAGARI)
    except Exception:
        return ""
    return out.replace("\U0000A8F3", "\u0902").replace("\U0000A8F2", "\u0901")


def parse_l2(path):
    """-> {passage_id: (title, prose)}"""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    out = {}
    parts = re.split(r"^## ", text, flags=re.M)
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        m = re.match(r"(\S+)\s+—\s+(.+?)\s*\(v\.\s*\d+\)", head)
        if not m:
            m = re.match(r"(\S+)\s+—\s+(.+)", head)
        if not m:
            continue
        pid, title = m.group(1), m.group(2).strip()
        # prose: strip the Sanskrit trailer and headers
        body = re.split(r"The Sanskrit:", body)[0]
        body = re.sub(r"^.*?\n", "", body, count=0)  # keep all; trim blank lines
        prose = " ".join(line.strip() for line in body.splitlines() if line.strip())
        prose = re.sub(r"\*\*.*?\*\*", "", prose)
        out[pid] = (title[:1].upper() + title[1:], prose.strip())
    return out


def load_poems():
    poems = []
    for w in WORKS:
        l2 = parse_l2(HERE / w["l2"])
        files = sorted(glob.glob(str(TW / w["dir"] / "L4-*.json")))
        for f in files:
            d = json.load(open(f))
            l4 = d.get("l4", {})
            pid = l4.get("verse_id") or pathlib.Path(f).stem
            title, prose = l2.get(pid, (f"Verse {l4.get('verse','')}", ""))
            poems.append(dict(
                work=w["id"], work_title=w["title"], numeral=w["numeral"],
                verse=l4.get("verse"), pid=pid, title=title,
                lines=l4.get("lines", []), iast=l4.get("sanskrit_cite", ""),
                dev=deva(l4.get("sanskrit_cite", "")),
                prose=prose,
                craft=d.get("craft_notes", ""),
                argmap=(d.get("reads_against") or {}).get("argmap", ""),
                rasa=(d.get("reads_against") or {}).get("c1_rasa", ""),
                status=d.get("status", ""),
                fidelity=l4.get("fidelity", ""),
                needs=", ".join(l4.get("needs", []) or []),
                l4file=pathlib.Path(f).name,
                src_dir=w["dir"],
            ))
    return poems


def esc(s):
    return html.escape(s or "")


def craft_size(p):
    L = len(p["craft"]) + len(p["argmap"] or "")
    if L <= 850:
        return "11.5pt", "1.55"
    if L <= 1250:
        return "10.5pt", "1.5"
    return "9.5pt", "1.45"


def prose_size(p):
    L = len(p["prose"] or "")
    if L <= 250:
        return "10.5pt"
    if L <= 340:
        return "9.5pt"
    return "9pt"


def poem_sizes(p):
    dl = len(p["dev"] or "")
    if dl > 320:
        dev = "11.5pt"
    elif dl > 220:
        dev = "13pt"
    else:
        dev = "14.5pt"
    hchars = sum(len(l) for l in p["lines"])
    if hchars > 250:
        hero = "13pt"
    elif hchars > 160:
        hero = "14pt"
    else:
        hero = "15pt"
    return dev, hero, prose_size(p)


def build_html(poems):
    css = """
@font-face{font-family:'Tiro';src:url('fonts/TiroDevanagariSanskrit-Regular.ttf');}
@font-face{font-family:'Cormorant';src:url('fonts/CormorantGaramond[wght].ttf');font-weight:400 700;}
:root{--ink:#17140f;--grey:#76736e;--hair:#d9d5cc;}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#efece5;color:var(--ink);}
body{font-family:'Cormorant',Georgia,serif;font-size:15pt;line-height:1.5;}
.page{background:#fff;width:148mm;min-height:210mm;margin:0 auto 10mm;padding:20mm 18mm;
  box-shadow:0 2px 14px rgba(0,0,0,.12);position:relative;page-break-after:always;}
.spread{display:flex;gap:8mm;justify-content:center;flex-wrap:wrap;margin:0 auto 10mm;}
.spread .page{margin:0;}
.cover{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;}
.cover .om{font-family:'Tiro';font-size:56pt;line-height:1;margin-bottom:14mm;}
.cover h1{font-family:'Cormorant';font-weight:600;font-size:34pt;letter-spacing:.06em;margin:0;text-transform:uppercase;}
.cover .sub{font-size:16pt;font-style:italic;color:var(--grey);margin-top:4mm;}
.cover .rule{width:40mm;height:1px;background:var(--ink);margin:10mm auto;}
.cover .blurb{font-size:11pt;text-transform:uppercase;letter-spacing:.14em;color:var(--grey);}
.epi{display:flex;flex-direction:column;justify-content:center;text-align:center;}
.epi .lines{font-size:15pt;line-height:1.8;font-style:italic;color:#241f19;}
.epi .src{font-size:9.5pt;letter-spacing:.15em;text-transform:uppercase;color:var(--grey);margin-top:10mm;}
.toc h2,.sec-div h2,.bib h2{font-family:'Cormorant';font-weight:600;letter-spacing:.12em;text-transform:uppercase;font-size:13pt;color:var(--grey);line-height:1.3;}
.toc ol{list-style:none;padding:0;margin:3mm 0 0;}
.toc .sec{margin-top:2.5mm;font-size:9.5pt;letter-spacing:.18em;text-transform:uppercase;color:var(--grey);line-height:1.2;}
.toc li{margin:.2mm 0;font-size:11pt;line-height:1.25;}
.toc .n{color:var(--grey);display:inline-block;width:8mm;}
.sec-div{display:flex;flex-direction:column;justify-content:center;text-align:center;}
.sec-div .num{font-family:'Cormorant';font-size:11pt;letter-spacing:.3em;color:var(--grey);}
.sec-div h2{font-size:28pt;letter-spacing:.06em;margin:4mm 0 0;color:var(--ink);text-transform:none;font-weight:600;}
.sec-div .sub{font-style:italic;color:var(--grey);font-size:13pt;margin-top:3mm;}
.sec-div .note{font-size:11.5pt;color:#241f19;max-width:100mm;margin:6mm auto 0;line-height:1.5;}
.sec-div .rule{width:30mm;height:1px;background:var(--ink);margin:8mm auto 0;}
.src{font-size:9.5pt;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);}
.poem h3,.craft h3{font-family:'Cormorant';font-weight:600;font-size:17pt;margin:2mm 0 4mm;text-align:center;}
.poem .dev{font-family:'Tiro';font-size:14.5pt;line-height:1.7;text-align:center;white-space:pre-line;}
.poem .iast{font-style:italic;color:var(--grey);text-align:center;font-size:10.5pt;line-height:1.45;margin-top:2mm;}
.poem .hero{margin:4mm auto 0;max-width:118mm;text-align:center;font-size:15pt;line-height:1.6;color:#241f19;}
.poem .hero .ln{display:block;}
.poem .plain{border-top:1px solid var(--hair);padding-top:3mm;}
.poem .plain .lbl{font-size:8.5pt;letter-spacing:.2em;text-transform:uppercase;color:var(--grey);display:block;margin-bottom:1.5mm;}
.poem .plain p{margin:0;font-size:11pt;line-height:1.45;color:var(--grey);}
.craft .label{font-size:9pt;letter-spacing:.24em;text-transform:uppercase;color:var(--grey);margin-bottom:3mm;}
.craft h3{text-align:left;font-size:19pt;margin:0 0 4mm;}
.craft .body{font-size:11.5pt;line-height:1.55;color:#241f19;}
.craft .body p{margin:0 0 3mm;}
.craft .blk{margin-bottom:3mm;}
.craft .bl{font-size:8.5pt;letter-spacing:.2em;text-transform:uppercase;color:var(--grey);display:block;margin-bottom:1mm;}
.craft .rasa{font-style:italic;color:var(--grey);font-size:10.5pt;margin-bottom:3mm;}
.craft .foot{margin-top:auto;border-top:1px solid var(--hair);padding-top:3mm;font-size:9pt;color:var(--grey);letter-spacing:.06em;}
.craft .foot a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--hair);}
.craft .badge{display:inline-block;font-size:8pt;letter-spacing:.14em;text-transform:uppercase;border:1px solid var(--hair);padding:.6mm 2mm;margin-right:2mm;color:var(--grey);}
.bib ul{list-style:none;padding:0;margin:6mm 0 0;}
.bib li{margin:0 0 4mm;font-size:11pt;}
.bib li a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--hair);}
.pnum{position:absolute;bottom:10mm;left:0;right:0;text-align:center;font-size:9pt;color:var(--grey);letter-spacing:.1em;}
@media print{html,body{background:#fff}.page{margin:0;box-shadow:none;width:auto;min-height:auto}.spread{display:block;margin:0}@page{size:A5;margin:0}}
"""
    pages = []
    pages.append(f"""<section class="page cover">
<div class="om">ॐ</div>
<h1>{esc(META['title'])}</h1>
<div class="sub">{esc(META['subtitle'])}</div>
<div class="rule"></div>
<div class="blurb">{esc(META['blurb'])}</div>
</section>""")

    epi = "".join(f'<span class="ln">{esc(l)}</span>' for l in META["epi_lines"])
    pages.append(f"""<section class="page epi"><div class="lines">{epi}</div>
<div class="src">{esc(META['epi_src'])}</div></section>""")

    toc = ['<section class="page toc"><h2>Contents</h2><ol>']
    for w in WORKS:
        toc.append(f'<div class="sec">{w["numeral"]} &nbsp; {esc(w["title"])} '
                   f'<span style="opacity:.6">{esc(w["sub"])}</span></div>')
        for p in [x for x in poems if x["work"] == w["id"]]:
            toc.append(f'<li><span class="n">{p["verse"]}</span>{esc(p["title"])}</li>')
    toc.append("</ol></section>")
    pages.append("".join(toc))

    n = 0
    for w in WORKS:
        wp = [x for x in poems if x["work"] == w["id"]]
        pages.append(f"""<section class="page sec-div"><div class="num">{esc(w['numeral'])}</div>
<h2>{esc(w['title'])}</h2><div class="sub">{esc(w['sub'])}</div>
<div class="note">{esc(w['note'])}</div><div class="rule"></div></section>""")
        for p in wp:
            n += 1
            hero = "".join(f'<span class="ln">{esc(l)}</span>' for l in p["lines"])
            badges = " ".join(f'<span class="badge">{esc(b)}</span>' for b in
                              filter(None, [p["status"], p["fidelity"], p["needs"]]))
            csize, clh = craft_size(p)
            dsize, hsize, psize = poem_sizes(p)
            pages.append(f"""<div class="spread">
<section class="page poem">
<div class="src">{esc(p['work_title'])} · verse {p['verse']}</div>
<h3>{esc(p['title'])}</h3>
<div class="dev" style="font-size:{dsize}">{esc(p['dev'])}</div>
<div class="iast">{esc(p['iast'])}</div>
<div class="hero" style="font-size:{hsize};line-height:1.6">{hero}</div>
<div class="plain"><span class="lbl">Plain reading (L2)</span><p style="font-size:{psize}">{esc(p['prose'])}</p></div>
<div class="pnum">{n}</div></section>
<section class="page craft">
<div class="label">The Craft</div>
<h3>{esc(p['title'])}</h3>
<div class="body" style="font-size:{csize};line-height:{clh}">
<p>{esc(p['craft'])}</p>
<div class="blk"><span class="bl">The logic</span><p>{esc(p['argmap'])}</p></div>
<div class="rasa">rasa — {esc(p['rasa'])}</div>
</div>
<div class="foot">{badges}<br>
L4: <a href="sources/{esc(p['src_dir'])}/{esc(p['l4file'])}">{esc(p['l4file'])}</a>
 · L2: <a href="{esc(WORKS[[w['id'] for w in WORKS].index(p['work'])]['l2'])}">{esc(p['pid'])}</a></div>
<div class="pnum">{n} · craft</div></section>
</div>""")

    pages.append(f"""<section class="page epi"><div class="lines"><span class="ln">ॐ शान्तिः शान्तिः शान्तिः</span></div>
<div class="src">The Surrender</div></section>""")

    bib = ['<section class="page bib"><h2>Sources</h2><ul>']
    for w in WORKS:
        bib.append(f'<li><b>{esc(w["title"])} — L2 plain reading</b><br>'
                   f'<a href="{esc(w["l2"])}">{esc(w["l2"])}</a></li>')
    bib.append('<li><b>L4 craft files (in the corpus)</b><br>'
               '<span style="color:#76736e">/home/box/repos/translation-work/'
               'bhairavastava/L4-*.json · pancashloki/ · anuttarastika/</span></li>')
    bib.append("</ul></section>")
    pages.append("".join(bib))

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(META['title'])} — {esc(META['subtitle'])}</title>
<style>{css}</style></head><body>{''.join(pages)}</body></html>"""
    (HERE / "index.html").write_text(doc, encoding="utf-8")


def build_json(poems):
    data = {"meta": META, "poems": poems, "count": len(poems)}
    (HERE / "poems.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    poems = load_poems()
    build_json(poems)
    build_html(poems)
    print(f"poems: {len(poems)}")
    for w in WORKS:
        print(f"  {w['numeral']}. {w['title']:<16} {len([p for p in poems if p['work']==w['id']])}")
    empty = [p["pid"] for p in poems if not p["lines"] or not p["craft"]]
    print("incomplete:", empty or "none")
