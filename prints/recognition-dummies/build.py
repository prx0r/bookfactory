#!/usr/bin/env python3
"""Recognition for Dummies — compile merged Q&A entries -> JSON + print HTML."""

import json, html, pathlib, re

HERE = pathlib.Path(__file__).parent

META = {
    "title": "Recognition for Dummies",
    "subtitle": "A no-nonsense guide to seeing what was always true",
    "blurb": "Kashmir Shaiva pratyabhijñā, in plain English",
    "epigraph_q": "What actually changes when someone has a recognition?",
    "epigraph_a": "The content of experience stays identical. What changes is the observer's relation to its own dependence — a single status flip, not new information.",
    "epigraph_src": "FORMALIZATION-OF-RECOGNITION",
}

SECTIONS = [
    ("recognition", "I", "The Recognition", [
        "recognit", "what changes", "status flip", "re-posit", "conditions of", "felt", "camatk"]),
    ("proof", "II", "Proof & Doubt", [
        "proof", "prove", "argument", "doubt", "evidence", "coerce", "force", "logic", "razor", "justif"]),
    ("self", "III", "The Self", [
        " the i ", "self-model", "ego", "ahaṃk", "ahamk", "who am i", "subject", "first-person",
        "self-grasp", "nonconstructed", "non-constructed", "mine"]),
    ("consciousness", "IV", "Consciousness & Freedom", [
        "consciousness", "freedom", "svatantr", "lord", "śiva", "shiva", "absolute", "awareness",
        "cit ", "vimarś", "vimsar", "self-lumin", "self-shin", "svaprakāś", "svaprakas"]),
    ("world", "V", "The World", [
        "world", "illusion", "dream", "unreal", "māyā", "maya", "construct", "object", "reflec",
        "appearance", "dual"]),
    ("practice", "VI", "Practice & Freedom", [
        "practice", "liberat", "transform", "meditat", "yoga", "path", "stabil", "absorb",
        "samādhi", "sadhana", "sādhana", "effort", "spontane"]),
    ("schools", "VII", "Against Other Schools", [
        "advaita", "vedanta", "buddh", "nyāya", "nyaya", "nisargad", "nietzsche", "other school",
        "competition", "differ", "vs ", "versus", "jain", "sāṃkhya", "samkhya"]),
    ("scripture", "VIII", "Scripture & Authority", [
        "ipvv", "text", "verse", "scripture", "authority", "abhinavagupta", "utpaladeva",
        "śivasūtra", "sivasutra", "spanda", "tantra", "krama", "vimarśinī", "vimarsini",
        "commentar", "canonical", "revelation", "śastra", "shastra"]),
]

SRC_GROUPS = [
    ("IPVV essays", "/home/box/Downloads/ipvv/site/data/essays/"),
    ("Recognition library (gochema)", "/home/box/repos/gochema/library/recognition/"),
    ("Recognition transcripts", "/home/box/recognition formulation · recognitionexpounded · recognitionandsiva"),
    ("Checkpoint modules", "/home/box/patalacheckpoints/docs/content/modules/"),
    ("Formalisation schema", "/home/box/sanskritree/FORMALISATION_SCHEMA.md"),
    ("Scripture L2 corpus", "/home/box/repos/translation-work/ (svabodhasiddhi, isvarasiddhi, ajadapramatrsiddhi, sambandhasiddhi, bodhavilasa, parapravesika)"),
]


def load_entries():
    d = json.load(open(HERE / "sources" / "entries_merged.json"))
    return d["entries"]


def bucket(e):
    text = (" " + e["q"] + " " + e["a"] + " " + e["source"] + " ").lower()
    best, best_score, order = None, 0, 0
    for sid, _, _, kws in SECTIONS:
        score = sum(text.count(k) for k in kws)
        if score > best_score or (score == best_score and score > 0 and SECTIONS.index(
                next(s for s in SECTIONS if s[0] == sid)) > order and best is None):
            if score > best_score:
                best, best_score, order = sid, score, SECTIONS.index(
                    next(s for s in SECTIONS if s[0] == sid))
    return best or "recognition"


def build():
    entries = load_entries()
    buckets = {s[0]: [] for s in SECTIONS}
    for e in entries:
        buckets[bucket(e)].append(e)

    data = {"meta": META,
            "sections": [{"id": s[0], "numeral": s[1], "title": s[2],
                          "entries": buckets[s[0]]} for s in SECTIONS],
            "entry_count": len(entries),
            "source_count": len({e["source"] for e in entries})}
    (HERE / "dummies.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def esc(s):
    return html.escape(s)


def build_html(data):
    css = """
@font-face{font-family:'Cormorant';src:url('fonts/CormorantGaramond[wght].ttf');font-weight:400 700;}
:root{--ink:#17140f;--grey:#76736e;--hair:#d9d5cc;}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#efece5;color:var(--ink);}
body{font-family:'Cormorant',Georgia,serif;font-size:14pt;line-height:1.5;}
.page{background:#fff;width:148mm;min-height:210mm;margin:0 auto 10mm;padding:20mm 18mm;
  box-shadow:0 2px 14px rgba(0,0,0,.12);position:relative;page-break-after:always;}
.cover{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;}
.cover .dev{font-family:'Noto','Tiro',serif;font-size:30pt;margin-bottom:12mm;color:var(--grey);}
.cover h1{font-family:'Cormorant';font-weight:600;font-size:36pt;letter-spacing:.04em;margin:0;text-transform:uppercase;}
.cover .sub{font-size:15pt;font-style:italic;color:var(--grey);margin-top:4mm;line-height:1.4;}
.cover .rule{width:40mm;height:1px;background:var(--ink);margin:10mm auto;}
.cover .blurb{font-size:11pt;text-transform:uppercase;letter-spacing:.16em;color:var(--grey);}
.epi{display:flex;flex-direction:column;justify-content:center;text-align:center;}
.epi .q{font-weight:600;font-size:16pt;margin-bottom:6mm;}
.epi .a{font-style:italic;color:var(--grey);font-size:13pt;max-width:100mm;margin:0 auto;line-height:1.55;}
.epi .src{font-size:9.5pt;letter-spacing:.15em;text-transform:uppercase;color:var(--grey);margin-top:8mm;}
.sec-div{display:flex;flex-direction:column;justify-content:center;text-align:center;}
.sec-div .num{font-family:'Cormorant';font-size:11pt;letter-spacing:.3em;color:var(--grey);}
.sec-div h2{font-family:'Cormorant';font-weight:600;font-size:26pt;letter-spacing:.08em;margin:4mm 0 0;text-transform:uppercase;}
.sec-div .rule{width:30mm;height:1px;background:var(--ink);margin:8mm auto 0;}
.sec-div .count{font-style:italic;color:var(--grey);font-size:12pt;margin-top:4mm;}
.qa{margin:0 0 6mm;page-break-inside:avoid;}
.qa .q{font-weight:600;font-size:13.5pt;line-height:1.4;}
.qa .q::before{content:"Q  ";color:var(--grey);font-weight:400;letter-spacing:.1em;}
.qa .a{font-size:12.5pt;line-height:1.5;color:#241f19;margin-top:1mm;}
.qa .s{display:block;font-size:8.5pt;letter-spacing:.08em;text-transform:uppercase;color:var(--grey);margin-top:1mm;}
.toc h2,.bib h2{font-family:'Cormorant';font-weight:600;letter-spacing:.12em;text-transform:uppercase;font-size:13pt;color:var(--grey);}
.toc ol{list-style:none;padding:0;margin:8mm 0 0;}
.toc li{margin:2.5mm 0;font-size:14pt;}
.toc .n{color:var(--grey);display:inline-block;width:8mm;}
.bib ul{list-style:none;padding:0;margin:6mm 0 0;}
.bib li{margin:0 0 4mm;font-size:10.5pt;line-height:1.45;color:#241f19;}
.bib li .p{color:var(--grey);font-size:9.5pt;display:block;word-break:break-all;}
.bib .intro{font-style:italic;color:var(--grey);font-size:12pt;}
@media print{html,body{background:#fff}.page{margin:0;box-shadow:none;width:auto;min-height:auto}@page{size:A5;margin:0}}
"""
    pages = []
    pages.append(f"""<section class="page cover">
<div class="dev">प्रत्यभिज्ञा</div>
<h1>{esc(META['title'])}</h1>
<div class="sub">{esc(META['subtitle'])}</div>
<div class="rule"></div>
<div class="blurb">{esc(META['blurb'])}</div>
</section>""")

    pages.append(f"""<section class="page epi">
<div class="q">{esc(META['epigraph_q'])}</div>
<div class="a">{esc(META['epigraph_a'])}</div>
<div class="src">{esc(META['epigraph_src'])}</div></section>""")

    toc = ['<section class="page toc"><h2>Contents</h2><ol>']
    for s in data["sections"]:
        toc.append(f'<li><span class="n">{esc(s["numeral"])}</span>{esc(s["title"])}'
                   f'<span style="color:#76736e;font-size:11pt"> — {len(s["entries"])} questions</span></li>')
    toc.append("</ol></section>")
    pages.append("".join(toc))

    for s in data["sections"]:
        if not s["entries"]:
            continue
        pages.append(f"""<section class="page sec-div"><div class="num">{esc(s['numeral'])}</div>
<h2>{esc(s['title'])}</h2><div class="rule"></div>
<div class="count">{len(s['entries'])} questions</div></section>""")
        qas = "".join(
            f'<div class="qa"><div class="q">{esc(e["q"])}</div>'
            f'<div class="a">{esc(e["a"])}<span class="s">{esc(e["source"])}</span></div></div>'
            for e in s["entries"])
        pages.append(f'<section class="page"><div class="sec-head"></div>{qas}</section>')

    bib = ['<section class="page bib"><h2>Sources</h2>',
           f'<p class="intro">All {data["entry_count"]} answers distilled from {data["source_count"]} '
           f'documents in the house archive — nothing invented, nothing from outside the box.</p><ul>']
    for label, path in SRC_GROUPS:
        bib.append(f'<li><b>{esc(label)}</b><span class="p">{esc(path)}</span></li>')
    bib.append("</ul></section>")
    pages.append("".join(bib))

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(META['title'])}</title><style>{css}</style></head>
<body>{''.join(pages)}</body></html>"""
    (HERE / "index.html").write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    data = build()
    build_html(data)
    print(f"entries: {data['entry_count']}  sources: {data['source_count']}")
    for s in data["sections"]:
        print(f"  {s['numeral']}. {s['title']:<26} {len(s['entries'])}")
