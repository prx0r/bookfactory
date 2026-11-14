# bookfactory MCP — agent interface to the publishing factory

**What it is:** a stdio JSON-RPC Model Context Protocol server that lets an
agent (OpenCode, any MCP client) *read* and *act on* the bookfactory without
shell-guessing paths. Same wire format as `neuro_mix/mcp/server.py`.

**Root:** `/home/box/repos/bookfactory`  
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

## Authenticated Streamable HTTP adapter

`bf_mcp/http_server.py` wraps the same canonical `bf_mcp.tools.HANDLERS` and
`TOOLS`; it does not replace or alter the local stdio server. It serves the MCP
endpoint at `/mcp` on loopback port 8950 by default. Install FastMCP and Uvicorn
in the service environment to run the HTTP adapter:

```bash
python3 -m pip install 'fastmcp>=2,<5' 'uvicorn>=0.30,<1'
```

Set two distinct random bearer secrets outside the repository:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Store one generated value as `BOOKFACTORY_MCP_READ_TOKEN` and a different one
as `BOOKFACTORY_MCP_WRITE_TOKEN` in a root-owned service environment file with
mode `0600`. Both values must be at least 32 characters. The server refuses
to start if either is missing, too short, or identical.

The read token can call only the explicitly classified read-only tools. The
write token can call those reads and the seven file- or record-changing tools:
`decide`, `new_book`, `stage`, `audio_plan`, `epub`, `package`, and
`quote_preview`. Unknown or malformed tool calls fail closed. These tokens
authenticate the MCP transport; factory thesis, stage, rights, and owner-signoff
gates still apply. Authentication is not an owner sign-off and must not be used
to automate publication or shipping.

Example service launch (adapt the interpreter and repository paths locally):

```ini
[Service]
EnvironmentFile=/etc/bookfactory/mcp.env
ExecStart=/home/box/Documents/patala/.venv/bin/python3 /home/box/repos/bookfactory/bf_mcp/http_server.py
Restart=always
```

Keep the app bound to `127.0.0.1`; terminate HTTPS at the existing reverse
proxy/tunnel and forward the `Authorization` header unchanged. Do not expose
port 8950 directly to the public network. A public ChatGPT deployment still
needs a properly managed secret per connector and a review of which agents are
allowed to hold the write token.

Focused authorization tests, which need only Python's standard library, run
with:

```bash
python3 -m unittest tests.test_mcp_http_auth -v
```

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

Stdio: one JSON object per line, newline-delimited. No HTTP. No auth (local only).

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
| `BOOKFACTORY_PY` | `/home/box/Documents/patala/.venv/bin/python3` | Python for `factory.py` / `check.py` subprocesses |
| `BOOKFACTORY_TRANSLATIONS` | `/home/box/repos/translation-work` | Upstream layers root |

---

## File map

```
bf_mcp/
  README.md     ← this document
  __init__.py
  server.py     ← stdio JSON-RPC loop (initialize / tools/*)
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
- Protocol: MCP `2024-11-05` stdio  
- Tool count: **22** (as of 2026-11-07)  
- Repo: https://github.com/prx0r/bookfactory
