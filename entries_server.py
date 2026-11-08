#!/usr/bin/env python3
"""bookfactory entries editor — local HTTP UI to edit entries.json and save.

  python3 entries_server.py            # http://127.0.0.1:8610/
  (writes back to prints/<book>/entries.json and git-commits the change)

Stdlib only. Fail-closed: refuses paths outside this repo; no PDF involved.
"""
from __future__ import annotations
import json
import subprocess
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
PRINTS = ROOT / "prints"
BOOKS = [
    "practical-prayers",
    "tantric-prayer",
    "learn-sanskrit",
    "trika-sanskrit-36",
]
# fields shown in the editor (order matters)
FIELDS = [
    "id", "section", "title", "source", "source_ref", "source_path",
    "iast", "en", "brief", "logic", "howto", "sign", "how", "feel",
    "alternatives", "recitation", "witness", "padaccheda", "morphology",
    "sandhi", "syntax", "translation", "trika", "practice", "levels",
    "rule_boxes",
]
TEXT_FIELDS = {
    "id", "section", "title", "source", "source_ref", "source_path",
    "iast", "en", "brief", "logic", "howto", "sign", "how", "feel",
    "alternatives",
}


def entries_path(book: str) -> Path:
    if book not in BOOKS:
        raise ValueError(f"unknown book {book}")
    p = PRINTS / book / "entries.json"
    if not p.is_file():
        raise ValueError(f"missing {p}")
    return p


def load(book: str):
    return json.loads(entries_path(book).read_text(encoding="utf-8"))


def save(book: str, entries, note: str) -> dict:
    if not isinstance(entries, list) or not entries:
        raise ValueError("entries must be a nonempty list")
    ids = [e.get("id") for e in entries]
    if any(not i for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("entries need unique non-empty id")
    path = entries_path(book)
    # keep backup
    bak = path.with_suffix(".json.edit-bak")
    bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # git commit
    msg = f"edit {book}: {note[:120] or 'entries via web editor'}"
    try:
        subprocess.run(
            ["git", "add", str(path.relative_to(ROOT))],
            cwd=ROOT, check=True, capture_output=True, text=True, timeout=30,
        )
        c = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        if c.returncode != 0 and "nothing to commit" not in (c.stdout + c.stderr):
            raise RuntimeError(c.stderr.strip() or c.stdout.strip())
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception as exc:
        commit = f"(git failed: {exc})"
    return {"ok": True, "book": book, "n": len(entries), "commit": commit, "ts": datetime.now(timezone.utc).isoformat()}


UI_TMPL = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>bookfactory · edit entries</title>
<style>
:root{--ink:#17140f;--mut:#76736e;--line:#e7e3db;--gold:#a86f14;--ok:#1f7a6e;--bg:#fff}
*{box-sizing:border-box}
body{font:16px/1.5 Georgia,serif;background:var(--bg);color:var(--ink);margin:0}
header{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line);z-index:5;padding:.7rem 1rem;display:flex;gap:.7rem;align-items:center;flex-wrap:wrap;font-family:system-ui,sans-serif}
header b{font-family:Georgia,serif;font-weight:500}
select,button,input,textarea{font-family:system-ui,sans-serif;font-size:.9rem}
select,input[type=text]{padding:.4rem .6rem;border:1px solid var(--line);border-radius:.4rem;background:#fff}
button{padding:.45rem .9rem;border:1px solid var(--ink);background:var(--ink);color:#fff;border-radius:.4rem;cursor:pointer}
button.secondary{background:#fff;color:var(--ink)}
button:disabled{opacity:.4;cursor:default}
#bar{display:flex;gap:.5rem;align-items:center}
#list{border-right:1px solid var(--line);width:240px;position:fixed;top:52px;bottom:0;overflow:auto;padding:.5rem;font-family:system-ui,sans-serif;font-size:.85rem;background:#faf9f7}
#list a{display:block;padding:.4rem .55rem;color:var(--ink);text-decoration:none;border-radius:.35rem}
#list a.on{background:#f4f1ea;font-weight:600}
#list a:hover{text-decoration:underline}
main{margin-left:250px;max-width:52rem;padding:1rem 1.2rem 6rem}
main h1{font-weight:500;font-size:1.4rem;margin:.2rem 0}
.field{margin:.7rem 0}
.field label{display:block;font-family:system-ui,sans-serif;font-size:.75rem;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);margin-bottom:.2rem}
.field input,.field textarea{width:100%;padding:.5rem .6rem;border:1px solid var(--line);border-radius:.4rem;font:15px/1.45 Georgia,serif;background:#fffdf7}
.field textarea{min-height:5.5rem;resize:vertical}
.field.big textarea{min-height:8rem}
#status{font-family:system-ui,sans-serif;font-size:.85rem;color:var(--ok)}
#status.err{color:#b04a5a}
.mut{color:var(--mut);font-size:.9rem}
details{margin:.6rem 0}
details summary{font-family:system-ui,sans-serif;font-size:.85rem;cursor:pointer;color:var(--mut)}
pre.raw{background:#f6f3ee;padding:.6rem;overflow:auto;font-size:.75rem;max-height:18rem}
</style></head><body>
<header>
  <b>bookfactory</b>
  <span class="mut">edit entries → save → auto-commit</span>
  <div id="bar">
    <label class="mut">book</label>
    <select id="book"></select>
    <input type="text" id="q" placeholder="filter…" size="12"/>
    <span id="status"></span>
    <button id="save" disabled>Save + commit</button>
  </div>
</header>
<nav id="list"></nav>
<main id="main"><p class="mut">Loading…</p></main>
<script>
let BOOK=null, ENTRIES=[], IDX=0, DIRTY=false;
const $=s=>document.querySelector(s);
const FIELDS=["title","source","source_ref","source_path","iast","en","brief","logic","howto","sign","how","feel","alternatives"];

function setStatus(msg, err){ const s=$("#status"); s.textContent=msg||""; s.className=err?"err":""; }

async function loadBook(name){
  BOOK=name; DIRTY=false; setStatus("");
  const r=await fetch("/api/entries?book="+encodeURIComponent(name));
  if(!r.ok){ setStatus("load failed "+r.status,1); return; }
  ENTRIES=await r.json();
  renderList(); select(0);
}

function renderList(){
  const q=($("#q").value||"").toLowerCase();
  const nav=$("#list"); nav.innerHTML="";
  ENTRIES.forEach((e,i)=>{
    if(q && !((e.id||"")+" "+(e.title||"")).toLowerCase().includes(q)) return;
    const a=document.createElement("a");
    a.href="#"+i; a.textContent=(e.id||i)+" — "+(e.title||"").slice(0,40);
    a.onclick=ev=>{ev.preventDefault();select(i)};
    if(i===IDX)a.className="on";
    nav.appendChild(a);
  });
}

function select(i){
  if(DIRTY && !confirm("Unsaved changes. Discard?")) return;
  IDX=i; DIRTY=false; $("#save").disabled=false;
  renderList();
  const e=ENTRIES[i];
  let html=`<p class="mut">#${i+1} / ${ENTRIES.length} · ${e.id}</p><h1>${esc(e.title||"")}</h1>`;
  html+=`<p class="mut">${esc(e.source||"")} · ${esc(e.source_ref||"")}</p>`;
  for(const f of FIELDS){
    const v=e[f]??"";
    const big=["iast","en","brief","logic","howto","sign","how"].includes(f);
    html+=`<div class="field${big?" big":""}"><label>${f}</label>`;
    if(big) html+=`<textarea data-f="${f}">${esc(String(v))}</textarea>`;
    else html+=`<input type="text" data-f="${f}" value="${esc(String(v))}"/>`;
    html+=`</div>`;
  }
  html+=`<details><summary>JSON of this entry</summary><pre class="raw">${esc(JSON.stringify(e,null,2))}</pre></details>`;
  $("#main").innerHTML=html;
  $("#main").querySelectorAll("[data-f]").forEach(el=>{
    el.addEventListener("input",()=>{
      ENTRIES[IDX][el.getAttribute("data-f")]=el.value;
      DIRTY=true; setStatus("unsaved…"); setStatus("unsaved…",1);
    });
  });
  setStatus("");
}

async function save(){
  const note=prompt("Commit note (what changed)?", "edit "+BOOK+" via web editor");
  if(note===null) return;
  $("#save").disabled=true; setStatus("saving…");
  const r=await fetch("/api/entries?book="+encodeURIComponent(BOOK),{
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({note:note, entries:ENTRIES})
  });
  const j=await r.json();
  if(!r.ok||j.error){ setStatus(j.error||("save failed "+r.status),1); $("#save").disabled=false; return; }
  DIRTY=false; setStatus("saved · "+j.commit); 
}

function esc(s){ return String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

(async function init(){
  const sel=$("#book");
  for(const b of ${json.dumps(BOOKS)}){
    const o=document.createElement("option"); o.value=b; o.textContent=b; sel.appendChild(o);
  }
  sel.onchange=()=>loadBook(sel.value);
  $("#q").oninput=()=>renderList();
  $("#save").onclick=save;
  await loadBook(sel.value);
})();
</script>
</body></html>
"""
UI = UI_TMPL.replace("const BKS = [];", "const BKS = " + json.dumps(BOOKS) + ";")
UI = UI_TMPL.replace("for(const b of ${json.dumps(BOOKS)}){", "for(const b of BKS){")

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("entries-server: " + (fmt % args) + "\n")

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            self._send(200, UI.encode("utf-8"), "text/html; charset=utf-8")
            return
        if u.path == "/api/books":
            self._json(200, {"books": BOOKS})
            return
        if u.path == "/api/entries":
            book = (parse_qs(u.query).get("book") or [""])[0]
            try:
                self._json(200, load(book))
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/api/entries":
            self._json(404, {"error": "not found"})
            return
        book = (parse_qs(u.query).get("book") or [""])[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 8_000_000:
                raise ValueError("body too large")
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
            entries = payload.get("entries")
            note = payload.get("note") or ""
            result = save(book, entries, note)
            self._json(200, result)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8610
    srv = HTTPServer(("127.0.0.1", port), H)
    print(f"bookfactory entries editor → http://127.0.0.1:{port}/  books={BOOKS}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
