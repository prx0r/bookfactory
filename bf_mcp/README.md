# bookfactory MCP — agent interface to the publishing factory

**What it is:** a JSON-RPC Model Context Protocol server that lets an agent
(OpenCode, ChatGPT, Claude, any MCP client) *read* and *act on* the bookfactory
without shell-guessing paths. Two front-ends share one tool surface: **stdio**
(local) and **Streamable HTTP** (remote/connectors). Same wire format as
`neuro_mix/mcp/server.py` for stdio.

**Root:** `/home/box/repos/bookfactory` (override with `BOOKFACTORY_ROOT`)  
**Entry:** `bf_mcp/server.py` · tools in `bf_mcp/tools.py`  
**Python:** `/home/box/Documents/patala/.venv/bin/python3` (jsonschema, etc.)

---

## Why this exists

The factory already has a strict law: thesis → append-only decisions → staged
gate (`check.py`) → PDF last. An agent that only has Bash will:

- invent paths (`prints/` vs `projects/` vs `specs/`)
- skip the gate, or treat a preview as a ship approval
- retype Sanskrit instead of reading translation-work layers
- advance stages out of order

The MCP makes the **right move the easy move**: one tool call, schema-shaped
arguments, fail-closed errors, same semantics as the CLI.

---

## House style (read before editing English or layout)

See **[`../STYLE.md`](../STYLE.md)** — owner translation voice (sharp Trika English,
Gītā 4.24 model) + **prayer page as full-page art** (centred, Devanagari maximised).
Also `EXPLAINER.md` for facing-page guide fields.

## Register (OpenCode only)

Already wired on this box:

```jsonc
// ~/.config/opencode/mcp.json  (and opencode.jsonc)
"bookfactory": {
  "type": "local",
  "command": [
    "/home/box/Documents/patala/.venv/bin/python3",
    "/home/box/repos/bookfactory/bf_mcp/server.py"
  ],
  "enabled": true
}
```

**Do not register with Hermes** (owner ruling 2026-11-07).

Companion skill (agent map + laws):  
`~/.config/opencode/skills/bookfactory/SKILL.md`  
(copy of the operational map also lives in repo docs: `AGENTS.md` § MCP).

Restart OpenCode (new session) after config changes so tools load.

---

## Remote / HTTP mode

The same tools are served over stateless **Streamable HTTP** for remote agents
(ChatGPT connectors, Claude, etc.):

```bash
BOOKFACTORY_MCP_TOKEN=<secret> \
  /home/box/Documents/patala/.venv/bin/python3 bf_mcp/server.py \
  --serve-http --host 127.0.0.1 --port 8932
```

- `POST /mcp` — one JSON-RPC message or batch → JSON (notifications → `202`).
- `GET /mcp` — `405` (no server-initiated SSE; clients POST).
- `OPTIONS` — `204` + CORS.
- Auth: `Authorization: Bearer <token>` or `?token=<token>` when
  `BOOKFACTORY_MCP_TOKEN` is set; open if unset (localhost default).
- `initialize` echoes the client's `protocolVersion` (2024-11-05 / 2025-06-18).

Deployment units and an installer live in `deploy/`. Connect steps, the full
chain, autonomy bounds and ops are in **[`../CHATGPT-PLUGIN.md`](../CHATGPT-PLUGIN.md)**;
architecture and the 10 todos are in
**[`../docs/REMOTE-MCP-PLAN.md`](../docs/REMOTE-MCP-PLAN.md)**.

---

## Smoke tests

```bash
# list tools (expect 22)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | /home/box/Documents/patala/.venv/bin/python3 /home/box/repos/bookfactory/bf_mcp/server.py

# initialize + one call
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"factory_overview","arguments":{}}}' \
  | /home/box/Documents/patala/.venv/bin/python3 /home/box/repos/bookfactory/bf_mcp/server.py
```

Every `tools/call` returns MCP content `[{type:"text", text: <json>}]` where
the JSON is the tool result: `{"ok": true|false, ...}` plus tool-specific keys.
On handler exceptions: `{"ok": false, "error", "tool", "traceback"}`.

---

## Wire protocol (what the server speaks)

| Method | Behaviour |
|--------|-----------|
| `initialize` | `protocolVersion 2024-11-05`, `capabilities.tools`, serverInfo `bookfactory` 0.1.0 |
| `notifications/initialized` | ignored (no id — not a request) |
| `ping` | empty result |
| `tools/list` | all 22 tool defs with `inputSchema` |
| `tools/call` | dispatch to `bf_mcp.tools.handle(name, arguments)` |
| anything else | `{"unsupported": method}` inside a text content block |

Stdio: one JSON object per line, newline-delimited. HTTP: stateless POST of the
same messages (optional bearer/`?token=` auth). Both share `dispatch()`.

---

## Tool catalog (22)

### Orientation — start here

| Tool | Args | Returns | When |
|------|------|---------|------|
| **`factory_overview`** | — | goal, mode, lanes, milestones, docs map, layout, laws | First call every session |
| **`list_lanes`** | — | every lane: registry stage, project stage, thesis title, entry count, max_pages, has_prints | “what’s in the factory?” |
| **`next_actions`** | `lane?` | ordered worklist: `[BLOCKED]` → high, `[DUE-LATER]` → medium, open milestones, stage law, raw gate text | After any edit; before planning |
| **`check_lane`** | `lane?` | full `check.py` output + `canonical` / `blocking` / `exit` | Always before `stage` |

### Read (no side effects)

| Tool | Args | Returns |
|------|------|---------|
| **`read_thesis`** | `book` \| `spec` \| `path` | thesis JSON + path. `spec=learn-sanskrit` finds `specs/learn-sanskrit.thesis.json` |
| **`list_specs`** | — | `specs/`, `templates/`, `styles/` listings |
| **`read_template`** | `id` | genre template (entry_anatomy, layout, provenance, products, inclusion/exclusion) |
| **`read_entries`** | `book`, `entry_id?` | `prints/<book>/entries.json` (all or one) |
| **`read_book`** | `book` | `prints/<book>/book.json` (meta, sections, trim, target_pages) |
| **`read_decisions`** | `book` | parsed `decisions.jsonl` |
| **`read_docs`** | `doc` | root markdown: `FACTORY-SPEC` \| `BOOKS` \| `PIPELINE` \| `AUTONOMY` \| `AGENTS` \| `CANDIDATES` (± `.md`) |
| **`read_file`** | `path`, `allow_translations?` | any relative file under bookfactory; `allow_translations` also allows `translation-work/` relative paths |
| **`list_dir`** | `path` | directory listing (relative, no `..`) |
| **`inspect_verse`** | `text`, `ref`, `layer?`, `gate_id?` | `factory inspect` — exact layer record + gate. **Never guess refs from verse numbers** |
| **`read_rule_boxes`** | `book?` | foundational rule boxes (default `learn-sanskrit`) |

### Act (mutating — always fail-closed)

| Tool | Args | Notes |
|------|------|-------|
| **`decide`** | `book`, `action`, `target`, `thesis_ref`, `justification` ≥40 chars, `from_section?`, `to_section?`, `decided_by?` | Appends one line to `decisions.jsonl`. Actions: `add-section` · `remove-section` · `add-entry` · `remove-entry` · `move-entry` · `retire-entry` · `replace-entry` · `declare-structure`. `thesis_ref` must resolve (`exclusion/0`, `structure`, …) |
| **`new_book`** | `slug` + (`thesis` path/spec **or** `claim` + `sections[]` + `template`) | Prefer `thesis=learn-sanskrit` / `specs/x.thesis.json`. Scaffolds `projects/<slug>/` at stage `content` |
| **`stage`** | `book`, `to` ∈ content\|structure\|formatting\|build | Forward moves are **verified** — failing checks refuse. **PDF/build is last** |
| **`audio_plan`** | `book` | Writes `audio-plan.json` only — **no Fish API calls** |
| **`epub`** | `book` | Build + validate EPUB3 (timeout 120s) |
| **`package`** | `book` | Customer package + sha256 manifest (needs build outputs) |
| **`quote_preview`** | `text`, `ref`, `output?`, `layer?`, `gate_id?` | **DRAFT · NOT FOR SALE** watermarked cards — never a ship approval |

---

## Canonical agent loops

### A. Orient (read-only)

```
factory_overview
  → list_lanes
  → next_actions {lane: "learn-sanskrit"}
  → read_thesis {spec: "learn-sanskrit"}   # or {book: "practical-prayers"}
  → read_entries {book: "learn-sanskrit"}
```

### B. Change content (fail closed)

```
read_thesis + read_decisions          # know the law first
# edit upstream: translation-work layers OR prints/<book>/entries.json
# every entry needs source_path file inside the book dir
check_lane {lane: "..."}              # until content/structure clear
next_actions {lane: "..."}            # confirm no BLOCKED at your stage
```

### C. Record a construction decision

```
decide {
  book, action, target,
  thesis_ref: "inclusion/2",          # must resolve into thesis
  justification: "≥40 chars — full why"
}
check_lane
```

### D. Advance a stage

```
check_lane          # prior stage must be clean
stage {book, to: "structure"}         # refuses if gate fails
# … formatting …
stage {book, to: "build"}             # LAST — renders PDF via documented path
```

### E. Ship-adjacent (never automatic)

`epub` / `package` only after build artifacts exist.  
`quote_preview` is draft.  
Commercial ship still blocked on rights (GRETIL NC etc.) — see `PIPELINE.md`.

---

## Design rules (encoded in `tools.py`)

1. **Reads are in-process JSON** — fast, no subprocess.  
2. **Mutations shell out to `factory.py`** with the venv python — one code path with the CLI, same validation, same error strings.  
3. **Path safety:** `read_file` / `list_dir` reject absolute paths and `..`; must stay under bookfactory (or `translation-work` only when `allow_translations=true`).  
4. **No render/ffmpeg** in any tool — Global Rule 8 still applies to media; book PDF is the documented Chrome build path at `stage build` only.  
5. **No invented refs:** `inspect_verse` requires exact `text` + `ref`.  
6. **Justification floor:** `decide` refuses `< 40` characters.  
7. **Unknown tool** → `ok:false` + `available[]` list (never a silent no-op).

---

## Environment overrides

| Env | Default | Meaning |
|-----|---------|---------|
| `BOOKFACTORY_ROOT` | `/home/box/repos/bookfactory` | Factory root (paths + subprocess cwd) |
| `BOOKFACTORY_PY` | `/home/box/Documents/patala/.venv/bin/python3` | Python for `factory.py` / `check.py` subprocesses |
| `BOOKFACTORY_TRANSLATIONS` | `/home/box/repos/translation-work` | Upstream layers root |
| `BOOKFACTORY_MCP_TOKEN` | *(unset = open)* | Shared secret for `--serve-http` |

---

## File map

```
bf_mcp/
  README.md     ← this document
  __init__.py
  server.py     ← stdio + Streamable HTTP front-ends (shared dispatch)
  tools.py      ← 22 handlers + JSON schemas (TOOLS / HANDLERS / handle)
```

Docs that stay authoritative for *policy*: `FACTORY-SPEC.md`, `BOOKS.md`,
`PIPELINE.md`, `AUTONOMY.md`, `AGENTS.md`. This README is authoritative for
*the MCP surface*.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Tools missing in OpenCode | New session; confirm `mcp.json` + `opencode.jsonc`; `enabled: true` |
| `jsonschema missing` | Server uses venv python — don’t run `server.py` with system `python3` if you also call tools that subprocess factory (handlers already use `BOOKFACTORY_PY`) |
| `path escapes bookfactory root` | Use relative paths only; no leading `/`, no `..` |
| `justification must be >= 40 characters` | Write a real why; empty why = no decision |
| `thesis drops template inclusion rule` | Merge template inclusion/exclusion into the thesis before `check_lane` |
| `unknown tool` | `tools/list` for names; handlers are only those in `HANDLERS` |
| Want Hermes | **Don’t** — owner: OpenCode only |

---

## Version

- Server name: `bookfactory` · version `0.1.0`  
- Protocol: MCP `2024-11-05` (stdio) · Streamable HTTP stateless  
- Tool count: **22** (as of 2026-11-11)
- Remote: enabled (`--serve-http`)  
- Repo: https://github.com/prx0r/bookfactory
