#!/usr/bin/env python3
"""Build Learn Sanskrit static site from entries.json (ipvv/svread shell).

Output: prints/learn-sanskrit/site/
  index.html + lesson-01.html … lesson-10.html

Merge into prx0r/ipvv later:
  cp -r prints/learn-sanskrit/site/* <ipvv>/site/dist/sanskrit/
  topnav: <a href="/sanskrit/index.html" data-sec="sanskrit">Sanskrit</a>
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site"
ENTRIES = json.loads((ROOT / "entries.json").read_text(encoding="utf-8"))
BOOK = json.loads((ROOT / "book.json").read_text(encoding="utf-8"))
BOXES = json.loads((ROOT / "rule-boxes.json").read_text(encoding="utf-8")) if (ROOT / "rule-boxes.json").is_file() else []
AUDIT = json.loads((ROOT / "grammar-audit.json").read_text(encoding="utf-8")) if (ROOT / "grammar-audit.json").is_file() else {}

CSS = """
:root{--paper:#fff;--card:#fff;--card-hi:#fffdf7;--ink:#17140f;--mut:#76736e;--faint:#a9a49c;--line:#e7e3db;--gold:#a86f14;--gold-ink:#7c5410;--sans:'Inter',system-ui,-apple-system,sans-serif;--serif:Georgia,'Cormorant Garamond',serif;--deva:'Tiro Devanagari Sanskrit','Noto Serif Devanagari',serif}
*{box-sizing:border-box}
b,strong{font-weight:600}
html{-webkit-text-size-adjust:100%}
body{font-family:var(--serif);margin:0;background:var(--paper);color:var(--ink);font-size:17px;line-height:1.55;min-height:100vh;display:flex;flex-direction:column}
a{color:var(--ink);text-decoration:underline;text-decoration-color:var(--line);text-underline-offset:2px}
a:hover{text-decoration-color:var(--gold)}
.topbar{position:sticky;top:0;z-index:50;background:var(--paper);border-bottom:1px solid var(--line)}
.topbar-in{max-width:1400px;margin:0 auto;display:flex;align-items:center;gap:.9rem;padding:.55rem 1rem}
.brand{color:var(--ink);white-space:nowrap;text-decoration:none;line-height:1.05}
.deva-brand{font-family:var(--deva);font-size:1.45rem;line-height:1.25}
.brand small{font-family:var(--sans);font-size:.68rem;color:var(--mut);letter-spacing:.08em;text-transform:uppercase;display:block;line-height:1}
.topnav{display:flex;gap:1.1rem;flex-wrap:nowrap;overflow-x:auto;font-family:var(--sans);font-size:.82rem;scrollbar-width:none}
.topnav::-webkit-scrollbar{display:none}
.topnav a{padding:.4rem .1rem;color:var(--mut);text-decoration:none;letter-spacing:.12em;text-transform:uppercase;white-space:nowrap;border-bottom:2px solid transparent}
.topnav a:hover{color:var(--ink);text-decoration:none}
.topnav a.on{color:var(--ink);font-weight:600;border-bottom-color:var(--gold)}
.burger{display:none;background:none;border:1px solid var(--line);border-radius:.5rem;padding:.35rem .6rem;font-size:1rem;cursor:pointer;color:var(--ink)}
.shell{flex:1;width:100%;max-width:1400px;margin:0 auto;display:grid;grid-template-columns:264px minmax(0,1fr) 228px;gap:2rem;padding:1.5rem 1rem 3rem;align-items:start}
.side{position:sticky;top:64px;max-height:calc(100vh - 84px);overflow:auto;font-family:var(--sans);font-size:.8rem;padding-right:.5rem}
.side .hd{color:var(--faint);font-size:.68rem;text-transform:uppercase;letter-spacing:.09em;margin:.7rem 0 .2rem;font-weight:400}
.side a{display:block;padding:.28rem .55rem;border-radius:.45rem;color:var(--ink);line-height:1.35;text-decoration:none}
.side a:hover{background:#f4f1ea;text-decoration:none}
.side a.on{background:#f4f1ea;font-weight:600}
.side .n{color:var(--faint);font-size:.72rem}
main{min-width:0;max-width:46rem}
.crumbs{font-family:var(--sans);font-size:.78rem;color:var(--mut);margin-bottom:.6rem}
.crumbs a{color:var(--mut)}
h1{font-weight:500;font-size:34px;letter-spacing:.01em;line-height:1.2;margin:.2rem 0 .4rem}
h2{font-weight:500;font-size:22px;margin:1.7rem 0 .35rem;border-bottom:1px solid var(--line);padding-bottom:.25rem}
h3{font-weight:600;font-size:1rem;margin:1.1rem 0 .3rem}
.klabel{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--mut)}
.sub{color:var(--mut);font-size:15px;margin-bottom:1rem}
.dev{font-family:var(--deva);font-size:1.55rem;line-height:1.85;margin:.4rem 0}
.iast{color:var(--mut);font-size:1rem;font-style:italic;margin:.2rem 0 .8rem}
.en{font-size:15px;max-width:72ch;line-height:1.6}
.stats{display:flex;gap:22px;flex-wrap:wrap;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:14px 0;margin:1rem 0 1.4rem;font-size:14px;color:var(--mut);font-family:var(--sans)}
.stats b{color:var(--ink);font-weight:600}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.5rem 0 1rem;font-family:var(--sans)}
th,td{border:1px solid var(--line);padding:.4rem .55rem;text-align:left;vertical-align:top}
th{background:#f6f3ee;font-weight:600;font-size:.72rem;letter-spacing:.05em;text-transform:uppercase;color:#555}
.depth{margin:.9rem 0;position:sticky;top:57px;background:var(--paper);padding:.35rem 0;z-index:5;border-bottom:1px solid var(--line);display:flex;gap:.35rem;flex-wrap:wrap}
.depth button{font-family:var(--sans);font-size:13px;padding:.42rem .85rem;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.depth button.on{background:var(--ink);color:var(--paper);border-color:var(--ink);font-weight:600}
.depth-panel{display:none}
.depth-panel.on{display:block}
.rulebox{border:2px solid var(--ink);padding:.75rem .95rem;margin:1rem 0;background:var(--card-hi);font-family:var(--sans);font-size:.92rem}
.rulebox .rb-t{font-weight:700;margin-bottom:.3rem}
.levels{display:grid;grid-template-columns:1fr;gap:.6rem;margin:1rem 0}
@media(min-width:700px){.levels{grid-template-columns:1fr 1fr 1fr}}
.level{border:1px solid var(--line);padding:.65rem .75rem;font-size:.9rem;background:var(--card-hi);font-family:var(--sans)}
.level b{display:block;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin-bottom:.3rem}
.idx a{display:flex;gap:10px;color:var(--ink);text-decoration:none;font-size:14px;padding:7px 0;border-bottom:1px solid var(--line);font-family:var(--sans)}
.idx a:hover{text-decoration:underline}
.idx a small{color:var(--mut);margin-left:auto;flex:none}
.card{display:block;padding:.7rem .9rem;border:1px solid var(--line);border-radius:.55rem;text-decoration:none;color:var(--ink);font-family:var(--sans);font-size:.9rem;background:var(--card)}
.card:hover{border-color:var(--gold);text-decoration:none}
.card b{display:block;margin-bottom:.15rem}
.card small{color:var(--mut)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(13rem,1fr));gap:.55rem;margin:.8rem 0 1.4rem}
.badge{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:.15rem .55rem;font-family:var(--sans);font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);margin-right:.35rem}
.badge.ok{border-color:#1f7a6e;color:#1f7a6e}
.badge.warn{border-color:var(--gold);color:var(--gold-ink)}
.mut{color:var(--mut);font-size:.92rem}
.prov{font-family:var(--sans);font-size:.72rem;color:var(--mut);letter-spacing:.04em;margin-top:1.2rem;border-top:1px solid var(--line);padding-top:.55rem}
.pn{display:flex;justify-content:space-between;gap:1rem;margin:2rem 0 0;padding-top:1rem;border-top:1px solid var(--line);font-family:var(--sans);font-size:.88rem}
.toc{position:sticky;top:64px;max-height:calc(100vh - 84px);overflow:auto;font-family:var(--sans);font-size:.82rem;border-left:1px solid var(--line);padding-left:1rem}
.toc .hd{color:var(--mut);font-size:.7rem;text-transform:uppercase;letter-spacing:.09em;margin-bottom:.4rem}
.toc a{display:block;padding:.22rem 0;color:#4a463c;line-height:1.4;text-decoration:none}
.toc a:hover{color:var(--ink)}
footer{border-top:1px solid var(--line);background:var(--card);margin-top:auto}
footer .fin{max-width:1400px;margin:0 auto;padding:1.2rem 1rem;font-family:var(--sans);font-size:.8rem;color:var(--mut);display:flex;gap:1.2rem;flex-wrap:wrap}
footer a{color:var(--gold-ink)}
pre{background:#f6f3ee;padding:.55rem .75rem;overflow:auto;font-size:.88rem;font-family:var(--sans);margin:.4rem 0 .8rem}
ul.compact{margin:.35rem 0 .9rem;padding-left:1.2rem;font-size:.95rem}

.playrow{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin:.6rem 0 1rem;font-family:var(--sans)}
.vplay{font-family:var(--sans);font-size:.8rem;border:1px solid var(--line);background:var(--card);border-radius:999px;padding:.35rem .85rem;cursor:pointer;color:var(--ink)}
.vplay:hover{border-color:var(--gold);color:var(--gold-ink)}
.vplay.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.kw{transition:color .18s ease;color:#cfc9be;padding:0 .02em}
.kw.on{color:var(--ink)}
.kword .kw{padding:0}

@media(max-width:1100px){.shell{grid-template-columns:240px minmax(0,1fr)}.toc{display:none}}
@media(max-width:800px){
  .shell{grid-template-columns:minmax(0,1fr)}
  .side{position:fixed;inset:57px auto 0 0;width:min(84vw,320px);background:var(--paper);border-right:1px solid var(--line);z-index:60;padding:1rem;transform:translateX(-105%);transition:transform .2s;max-height:none}
  body.navopen .side{transform:none}
  .burger{display:block}
  main{max-width:100%}
  .depth{top:53px}
  .dev{font-size:1.35rem}
}
"""

TOPNAV = (
    '<nav class="topnav" id="topnav">'
    '<a href="index.html" data-sec="sanskrit" class="on">Sanskrit</a>'
    "</nav>"
)


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def side_nav(active: str) -> str:
    stages = {}
    for e in ENTRIES:
        stages.setdefault(e["section"], []).append(e)
    order = [s["id"] for s in BOOK.get("sections", [])]
    titles = {s["id"]: s.get("title", s["id"]) for s in BOOK.get("sections", [])}
    parts = ['<div class="hd">Stages</div>']
    for sid in order:
        items = stages.get(sid, [])
        parts.append(f'<a href="index.html#{esc(sid)}" class="{"on" if active==sid else ""}">{esc(titles.get(sid,sid))} <span class="n">({len(items)})</span></a>')
        for e in items:
            n = e.get("n") or (ENTRIES.index(e) + 1)
            fn = f"lesson-{n:02d}.html"
            parts.append(f'<a href="{fn}" class="{"on" if active==e["id"] else ""}" style="padding-left:1rem">{esc(e.get("title",""))}</a>')
    parts.append('<div class="hd">Volume</div>')
    parts.append('<a href="index.html#boxes">Rule boxes</a>')
    parts.append('<a href="index.html#audit">Grammar audit</a>')
    parts.append('<a href="index.html#status">Status</a>')
    return "".join(parts)


def page(title: str, body: str, *, active: str = "index", crumb: str = "", toc: str = "") -> str:
    side = side_nav(active)
    toc_html = f'<aside class="toc"><div class="hd">On this page</div>{toc}</aside>' if toc else '<aside class="toc"></aside>'
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)} · Learn Sanskrit</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Tiro+Devanagari+Sanskrit:ital@0;1&family=Noto+Serif+Devanagari:wght@400;500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>{CSS}</style>
</head><body data-lesson="{esc(active if active.startswith("l") else "")}">
<div class="topbar"><div class="topbar-in">
<button class="burger" id="burger" aria-label="menu">☰</button>
<a class="brand" href="index.html"><span class="deva-brand">संस्कृत</span><small>learn · Abhinavagupta</small></a>
{TOPNAV}
</div></div>
<div class="shell">
<aside class="side" id="sidenav">{side}</aside>
<main>
{crumb}
{body}
</main>
{toc_html}
</div>
<footer><div class="fin">
<span>Learn Sanskrit with Abhinavagupta · Vol. I — content stage; print build last.</span>
<a href="index.html">Course</a>
<a href="https://github.com/prx0r/bookfactory">Source</a>
</div></footer>
<script>
document.getElementById('burger')?.addEventListener('click',()=>document.body.classList.toggle('navopen'));
document.querySelectorAll('.depth button[data-d]').forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    const d=btn.getAttribute('data-d');
    btn.parentElement.querySelectorAll('button').forEach(b=>b.classList.toggle('on',b===btn));
    document.querySelectorAll('.depth-panel').forEach(p=>p.classList.toggle('on',p.getAttribute('data-d')===d));
  }});
}});

// — lesson player (videofactory Fish voice + karaoke when audio-manifest has timings) —
(function(){
  var AUDIO_MANIFEST = null;
  fetch('audio-manifest.json').then(function(r){ return r.ok ? r.json() : null; })
    .then(function(m){ AUDIO_MANIFEST = m; })
    .catch(function(){ AUDIO_MANIFEST = null; });
  var au = document.getElementById('lesson-audio');
  if(!au) return;
  var lessonId = (document.body.getAttribute('data-lesson') || location.pathname.split('/').pop().replace('.html',''));
  function urlFor(kind){
    if(!AUDIO_MANIFEST || !AUDIO_MANIFEST.clips) return null;
    var c = AUDIO_MANIFEST.clips[lessonId + '__' + kind];
    return c || null;
  }
  document.querySelectorAll('.vplay[data-play]').forEach(function(btn){
    btn.addEventListener('click', function(){
      var kind = btn.getAttribute('data-play');
      var src = urlFor(kind);
      document.querySelectorAll('.vplay').forEach(function(b){ b.classList.remove('on'); });
      if(src){
        au.src = src;
        au.play().then(function(){ btn.classList.add('on'); }).catch(function(){
          document.getElementById('play-note').textContent = 'audio failed — using browser voice';
          speak(kind);
        });
      } else {
        speak(kind);
      }
    });
  });
  function speak(kind){
    try{
      speechSynthesis.cancel();
      var host = document.getElementById('src-line');
      var iast = document.querySelector('.iast');
      var text = (kind === 'verse' && iast) ? iast.textContent
               : (kind === 'howto' ? (document.querySelector('#practice') ? document.querySelector('#practice').textContent : iast.textContent)
               : iast.textContent);
      var u = new SpeechSynthesisUtterance(String(text).slice(0, 1200));
      u.rate = 0.95;
      u.onend = function(){ document.querySelectorAll('.vplay').forEach(function(b){ b.classList.remove('on'); }); };
      speechSynthesis.speak(u);
      document.getElementById('play-note').textContent = 'browser voice (Fish clip not rendered yet)';
      btnMark(kind);
    }catch(e){}
  }
  function btnMark(kind){
    document.querySelectorAll('.vplay').forEach(function(b){ b.classList.remove('on'); });
    var b = document.querySelector('.vplay[data-play="'+kind+'"]');
    if(b) b.classList.add('on');
  }
  au.addEventListener('ended', function(){
    document.querySelectorAll('.vplay').forEach(function(b){ b.classList.remove('on'); });
  });
})();
</script>
</body></html>
"""


def table(rows, cols):
    if not rows:
        return '<p class="mut">(empty)</p>'
    head = "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = ""
    for it in rows:
        if not isinstance(it, dict):
            continue
        tds = ""
        for c in cols:
            v = it.get(c, "")
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v)
            tds += f"<td>{esc(v)}</td>"
        body += f"<tr>{tds}</tr>"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def kv_list(d, keys):
    out = "<ul class='compact'>"
    for k in keys:
        if d.get(k):
            out += f"<li><b>{esc(k.replace('_',' '))}:</b> {esc(d.get(k))}</li>"
    out += "</ul>"
    return out


def lesson_body(e, n):
    w = e.get("witness") or {}
    rec = e.get("recitation") or {}
    tr = e.get("translation") or {}
    sx = e.get("syntax") or {}
    tri = e.get("trika") or {}
    pr = e.get("practice") or {}
    lv = e.get("levels") or {}
    comps = e.get("compounds") or {}
    boxes = e.get("rule_boxes") or []

    # Devanagari from IAST at "build" (site): use transliteration lib if present
    deva = ""
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        deva = transliterate(e.get("iast") or "", sanscript.IAST, sanscript.DEVANAGARI)
        deva = deva.replace("||", "॥").replace("|", "।")
    except Exception:
        deva = ""

    mapping = "".join(
        f"<li><b>{esc(m.get('role'))}</b> — {esc(m.get('trika'))}</li>"
        for m in (tri.get("mapping") or [])
    )
    exercises = "".join(f"<li>{esc(x)}</li>" for x in (pr.get("exercises") or []))
    sandhi_rows = [x for x in (e.get("sandhi") or []) if isinstance(x, dict) and "inputs" in x]
    sandhi_ex = next((x.get("exercise") for x in (e.get("sandhi") or []) if isinstance(x, dict) and "exercise" in x), "")

    boxes_html = ""
    for b in boxes:
        boxes_html += (
            f'<div class="rulebox"><div class="rb-t">{esc(b.get("title"))}</div>'
            f"{esc(b.get('body'))}</div>"
        )

    # 10-layer full (Decode-oriented) vs Learn vs Recognise via depth tabs
    learn = f"""
<p class="klabel">Learn it — practical entry</p>
{deva and f'<div class="dev">{esc(deva)}</div>' or ''}
<div class="iast">{esc(e.get('iast'))}</div>
<p class="en"><strong>{esc(e.get('en'))}</strong></p>
<p class="mut">{esc(e.get('brief'))}</p>
<p>{esc(pr.get('when',''))} {esc(pr.get('recite',''))}</p>
<div class="levels">
  <div class="level"><b>Learn it</b>{esc(lv.get('learn'))}</div>
  <div class="level"><b>Decode it</b>{esc(lv.get('decode'))}</div>
  <div class="level"><b>Recognise it</b>{esc(lv.get('recognise'))}</div>
</div>
"""

    decode = f"""
<p class="klabel">Decode it — rigorous language instruction</p>
{boxes_html}
<h3>3 · Padaccheda</h3>
{table(e.get('padaccheda') or [], ['surface','underlying','gloss','rule','morph'])}
{f'<p class="mut">Exercise: {esc(sandhi_ex)}</p>' if sandhi_ex else ''}
<h3>4 · Morphology</h3>
{table(e.get('morphology') or [], ['surface','lemma','analysis','formation'])}
<h3>5 · Compounds</h3>
<p>{esc(comps.get('tree',''))}</p>
{table(comps.get('members') or [], ['compound','members','relation','reading'])}
{f'<p class="mut">{esc(comps.get("note"))}</p>' if comps.get('note') else ''}
<h3>6 · Sandhi proof</h3>
{table(sandhi_rows, ['inputs','rule','output'])}
<h3>7 · Syntax</h3>
{kv_list(sx, ['case_roles','agreement','finite_verbs','implied'])}
<h3>8 · Translation from the syntax</h3>
<p class="mut">Interlinear: {esc(tr.get('interlinear'))}</p>
<p><strong>Literal:</strong> {esc(tr.get('literal'))}</p>
<p><strong>Readable:</strong> {esc(tr.get('readable'))}</p>
{f'<p class="mut">Alternatives: {esc(e.get("alternatives"))}</p>' if e.get('alternatives') else ''}
"""

    recognise = f"""
<p class="klabel">Recognise it — Trika exegesis</p>
<p><strong>Text / Abhinavagupta:</strong> {esc(tri.get('abhinavagupta'))}</p>
<p><strong>Bridge:</strong> {esc(tri.get('bridge'))}</p>
<ul class="compact">{mapping}</ul>
<p><strong>Lakshmanjoo:</strong> {esc(tri.get('lakshmanjoo'))}</p>
<p class="mut"><strong>Our synthesis:</strong> {esc(tri.get('our_synthesis'))}</p>
<h3>10 · Practice and mastery</h3>
{kv_list(pr, ['recite','write','memorise','when'])}
<p><strong>Transfer exercises:</strong></p>
<ul class="compact">{exercises}</ul>
"""

    toc = "".join(
        f'<a href="#{k}">{esc(t)}</a>'
        for k, t in [
            ("witness", "Witness"),
            ("recite", "Recitation"),
            ("depth", "Depth tabs"),
            ("prov", "Provenance"),
        ]
    )

    prev_n = n - 1 if n > 1 else None
    next_n = n + 1 if n < len(ENTRIES) else None
    pn = '<div class="pn">'
    if prev_n:
        pn += f'<a href="lesson-{prev_n:02d}.html">← Lesson {prev_n}</a>'
    else:
        pn += "<span></span>"
    if next_n:
        pn += f'<a href="lesson-{next_n:02d}.html">Lesson {next_n} →</a>'
    pn += "</div>"

    crumb = f'<div class="crumbs"><a href="index.html">Sanskrit</a> · {esc(e.get("section"))} · L{n}</div>'
    body = f"""
<p class="klabel">Lesson {n} / {len(ENTRIES)} · {esc(e.get('section'))}</p>
<h1>{esc(e.get('title'))}</h1>
<p class="sub">{esc(e.get('source'))} · <code>{esc(e.get('source_ref'))}</code></p>
<p>
  <span class="badge ok">content</span>
  <span class="badge">{esc(e.get('id'))}</span>
</p>

<h2 id="witness">1 · The passage</h2>
{deva and f'<div class="dev">{esc(deva)}</div>' or ''}
<div class="iast">{esc(e.get('iast'))}</div>
<p class="en">{esc(e.get('en'))}</p>
<p class="mut" id="src-line">{esc(e.get('source'))} · {esc(e.get('source_ref'))}</p>
<div class="playrow" id="playrow">
  <button type="button" class="vplay" data-play="verse" id="btn-verse">▶ recite Sanskrit</button>
  <button type="button" class="vplay" data-play="howto" id="btn-howto">▶ practice note</button>
  <span class="mut" id="play-note">Fish verse voice · karaoke when timings exist</span>
</div>
<audio id="lesson-audio" preload="none"></audio>

<h2 id="recite">2 · Recitation</h2>
<pre>{esc(rec.get('syllables',''))}</pre>
{kv_list(rec, ['vowel_lengths','articulation','metre'])}

<div id="depth">
<div class="depth">
  <button data-d="learn" class="on">Learn it</button>
  <button data-d="decode">Decode it</button>
  <button data-d="recognise">Recognise it</button>
</div>
<div class="depth-panel on" data-d="learn">{learn}</div>
<div class="depth-panel" data-d="decode">{decode}</div>
<div class="depth-panel" data-d="recognise">{recognise}</div>
</div>

<div id="prov" class="prov">
Source path: {esc(e.get('source_path'))} · layers from translation-work ·
Deva transliterated from IAST · rights: see bookfactory RIGHTS.md (commercial blocked until cleared)
</div>
{pn}
"""
    return page(e.get("title") or f"Lesson {n}", body, active=e.get("id"), crumb=crumb, toc=toc)


def index_body():
    meta = BOOK.get("meta") or {}
    stages = {}
    for e in ENTRIES:
        stages.setdefault(e["section"], []).append(e)
    order = [s["id"] for s in BOOK.get("sections", [])]
    titles = {s["id"]: s.get("title", s["id"]) for s in BOOK.get("sections", [])}

    lesson_links = []
    n = 0
    for sid in order:
        lesson_links.append(f'<h3 id="{esc(sid)}">{esc(titles.get(sid,sid))}</h3><div class="idx">')
        for e in stages.get(sid, []):
            n += 1
            lesson_links.append(
                f'<a href="lesson-{n:02d}.html"><b>{esc(e.get("title"))}</b>'
                f'<small>{esc(e.get("source_ref"))}</small></a>'
            )
        lesson_links.append("</div>")

    box_items = "".join(
        f'<div class="card"><b>{esc(b.get("title"))}</b><small>{esc(b.get("body"))}</small></div>'
        for b in BOXES
    )
    cov = "".join(
        f"<li><b>{esc(k)}:</b> {esc(', '.join(v))}</li>"
        for k, v in (AUDIT.get("coverage") or {}).items()
    )

    body = f"""
<p class="klabel">Vol. I · bookfactory · content stage</p>
<h1>Learn Sanskrit with Abhinavagupta</h1>
<p class="sub">{esc(meta.get('subtitle',''))}</p>
<p class="lede">{esc(meta.get('blurb',''))}</p>
<p>
  <span class="badge ok">10 lessons</span>
  <span class="badge ok">gate: content canonical</span>
  <span class="badge warn">print build due-later</span>
  <span class="badge warn">rights open</span>
</p>
<p class="mut">Discovery before explanation. Glosses &amp; morphology from translation-work L0/L2/L3;
Trika exegesis attributed; a handful of foundational rule boxes only. Target 108 pages.</p>

<h2 id="lessons">Lessons</h2>
{''.join(lesson_links)}

<h2 id="boxes">Rule boxes (whole volume)</h2>
<div class="grid">{box_items or '<p class="mut">none</p>'}</div>

<h2 id="audit">Grammar coverage</h2>
<ul class="compact">{cov}</ul>
<p class="mut">{esc(AUDIT.get('three_encounters_note',''))}</p>

<h2 id="status">Status vs print</h2>
<div class="stats">
  <span>Lessons <b>10 / 10</b></span>
  <span>Stages <b>5</b></span>
  <span>Target <b>108 pp</b></span>
  <span>Rule boxes <b>{len(BOXES)}</b></span>
</div>
<ul class="compact">
  <li><b>Done:</b> thesis, curriculum, 10 full 10-layer records, HTML preview, content gate PASS.</li>
  <li><b>Due later:</b> fonts in print build, per-entry ship handoff, audio plan, PDF (build last).</li>
  <li><b>Rights:</b> GRETIL/SanskritDocuments commercial routes open — no KDP ship until cleared.</li>
</ul>

<h2>Merge into ipvv / svread</h2>
<p class="mut">Static shell matches prx0r/ipvv (<code>site/dist</code>). Later:</p>
<pre>cp -r prints/learn-sanskrit/site/*  ipvv/site/dist/sanskrit/
# topnav add: &lt;a href="/sanskrit/index.html" data-sec="sanskrit"&gt;Sanskrit&lt;/a&gt;
python3 ipvv/site/build.py   # if shell rebuilt from build.py</pre>
"""
    return page("Learn Sanskrit with Abhinavagupta", body, active="index",
                crumb='<div class="crumbs">bookfactory · learn-sanskrit</div>',
                toc='<a href="#lessons">Lessons</a><a href="#boxes">Rule boxes</a><a href="#audit">Audit</a><a href="#status">Status</a>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(index_body(), encoding="utf-8")
    for i, e in enumerate(ENTRIES, 1):
        e["n"] = i
        (OUT / f"lesson-{i:02d}.html").write_text(lesson_body(e, i), encoding="utf-8")
    # machine index for merge/tools
    idx = {
        "title": "Learn Sanskrit with Abhinavagupta",
        "subtitle": (BOOK.get("meta") or {}).get("subtitle"),
        "lessons": [
            {"n": i, "id": e["id"], "title": e["title"], "source_ref": e["source_ref"],
             "section": e["section"], "html": f"lesson-{i:02d}.html"}
            for i, e in enumerate(ENTRIES, 1)
        ],
        "rule_boxes": BOXES,
        "merge": {
            "target": "prx0r/ipvv site/dist/sanskrit/",
            "topnav": '<a href="/sanskrit/index.html" data-sec="sanskrit">Sanskrit</a>',
        },
    }
    (OUT / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # audio manifest: map lessonId__kind -> relative wav url (videofactory cache names)
    clips = {}
    audio_dir = ROOT / "audio" / "clips"
    if audio_dir.is_dir():
        for wav in sorted(audio_dir.glob("*.wav")):
            # name: l01-mamatma__verse_<hash>.wav
            parts = wav.name.split("__")
            if len(parts) >= 2:
                lesson = parts[0]
                kind = parts[1].split("_")[0]
                clips[f"{lesson}__{kind}"] = f"audio/clips/{wav.name}"
    manifest = {
        "engine": "fish-audio/s2.1-pro-free",
        "voices": VOICES_SRC,
        "pattern": "prx0r/videofactory render_chapter sha1(voice|text) cache",
        "clips": clips,
        "karaoke": "timings via kashaudio MMS when available — play falls back to browser voice",
    }
    (OUT / "audio-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # copy clips into site for one-link
    site_audio = OUT / "audio" / "clips"
    if audio_dir.is_dir():
        site_audio.mkdir(parents=True, exist_ok=True)
        for wav in audio_dir.glob("*.wav"):
            dest = site_audio / wav.name
            if not dest.exists() or dest.stat().st_mtime < wav.stat().st_mtime:
                dest.write_bytes(wav.read_bytes())
    print(f"site → {OUT}")
    for f in sorted(OUT.glob("*.html")):
        print(" ", f.name, f.stat().st_size)


if __name__ == "__main__":
    main()
