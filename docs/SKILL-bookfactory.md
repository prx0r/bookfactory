---
name: bookfactory
description: Navigate and operate the bookfactory publishing monorepo (thesis → decision log → staged gate → print products). Use when creating, checking, or shipping books, reading specs/templates/theses, appending decisions, advancing stages, or working on Learn Sanskrit / Practical Prayers / Tantric Prayer / queued lanes. Prefer the bookfactory MCP tools when available; this skill is the map and the laws.
---

# bookfactory — agent map

**Root:** `/home/box/repos/bookfactory`  
**Upstream texts:** `/home/box/repos/translation-work`  
**Gate:** `check.py` (exit 0 = canonical)  
**CLI:** `factory.py`  
**MCP:** stdio server `bf_mcp/server.py` (name: `bookfactory`) — full tool docs: `bf_mcp/README.md`

## Read this first

1. `AGENTS.md` — repo rules  
2. `FACTORY-SPEC.md` — product law  
3. `BOOKS.md` — full system (template → thesis → decisions → stages → products)  
4. `PIPELINE.md` — commands + current blockers  
5. `AUTONOMY.md` — what may run without a human  

If resuming a lane: `REGISTRY.json` + `projects/<book>/project.json` + latest `check.py <book>`.

## Explainer formula (EXPLAINER.md) — 2026-11-07

Facing pages follow **`EXPLAINER.md`** (PP editorial handoff → house law):

| Field | Carries |
|-------|---------|
| `brief` | IN ONE SENTENCE (literal proposition) |
| `logic` | THE TURN (recognitional insight) |
| `howto` | **When:** … **Practice:** … **Return:** … |
| `sign` | ordinary RETURN only — never a somatic test |

**No** feeling-checks, chest-warms, “sign of success,” or promised removal of
illness/anxiety. Pocket lines cut from longer verses = **EXTRACT** labels.
Speech acts stay distinct (mantra vs prayer vs hymn vs practice verse).

Source package: `prints/practical-prayers/editorial/` (overlay, QA CSV,
gold pages, `apply_preview.py`). English overlay = **owner approval** before
merge. Source QA BLOCKs forbid ship regardless of copy.

Metrics that justified the change: somatic-promise entries 23→0; When/Return
structure 0→36; guide length −38% (`editorial/WHY_BETTER.md`).

## MCP tools (when connected)

| Tool | Use |
|------|-----|
| `factory_overview` | **Start here** — goal, lanes, milestones, doc map, laws |
| `list_lanes` | All lanes + stage + counts |
| `check_lane` | Run the gate (`lane` optional) |
| `next_actions` | Blocking / due-later worklist + open milestones |
| `read_thesis` | `book=` lane thesis or `spec=` pre-lane (`learn-sanskrit`) |
| `list_specs` / `read_template` | specs, templates, styles |
| `read_entries` / `read_book` / `read_decisions` | prints + project state |
| `read_docs` | FACTORY-SPEC, BOOKS, PIPELINE, AUTONOMY, AGENTS |
| `read_file` / `list_dir` | Any relative path under the factory |
| `inspect_verse` | Exact translation-work verse + gate (never guess refs) |
| `read_rule_boxes` | lesson-book foundational rules (default `learn-sanskrit`) |
| `decide` | Append decision (justification ≥40 chars + `thesis_ref`) |
| `new_book` | Scaffold lane (`thesis=specs/...` preferred) |
| `stage` | Advance content→structure→formatting→**build last** |
| `audio_plan` / `epub` / `package` / `quote_preview` | Products (quote = DRAFT only) |

**Typical agent loop**

1. `factory_overview` → `list_lanes`  
2. `next_actions` on the target lane  
3. Read thesis + entries + decisions before editing  
4. Edit content **upstream** (translation-work or `prints/<book>/entries.json` with `source_path` files) — no retyped Sanskrit  
5. `check_lane` until content/structure/formatting clear  
6. `stage` only when the prior stage is clean  
7. PDF/`build` is **last**; never invent a ship command  

## Laws (fail closed)

1. **Stage order:** content → structure → formatting → build. PDF last.  
2. **No retyped text.** Strings from layers/sources; fix upstream; rebuild.  
3. **Deva from IAST at build** — never hand-written Devanagari bytes.  
4. **Decisions:** `decide` needs `justification` ≥40 chars and a resolvable `thesis_ref`. Append-only (`superseded`, never edit history).  
5. **Template inclusion/exclusion must be inherited** — dropping a template rule blocks the gate.  
6. **`GATE.json` BLOCKED** = verse does not ship without recorded owner adjudication in `project.json`.  
7. **Quote previews are DRAFT · NOT FOR SALE** — hashes ≠ approvals.  
8. **Copyright:** our English only; Lakshmanjoo/Dyczkowski prose never printed beyond brief attributed quote.  
9. **Rights:** GRETIL NC / SanskritDocuments commercial restrictions — no commercial ship until cleared (see `PIPELINE.md`, lesson `RIGHTS.md`).  
10. **One prayer, one book** — cross-book id/IAST uniqueness is gate-enforced (reference volumes own full texts; textbooks quote with attribution).

## Key paths

```
projects/<book>/thesis.json      # what the book IS
projects/<book>/decisions.jsonl  # why every change happened
projects/<book>/project.json     # stage + max_pages + adjudications
prints/<book>/book.json          # sections, trim, target_pages
prints/<book>/entries.json       # content (anatomy per template)
templates/<genre>.json           # genre law
specs/*.thesis.json              # pre-lane theses (e.g. learn-sanskrit)
schemas/*.json                   # fail-closed validators
```

## Learn Sanskrit vol. I (current teaching book)

- Spec thesis: `specs/learn-sanskrit.thesis.json`  
- Gold standard: `specs/learn-sanskrit.thesis.md`  
- Curriculum cut: `specs/learn-sanskrit-curriculum.md` (**10 lessons, 108pp, few rule boxes**)  
- Lane: `projects/learn-sanskrit/` · prints: `prints/learn-sanskrit/`  
- Preview: `prints/learn-sanskrit/index.html` + `lesson-01.html`…`lesson-10.html`  
- Gate: content-stage canonical; formatting/build still DUE-LATER (fonts, per-entry ship handoff, PDF)

## CLI (equivalent)

```bash
cd /home/box/repos/bookfactory
/home/box/Documents/patala/.venv/bin/python3 check.py                 # all lanes
/home/box/Documents/patala/.venv/bin/python3 check.py learn-sanskrit
/home/box/Documents/patala/.venv/bin/python3 factory.py decide --book B --action A --target T \
  --thesis-ref R --justification "..."
/home/box/Documents/patala/.venv/bin/python3 factory.py new-book --thesis specs/X.thesis.json --slug x
/home/box/Documents/patala/.venv/bin/python3 factory.py stage --book B --to structure
```

## Registration (OpenCode only)

- `~/.config/opencode/mcp.json` + `opencode.jsonc` → `mcp.bookfactory`
- Skill: `~/.config/opencode/skills/bookfactory/SKILL.md`
- Smoke: `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | /home/box/Documents/patala/.venv/bin/python3 /home/box/repos/bookfactory/bf_mcp/server.py`

## When MCP is down

Fall back to CLI in `AGENTS.md` / this skill. Do not invent tools. Long ops (>10s) → background job + log + notify (repo NEVER BLOCK rules). Heavy **media** renders stay on the fleet (Global Rule 8); book PDF via headless Chrome only at build stage as documented in BOOKS.md.
