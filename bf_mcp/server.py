#!/usr/bin/env python3
"""bookfactory MCP — the book factory as callable tools (FastMCP, stdio + HTTP).

Read tools inspect the factory; write tools shell to factory.py (which carries
its own gates and refuses on bad input). NO auto-publish/auto-sign.

Run:
  python3 bf_mcp/server.py --serve          # stdio MCP
  python3 bf_mcp/server.py --serve-http --port 8950
  python3 bf_mcp/server.py --list
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # /root/bookfactory
FACTORY = ROOT / "factory.py"
PROJECTS = ROOT / "projects"
PRINTS = ROOT / "prints"

from fastmcp import FastMCP
mcp = FastMCP("bookfactory")


def _safe(rel: str) -> Path:
    p = (ROOT / rel).resolve()
    if ROOT not in p.parents and p != ROOT:
        raise ValueError(f"path escapes repo: {rel}")
    return p


def _cli(sub: str, argv: list[str], timeout: int = 240) -> dict:
    r = subprocess.run([sys.executable, str(FACTORY), sub, *argv],
                       cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    out = (r.stdout or "").strip()
    try:
        data = json.loads(out) if out.startswith(("{", "[")) else out
    except ValueError:
        data = out
    return {"ok": r.returncode == 0, "command": sub, "rc": r.returncode,
            "output": data, "stderr": (r.stderr or "").strip()[-800:]}


def _lanes() -> list[str]:
    if not PROJECTS.is_dir():
        return []
    return sorted(d.name for d in PROJECTS.iterdir()
                  if d.is_dir() and not d.name.startswith("_"))


def _json(p: Path, default=None):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


# ---------------- READ ----------------
@mcp.tool()
def factory_overview() -> dict:
    """High-level factory state: lanes, templates, styles, docs, gate status."""
    lanes = _lanes()
    return {
        "root": str(ROOT),
        "lanes": lanes,
        "lane_count": len(lanes),
        "templates": sorted(p.stem for p in (ROOT / "templates").glob("*.json")) if (ROOT / "templates").is_dir() else [],
        "styles": sorted(p.stem for p in (ROOT / "styles").glob("*.json")) if (ROOT / "styles").is_dir() else [],
        "docs": sorted(p.name for p in ROOT.glob("*.md")),
        "registry": _json(ROOT / "REGISTRY.json", {}),
    }


@mcp.tool()
def list_lanes() -> dict:
    """List book lanes (projects)."""
    out = []
    for name in _lanes():
        th = _json(PROJECTS / name / "thesis.json", {}) or {}
        out.append({"book": name, "title": th.get("title"), "template": th.get("template"),
                    "stage": th.get("stage") or th.get("status")})
    return {"count": len(out), "lanes": out}


@mcp.tool()
def check_lane(book: str) -> dict:
    """State of one book lane: thesis, decisions count, files present."""
    d = PROJECTS / book
    if not d.is_dir():
        return {"error": f"unknown lane {book}"}
    files = sorted(p.name for p in d.iterdir() if p.is_file())
    dec = 0
    dj = d / "decisions.jsonl"
    if dj.exists():
        dec = sum(1 for ln in dj.read_text().splitlines() if ln.strip())
    th = _json(d / "thesis.json", {}) or {}
    return {"book": book, "title": th.get("title"), "template": th.get("template"),
            "claim": th.get("claim"), "files": files, "decisions": dec}


@mcp.tool()
def next_actions(book: str) -> dict:
    """Suggested next actions for a lane based on what exists."""
    d = PROJECTS / book
    if not d.is_dir():
        return {"error": f"unknown lane {book}"}
    have = {p.name for p in d.iterdir() if p.is_file()}
    acts = []
    if "thesis.json" not in have:
        acts.append("instantiate: new_book (needs thesis claim)")
    if not any(f.endswith("decisions.jsonl") for f in have):
        acts.append("record structure decision (decide --action declare-structure)")
    acts.append("stage --to structure|formatting|build as content fills")
    acts.append("audio_plan → epub → package when content complete")
    return {"book": book, "present": sorted(have), "next": acts}


@mcp.tool()
def read_thesis(book: str) -> dict:
    """Read a lane's thesis.json."""
    return {"book": book, "thesis": _json(PROJECTS / book / "thesis.json", None)}


@mcp.tool()
def list_specs() -> dict:
    """List factory spec/docs and schemas."""
    return {"docs": sorted(p.name for p in ROOT.glob("*.md")),
            "schemas": sorted(p.name for p in (ROOT / "schemas").glob("*.json")) if (ROOT / "schemas").is_dir() else []}


@mcp.tool()
def read_template(template: str) -> dict:
    """Read a genre template (templates/<id>.json)."""
    return {"template": template, "data": _json(ROOT / "templates" / f"{template}.json", None)}


@mcp.tool()
def read_entries(book: str) -> dict:
    """Read a lane's entries/book content if present."""
    d = PROJECTS / book
    for name in ("entries.json", "book.json", "content.json"):
        p = d / name
        if p.exists():
            return {"book": book, "file": name, "data": _json(p, None)}
    return {"book": book, "note": "no entries/book content file in lane", "files": sorted(p.name for p in d.iterdir() if p.is_file())}


@mcp.tool()
def read_book(book: str) -> dict:
    """Read the assembled bookkit book if present (build/ or lane)."""
    d = PROJECTS / book
    for cand in (d / "book.json", d / "build" / "book.json", d / "bookkit.json"):
        if cand.exists():
            return {"book": book, "file": str(cand.relative_to(ROOT)), "data": _json(cand, None)}
    return {"book": book, "note": "no assembled book.json"}


@mcp.tool()
def read_decisions(book: str) -> dict:
    """Read a lane's decision log (decisions.jsonl)."""
    p = PROJECTS / book / "decisions.jsonl"
    if not p.exists():
        return {"book": book, "decisions": [], "note": "no decisions yet"}
    rows = [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]
    return {"book": book, "count": len(rows), "decisions": rows}


@mcp.tool()
def read_docs() -> dict:
    """List all markdown docs in the factory."""
    docs = {p.name: len(p.read_text().splitlines()) for p in ROOT.glob("*.md")}
    return {"docs": docs}


@mcp.tool()
def read_file(path: str) -> dict:
    """Read a file inside the factory repo (sandboxed)."""
    p = _safe(path)
    if not p.is_file():
        return {"error": f"not a file: {path}"}
    txt = p.read_text(errors="replace")
    return {"path": path, "bytes": len(txt), "content": txt[:20000],
            "truncated": len(txt) > 20000}


@mcp.tool()
def list_dir(path: str = ".") -> dict:
    """List a directory inside the factory repo (sandboxed)."""
    p = _safe(path)
    if not p.is_dir():
        return {"error": f"not a dir: {path}"}
    items = []
    for c in sorted(p.iterdir()):
        items.append({"name": c.name, "dir": c.is_dir(),
                      "bytes": c.stat().st_size if c.is_file() else None})
    return {"path": path, "count": len(items), "items": items}


@mcp.tool()
def inspect_verse(text: str, ref: str, layer: str = "l3", gate_id: str = "") -> dict:
    """Inspect one exact translation-layer verse + its recorded gate (factory.py inspect)."""
    av = ["--text", text, "--ref", ref, "--layer", layer]
    if gate_id:
        av += ["--gate-id", gate_id]
    return _cli("inspect", av)


@mcp.tool()
def read_rule_boxes(book: str) -> dict:
    """Read a lane's rule boxes / thesis exclusions (structure hints)."""
    th = _json(PROJECTS / book / "thesis.json", {}) or {}
    return {"book": book,
            "structure": th.get("structure"),
            "exclusion": th.get("exclusion"),
            "inclusion": th.get("inclusion")}


# ---------------- WRITE / GATED ----------------
@mcp.tool()
def decide(book: str, action: str, target: str, justification: str,
           thesis_ref: str, from_section: str = "", to_section: str = "",
           decided_by: str = "owner", date: str = "") -> dict:
    """Append a justified content decision citing a thesis clause (factory.py decide).
    action: add-section|remove-section|add-entry|remove-entry|move-entry|retire-entry|replace-entry|declare-structure."""
    av = ["--book", book, "--action", action, "--target", target,
          "--justification", justification, "--thesis-ref", thesis_ref,
          "--decided-by", decided_by]
    if from_section: av += ["--from", from_section]
    if to_section: av += ["--to", to_section]
    if date: av += ["--date", date]
    return _cli("decide", av)


@mcp.tool()
def new_book(template: str, slug: str, claim: str, sections: list[str],
             title: str = "", entries_per_section: int = 0, max_pages: int = 0,
             style: str = "", series: str = "", volume: int = 0) -> dict:
    """Instantiate a genre template into a fresh lane (factory.py new-book).
    sections: list of 'ID:PURPOSE'. claim must be >=80 chars."""
    av = ["--template", template, "--slug", slug, "--claim", claim]
    for s in sections:
        av += ["--section", s]
    if title: av += ["--title", title]
    if entries_per_section: av += ["--entries-per-section", str(entries_per_section)]
    if max_pages: av += ["--max-pages", str(max_pages)]
    if style: av += ["--style", style]
    if series: av += ["--series", series]
    if volume: av += ["--volume", str(volume)]
    return _cli("new-book", av)


@mcp.tool()
def stage(book: str, to: str) -> dict:
    """Advance a lane: content→structure→formatting→build (PDF last) (factory.py stage)."""
    return _cli("stage", ["--book", book, "--to", to])


@mcp.tool()
def audio_plan(book: str) -> dict:
    """Plan per-entry audio clips (no API calls) (factory.py audio)."""
    return _cli("audio", ["--book", book])


@mcp.tool()
def epub(book: str) -> dict:
    """Build reflowable EPUB3 for the lane (factory.py epub)."""
    return _cli("epub", ["--book", book])


@mcp.tool()
def package(book: str) -> dict:
    """Assemble customer package: EPUB + PDF + audio + sha256 manifest (factory.py package)."""
    return _cli("package", ["--book", book])


@mcp.tool()
def quote_preview(text: str, ref: str, output: str, layer: str = "l3",
                  gate_id: str = "", backend: str = "chrome") -> dict:
    """Render a watermarked postcard/social preview from one exact verse (factory.py quote)."""
    av = ["--text", text, "--ref", ref, "--output", output,
          "--layer", layer, "--backend", backend]
    if gate_id:
        av += ["--gate-id", gate_id]
    return _cli("quote", av)


TOOLS = ["factory_overview", "list_lanes", "check_lane", "next_actions",
         "read_thesis", "list_specs", "read_template", "read_entries",
         "read_book", "read_decisions", "read_docs", "read_file", "list_dir",
         "inspect_verse", "read_rule_boxes", "decide", "new_book", "stage",
         "audio_plan", "epub", "package", "quote_preview"]


if __name__ == "__main__":
    import asyncio
    if "--serve-http" in sys.argv:
        port = 8950
        for i, a in enumerate(sys.argv):
            if a == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        mcp.run(transport="http", host="127.0.0.1", port=port, path="/mcp")
    elif "--serve" in sys.argv:
        mcp.run(transport="stdio")
    else:
        async def _list():
            print("bookfactory MCP — %d tools" % len(TOOLS))
            for n in TOOLS:
                t = await mcp.get_tool(n)
                print(f"  {n}: {(t.description or '').splitlines()[0] if t.description else ''}")
        asyncio.run(_list())
