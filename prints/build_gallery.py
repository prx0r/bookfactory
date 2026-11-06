#!/usr/bin/env python3
"""Build the prayer-card gallery: each poster beside its copyable JSON."""
import json, os, glob, html

PRINTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PRINTS)
PRAYERS = os.path.join(PRINTS, "prayers")
OUT = os.path.join(ROOT, "outputs", "print_products")
W, H = 1200, 1800

order = ["brahmarpanam", "lsj-siva-nama", "lsj-i-dont-mind", "lsj-embrace",
         "lsj-become-siva", "lsj-festival", "somananda", "s01v1"]

specs = {}
for p in glob.glob(os.path.join(PRAYERS, "*.json")):
    s = json.load(open(p, encoding="utf-8"))
    specs[s["id"]] = s
ids = [i for i in order if i in specs] + [i for i in specs if i not in order]

rows = []
for i in ids:
    s = specs[i]
    img = f"{i}/{i}_postcard_{W}x{H}.png"
    pretty = json.dumps(s, ensure_ascii=False, indent=1)
    lic = s.get("license", "")
    rows.append(f'''<article class="card">
  <div class="left">
    <a href="{img}"><img src="{img}" alt="{html.escape(s['title'])}"></a>
    <h2>{html.escape(s['title'])}</h2>
    <div class="src">{html.escape(s.get('source',''))}</div>
    {f'<div class="lic">{html.escape(lic)}</div>' if lic else ''}
  </div>
  <div class="json">
    <button onclick="copy(this)">Copy JSON</button>
    <pre>{html.escape(pretty)}</pre>
  </div>
</article>''')

page = f'''<!doctype html><meta charset="utf-8">
<title>Prayer cards — POSTCARD vertical 4×6″</title>
<style>
body{{font:15px/1.5 system-ui;background:#faf9f7;color:#17140f;max-width:1500px;margin:2rem auto;padding:0 2rem}}
h1{{font-weight:600;margin:.2rem 0}}.note{{font-size:13px;color:#888;max-width:1000px}}
.card{{display:grid;grid-template-columns:minmax(300px,420px) 1fr;gap:1.8rem;align-items:start;
  padding:1.6rem 0;border-top:1px solid #e6e2da}}
.left img{{width:100%;height:auto;background:#fff;box-shadow:0 2px 18px rgba(0,0,0,.12)}}
h2{{font-size:15px;margin:.7rem 0 .2rem}}.src{{color:#888;font-size:12px}}
.lic{{font-size:11px;color:#b06;margin-top:.3rem}}
.json{{position:relative}}
pre{{margin:0;background:#fff;border:1px solid #e6e2da;border-radius:8px;padding:1rem 1.1rem;
  font:12px/1.45 ui-monospace,Menlo,monospace;overflow:auto;max-height:560px;white-space:pre-wrap;
  word-break:break-word}}
button{{position:absolute;top:.6rem;right:.6rem;z-index:2;font:12px system-ui;padding:.35rem .7rem;
  border:1px solid #cfc9bd;border-radius:6px;background:#fff;cursor:pointer}}
button:active{{background:#f0ece4}}
@media(max-width:760px){{.card{{grid-template-columns:1fr}}}}
</style>
<h1>Prayer cards — POSTCARD vertical</h1>
<p class="note">1200×1800 px · 300 DPI · 4×6″ (101×152mm). Devanagari auto-fits both width and height (maximised); English at 53%. Copy the JSON to re-render with <code>prints/prayer_engine.py</code>.</p>
{''.join(rows)}
<script>
function copy(btn){{
  const pre = btn.parentElement.querySelector('pre');
  navigator.clipboard.writeText(pre.innerText).then(()=>{{
    const t=btn.textContent; btn.textContent='Copied ✓';
    setTimeout(()=>btn.textContent=t,1200);
  }});
}}
</script>
'''

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)

# combined json
combined = {i: specs[i] for i in ids}
open(os.path.join(OUT, "prayers.json"), "w", encoding="utf-8").write(
    json.dumps(combined, ensure_ascii=False, indent=1))
print(f"wrote index.html + prayers.json ({len(ids)} cards)")
