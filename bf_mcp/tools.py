"""bookfactory MCP tools — read + act on the publishing factory.

Read tools are in-process (json only). Action tools shell out to factory.py
with the patala venv so jsonschema/PyMuPDF behave the same as the CLI.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

ROOT = Path("/home/box/repos/bookfactory")
TRANSLATIONS = Path(os.environ.get("BOOKFACTORY_TRANSLATIONS", "/home/box/repos/translation-work"))
VENV_PY = Path(os.environ.get("BOOKFACTORY_PY", "/home/box/Documents/patala/.venv/bin/python3"))
if not VENV_PY.is_file():
    VENV_PY = Path(sys.executable)

# Paths an agent may read (fail-closed: outside = refuse)
READ_ROOTS = (
    ROOT,
    TRANSLATIONS,
)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_read(rel: str, *, allow_translations: bool = False) -> dict:
    """Resolve a relative path under the factory (or translation-work if allowed)."""
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        return {"ok": False, "error": "path must be relative without .."}
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT):
        return {"ok": False, "error": "path escapes bookfactory root"}
    if not p.is_file():
        # optional translations root
        if allow_translations:
            t = (TRANSLATIONS / rel).resolve()
            if t.is_relative_to(TRANSLATIONS) and t.is_file():
                return {"ok": True, "path": str(t), "text": t.read_text(encoding="utf-8", errors="replace")}
        return {"ok": False, "error": f"not a file: {rel}"}
    return {"ok": True, "path": str(p), "text": p.read_text(encoding="utf-8", errors="replace")}


def _run_factory(argv: list[str], timeout: int = 60) -> dict:
    """Run factory.py subcommand with venv python. Never runs long renders."""
    cmd = [str(VENV_PY), str(ROOT / "factory.py"), *argv]
    try:
        proc = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "factory.py timed out", "cmd": cmd}
    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return {
        "ok": proc.returncode == 0,
        "exit": proc.returncode,
        "cmd": cmd,
        "output": out.strip(),
    }


def _run_check(lane: str | None) -> dict:
    cmd = [str(VENV_PY), str(ROOT / "check.py")]
    if lane:
        cmd.append(lane)
    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "check.py timed out"}
    text = ((proc.stdout or "") + (proc.stderr or "")).strip()
    blocking = "BLOCKED" in text and "CANONICAL" not in text
    canonical = "CANONICAL" in text
    return {
        "ok": True,
        "canonical": canonical,
        "blocking": blocking and not canonical,
        "exit": proc.returncode,
        "output": text,
        "lane": lane or "*",
    }


# ── READ tools ──────────────────────────────────────────────────────

def factory_overview(args: dict) -> dict:
    reg = _json(ROOT / "REGISTRY.json")
    docs = [p.name for p in sorted(ROOT.glob("*.md"))]
    return {
        "ok": True,
        "root": str(ROOT),
        "goal": reg.get("goal"),
        "mode": reg.get("mode"),
        "lanes": reg.get("lanes"),
        "milestones": reg.get("milestones"),
        "docs": docs,
        "layout": {
            "FACTORY-SPEC.md": "the law (position, products, bars)",
            "BOOKS.md": "canonical system: template→thesis→decisions→stages→products",
            "PIPELINE.md": "commands, setup, blockers",
            "AUTONOMY.md": "unsupervised operation contract",
            "AGENTS.md": "repo rules",
            "check.py": "the only gate; exit 0 = canonical",
            "factory.py": "CLI: inspect/quote/decide/new-book/stage/audio/epub/package",
            "templates/": "genre templates",
            "styles/": "style packs",
            "projects/<book>/": "thesis.json + decisions.jsonl + lane.py + project.json",
            "prints/<book>/": "book.json + entries.json + HTML/PDF outputs",
            "specs/": "pre-lane thesis objects (*.thesis.json + curriculum md)",
            "schemas/": "fail-closed JSON schemas",
        },
        "laws": [
            "content → structure → formatting → build; PDF last",
            "no retyped text; Deva from IAST at build",
            "every decision cites a thesis clause; append-only",
            "GATE BLOCKED = does not ship without owner adjudication",
            "renders/fleet only for heavy media (Global Rule 8); book PDFs via chrome at build stage",
        ],
    }


def list_lanes(args: dict) -> dict:
    reg = _json(ROOT / "REGISTRY.json")
    lanes = []
    for name, meta in (reg.get("lanes") or {}).items():
        proj = ROOT / "projects" / name
        entry = {"name": name, **({} if isinstance(meta, dict) else {"stage": str(meta)})}
        if isinstance(meta, dict):
            entry.update(meta)
        pj = proj / "project.json"
        if pj.is_file():
            try:
                p = _json(pj)
                entry["project_stage"] = p.get("stage")
                entry["max_pages"] = p.get("max_pages")
            except Exception:
                pass
        th = proj / "thesis.json"
        if th.is_file():
            try:
                t = _json(th)
                entry["title"] = t.get("title")
                entry["template"] = t.get("template")
                entry["total_entries"] = (t.get("structure") or {}).get("total_entries")
            except Exception:
                pass
        entry["has_project"] = proj.is_dir()
        entry["has_prints"] = (ROOT / "prints" / name).is_dir()
        lanes.append(entry)
    return {"ok": True, "lanes": lanes}


def check_lane(args: dict) -> dict:
    lane = args.get("lane")
    if lane:
        if not (ROOT / "projects" / lane).is_dir() and lane != "*":
            # still allow prints-only? check needs project
            pass
    return _run_check(None if lane in (None, "*") else lane)


def read_thesis(args: dict) -> dict:
    book = args.get("book")
    spec = args.get("spec")
    path = args.get("path")
    if path:
        return _safe_read(path)
    if spec:
        # bare name or full
        candidates = [
            ROOT / "specs" / (spec if spec.endswith(".json") else f"{spec}.thesis.json"),
            ROOT / "specs" / spec,
        ]
        for c in candidates:
            if c.is_file():
                return {"ok": True, "path": str(c), "data": _json(c)}
        return {"ok": False, "error": f"spec not found: {spec}", "available": sorted(p.name for p in (ROOT / "specs").glob("*"))}
    if book:
        p = ROOT / "projects" / book / "thesis.json"
        if not p.is_file():
            return {"ok": False, "error": f"no thesis for {book}"}
        return {"ok": True, "path": str(p), "data": _json(p)}
    return {"ok": False, "error": "book, spec, or path required"}


def list_specs(args: dict) -> dict:
    specs = sorted(p.name for p in (ROOT / "specs").glob("*") if p.is_file())
    templates = sorted(p.stem for p in (ROOT / "templates").glob("*.json"))
    styles = sorted(p.stem for p in (ROOT / "styles").glob("*.json"))
    return {"ok": True, "specs": specs, "templates": templates, "styles": styles}


def read_template(args: dict) -> dict:
    tid = args.get("id") or args.get("template")
    if not tid:
        return {"ok": False, "error": "id required"}
    p = ROOT / "templates" / f"{tid}.json"
    if not p.is_file():
        return {"ok": False, "error": f"missing template {tid}", "available": sorted(x.stem for x in (ROOT / "templates").glob("*.json"))}
    return {"ok": True, "path": str(p), "data": _json(p)}


def read_entries(args: dict) -> dict:
    book = args.get("book")
    if not book:
        return {"ok": False, "error": "book required"}
    p = ROOT / "prints" / book / "entries.json"
    if not p.is_file():
        return {"ok": False, "error": f"no entries.json for {book}"}
    data = _json(p)
    # optional filter
    eid = args.get("entry_id")
    if eid and isinstance(data, list):
        for e in data:
            if e.get("id") == eid:
                return {"ok": True, "path": str(p), "entry": e, "count": len(data)}
        return {"ok": False, "error": f"entry {eid} not found", "ids": [e.get("id") for e in data if isinstance(e, dict)]}
    return {"ok": True, "path": str(p), "count": len(data) if isinstance(data, list) else None, "entries": data}


def read_book(args: dict) -> dict:
    book = args.get("book")
    if not book:
        return {"ok": False, "error": "book required"}
    p = ROOT / "prints" / book / "book.json"
    if not p.is_file():
        return {"ok": False, "error": f"no book.json for {book}"}
    return {"ok": True, "path": str(p), "data": _json(p)}


def read_decisions(args: dict) -> dict:
    book = args.get("book")
    if not book:
        return {"ok": False, "error": "book required"}
    p = ROOT / "projects" / book / "decisions.jsonl"
    if not p.is_file():
        return {"ok": False, "error": f"no decisions for {book}"}
    lines = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return {"ok": True, "path": str(p), "count": len(lines), "decisions": lines}


def read_docs(args: dict) -> dict:
    name = args.get("doc") or args.get("name") or ""
    # allow .md suffix
    if not name:
        return {"ok": False, "error": "doc required", "available": sorted(p.name for p in ROOT.glob("*.md"))}
    if not name.endswith(".md"):
        name = name + ".md"
    if name not in {p.name for p in ROOT.glob("*.md")}:
        return {"ok": False, "error": f"unknown doc {name}", "available": sorted(p.name for p in ROOT.glob("*.md"))}
    return _safe_read(name)


def read_file(args: dict) -> dict:
    return _safe_read(args.get("path") or "", allow_translations=bool(args.get("allow_translations")))


def list_dir(args: dict) -> dict:
    rel = args.get("path") or "."
    if rel.startswith("/") or ".." in Path(rel).parts:
        return {"ok": False, "error": "relative path only"}
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT):
        return {"ok": False, "error": "escapes root"}
    if not p.is_dir():
        return {"ok": False, "error": f"not a dir: {rel}"}
    items = []
    for c in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        items.append({
            "name": c.name,
            "dir": c.is_dir(),
            "size": c.stat().st_size if c.is_file() else None,
        })
    return {"ok": True, "path": str(p), "items": items}


def next_actions(args: dict) -> dict:
    """Worklist for an agent: gate output + registry + stage law."""
    lane = args.get("lane")
    check = _run_check(lane)
    reg = _json(ROOT / "REGISTRY.json")
    out = check.get("output", "")
    blocked, due = [], []
    for line in out.splitlines():
        if line.startswith("[BLOCKED]"):
            blocked.append(line)
        elif line.startswith("[DUE-LATER"):
            due.append(line)
    actions = []
    for b in blocked:
        actions.append({"priority": "high", "kind": "block", "detail": b})
    for d in due:
        actions.append({"priority": "medium", "kind": "due-later", "detail": d})
    if not blocked and not due:
        actions.append({"priority": "info", "kind": "ok", "detail": "no blocking or due-later problems"})
    return {
        "ok": True,
        "canonical": check.get("canonical"),
        "lane": check.get("lane"),
        "actions": actions,
        "milestones_todo": [m for m in reg.get("milestones", []) if m.get("status") not in ("done",)],
        "stage_law": "content → structure → formatting → build (PDF last). Advance only via factory stage after gate passes the prior stage.",
        "raw_output": out,
    }


def inspect_verse(args: dict) -> dict:
    text = args.get("text")
    ref = args.get("ref")
    if not text or not ref:
        return {"ok": False, "error": "text and ref required (exact verse_id, not a number guess)"}
    argv = ["inspect", "--text", text, "--ref", ref]
    if args.get("layer"):
        argv += ["--layer", args["layer"]]
    if args.get("gate_id"):
        argv += ["--gate-id", args["gate_id"]]
    argv += ["--translations", str(TRANSLATIONS)]
    return _run_factory(argv)


def read_rule_boxes(args: dict) -> dict:
    book = args.get("book") or "learn-sanskrit"
    p = ROOT / "prints" / book / "rule-boxes.json"
    if not p.is_file():
        # generic: any project docs
        return {"ok": False, "error": f"no rule-boxes.json for {book}"}
    return {"ok": True, "path": str(p), "data": _json(p)}


# ── ACTION tools ────────────────────────────────────────────────────

def decide(args: dict) -> dict:
    book = args.get("book")
    action = args.get("action")
    target = args.get("target")
    justification = args.get("justification") or ""
    thesis_ref = args.get("thesis_ref")
    if not all([book, action, target, thesis_ref]):
        return {"ok": False, "error": "book, action, target, thesis_ref required"}
    if len(justification.strip()) < 40:
        return {"ok": False, "error": "justification must be >= 40 characters (empty why = no decision)"}
    argv = [
        "decide", "--book", book, "--action", action, "--target", target,
        "--thesis-ref", thesis_ref, "--justification", justification,
    ]
    if args.get("from_section"):
        argv += ["--from", args["from_section"]]
    if args.get("to_section"):
        argv += ["--to", args["to_section"]]
    if args.get("decided_by"):
        argv += ["--decided-by", args["decided_by"]]
    return _run_factory(argv)


def new_book(args: dict) -> dict:
    slug = args.get("slug")
    if not slug:
        return {"ok": False, "error": "slug required"}
    if args.get("thesis"):
        # allow bare spec name
        th = args["thesis"]
        if not Path(th).is_absolute() and not (ROOT / th).is_file():
            cand = ROOT / "specs" / th
            if cand.is_file():
                th = str(cand)
            elif (ROOT / "specs" / f"{th}.thesis.json").is_file():
                th = str(ROOT / "specs" / f"{th}.thesis.json")
        argv = ["new-book", "--slug", slug, "--thesis", th]
        return _run_factory(argv)
    # flag-style
    if not args.get("claim") or not args.get("sections"):
        return {"ok": False, "error": "either thesis path/spec OR claim + sections (list of id:purpose)"}
    argv = ["new-book", "--slug", slug, "--claim", args["claim"], "--template", args.get("template") or "prayer-book"]
    for s in args["sections"]:
        argv += ["--section", s]
    if args.get("title"):
        argv += ["--title", args["title"]]
    if args.get("max_pages") is not None:
        argv += ["--max-pages", str(args["max_pages"])]
    if args.get("style"):
        argv += ["--style", args["style"]]
    if args.get("series"):
        argv += ["--series", args["series"], "--volume", str(args.get("volume") or 1)]
    return _run_factory(argv)


def stage(args: dict) -> dict:
    book = args.get("book")
    to = args.get("to")
    if not book or not to:
        return {"ok": False, "error": "book and to required (content|structure|formatting|build)"}
    if to not in ("content", "structure", "formatting", "build"):
        return {"ok": False, "error": "to must be content|structure|formatting|build"}
    return _run_factory(["stage", "--book", book, "--to", to])


def audio_plan(args: dict) -> dict:
    book = args.get("book")
    if not book:
        return {"ok": False, "error": "book required"}
    return _run_factory(["audio", "--book", book])


def epub(args: dict) -> dict:
    book = args.get("book")
    if not book:
        return {"ok": False, "error": "book required"}
    # EPUB can take a while — still bounded; package is for after build
    return _run_factory(["epub", "--book", book], timeout=120)


def package(args: dict) -> dict:
    book = args.get("book")
    if not book:
        return {"ok": False, "error": "book required"}
    return _run_factory(["package", "--book", book], timeout=120)


def quote_preview(args: dict) -> dict:
    """Draft-only quote cards — never a ship approval."""
    text = args.get("text")
    ref = args.get("ref")
    output = args.get("output") or "/tmp/opencode/quote-preview"
    if not text or not ref:
        return {"ok": False, "error": "text and ref required"}
    argv = ["quote", "--text", text, "--ref", ref, "--output", output]
    if args.get("layer"):
        argv += ["--layer", args["layer"]]
    if args.get("gate_id"):
        argv += ["--gate-id", args["gate_id"]]
    if args.get("book"):
        # existing book entry path via --ref entry id still works
        pass
    return _run_factory(argv, timeout=120)


# ── Tool schemas ────────────────────────────────────────────────────

def _t(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    }


STR = {"type": "string"}
BOOL = {"type": "boolean"}

TOOLS: dict[str, dict] = {
    "factory_overview": _t(
        "factory_overview",
        "Start here. Returns bookfactory goal, lanes, milestones, doc map, and the non-negotiable laws (stage order, no retyped text, decision log, fail-closed gate).",
        {},
    ),
    "list_lanes": _t(
        "list_lanes",
        "List every lane with registry stage, project stage, thesis title, entry count, max_pages, and whether prints/ exists.",
        {},
    ),
    "check_lane": _t(
        "check_lane",
        "Run the only gate (check.py). Returns canonical flag + full output. Omit lane to check the whole registry. BLOCKED = not shippable; DUE-LATER = worklist for upcoming stages.",
        {"lane": STR},
    ),
    "next_actions": _t(
        "next_actions",
        "Agent worklist: blocking problems, due-later problems, open milestones, and stage law. Call after any content change.",
        {"lane": STR},
    ),
    "read_thesis": _t(
        "read_thesis",
        "Read a thesis: book lane thesis (book=) or a pre-lane spec (spec=learn-sanskrit or learn-sanskrit.thesis.json) or raw path.",
        {"book": STR, "spec": STR, "path": STR},
    ),
    "list_specs": _t(
        "list_specs",
        "List specs/, templates/, and styles/ available to instantiate.",
        {},
    ),
    "read_template": _t(
        "read_template",
        "Read a genre template JSON (entry_anatomy, layout, provenance, products, inclusion/exclusion).",
        {"id": STR, "template": STR},
        ["id"],
    ),
    "read_entries": _t(
        "read_entries",
        "Read prints/<book>/entries.json (all entries or one by entry_id).",
        {"book": STR, "entry_id": STR},
        ["book"],
    ),
    "read_book": _t(
        "read_book",
        "Read prints/<book>/book.json (meta, sections, trim, target_pages).",
        {"book": STR},
        ["book"],
    ),
    "read_decisions": _t(
        "read_decisions",
        "Read projects/<book>/decisions.jsonl — every construction change with thesis_ref + justification.",
        {"book": STR},
        ["book"],
    ),
    "read_docs": _t(
        "read_docs",
        "Read a root markdown doc: FACTORY-SPEC | BOOKS | PIPELINE | AUTONOMY | AGENTS | CANDIDATES (with or without .md).",
        {"doc": STR, "name": STR},
        ["doc"],
    ),
    "read_file": _t(
        "read_file",
        "Read any file under bookfactory (relative path, no ..). Set allow_translations=true to also read translation-work relative paths.",
        {"path": STR, "allow_translations": BOOL},
        ["path"],
    ),
    "list_dir": _t(
        "list_dir",
        "List a directory under bookfactory (relative path).",
        {"path": STR},
    ),
    "inspect_verse": _t(
        "inspect_verse",
        "factory inspect: exact translation-layer verse + gate state. text + exact ref (e.g. tsa-a01-v01 or bh-p02). Never guess refs from verse numbers.",
        {"text": STR, "ref": STR, "layer": STR, "gate_id": STR, "allow_translations": BOOL},
        ["text", "ref"],
    ),
    "read_rule_boxes": _t(
        "read_rule_boxes",
        "Read foundational rule boxes for a lesson-book (default learn-sanskrit).",
        {"book": STR},
    ),
    "decide": _t(
        "decide",
        "Append a justified construction decision. action: add-section|remove-section|add-entry|remove-entry|move-entry|retire-entry|replace-entry|declare-structure. justification >=40 chars; thesis_ref must resolve into the thesis (e.g. exclusion/0, structure).",
        {
            "book": STR,
            "action": STR,
            "target": STR,
            "thesis_ref": STR,
            "justification": STR,
            "from_section": STR,
            "to_section": STR,
            "decided_by": STR,
        },
        ["book", "action", "target", "thesis_ref", "justification"],
    ),
    "new_book": _t(
        "new_book",
        "Scaffold a new lane. Prefer thesis= (path or specs name e.g. learn-sanskrit). Or claim + sections (id:purpose list) + template.",
        {
            "slug": STR,
            "thesis": STR,
            "template": STR,
            "claim": STR,
            "title": STR,
            "sections": {"type": "array", "items": STR},
            "max_pages": {"type": "integer"},
            "style": STR,
            "series": STR,
            "volume": {"type": "integer"},
        },
        ["slug"],
    ),
    "stage": _t(
        "stage",
        "Advance a lane stage (verified; failing checks refuse forward moves). to: content|structure|formatting|build. PDF is LAST.",
        {"book": STR, "to": STR},
        ["book", "to"],
    ),
    "audio_plan": _t(
        "audio_plan",
        "Write prints/<book>/audio-plan.json (NO API calls / no Fish render).",
        {"book": STR},
        ["book"],
    ),
    "epub": _t(
        "epub",
        "Build+validate reflowable EPUB3 for a book (after content exists).",
        {"book": STR},
        ["book"],
    ),
    "package": _t(
        "package",
        "Assemble customer package (EPUB + PDF + audio + sha256 manifest) — only after build outputs exist.",
        {"book": STR},
        ["book"],
    ),
    "quote_preview": _t(
        "quote_preview",
        "DRAFT quote postcard/social previews (watermarked, never a ship approval).",
        {"text": STR, "ref": STR, "output": STR, "layer": STR, "gate_id": STR},
        ["text", "ref"],
    ),
}


HANDLERS: dict[str, Callable[[dict], dict]] = {
    "factory_overview": factory_overview,
    "list_lanes": list_lanes,
    "check_lane": check_lane,
    "next_actions": next_actions,
    "read_thesis": read_thesis,
    "list_specs": list_specs,
    "read_template": read_template,
    "read_entries": read_entries,
    "read_book": read_book,
    "read_decisions": read_decisions,
    "read_docs": read_docs,
    "read_file": read_file,
    "list_dir": list_dir,
    "inspect_verse": inspect_verse,
    "read_rule_boxes": read_rule_boxes,
    "decide": decide,
    "new_book": new_book,
    "stage": stage,
    "audio_plan": audio_plan,
    "epub": epub,
    "package": package,
    "quote_preview": quote_preview,
}


def handle(name: str, arguments: dict) -> dict:
    if name not in HANDLERS:
        return {"ok": False, "error": f"unknown tool {name}", "available": sorted(HANDLERS)}
    try:
        return HANDLERS[name](arguments or {})
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "tool": name,
            "traceback": traceback.format_exc(limit=5),
        }
