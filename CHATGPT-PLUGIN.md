# ChatGPT plugin / connector — bookfactory

How a remote ChatGPT (or Claude / any MCP client) connects to bookfactory's MCP
and runs the whole chain: **books → audiobook plan → EPUB → customer package →
social/quote cards**, inside the factory gate.

Owner directive 2026-11-11: remote agents may drive bookfactory. This supersedes
the earlier "OpenCode only" note **for the remote MCP surface** (the Hermes ban
stands).

---

## 1. Connect it

Live endpoint (Streamable HTTP, stateless) — **stable named Cloudflare Tunnel**:

```
https://bookfactory.sanskrit.help/mcp?token=<BOOKFACTORY_MCP_TOKEN>
```

The hostname is permanent (named tunnel `bookfactory`, id
`a18b49d9-03ba-411f-a2fe-1c9727270c82`); it does not change when the service or
cloudflared restarts.

The shared secret lives in `/root/.config/bookfactory/mcp.env`
(`BOOKFACTORY_MCP_TOKEN`). Ask the owner for the value; it is deliberately **not**
committed to this repo.

### ChatGPT (Team/Pro/Enterprise)

1. **Settings → Connectors → Advanced → Developer mode** (on).
2. **Create / Add custom connector.**
3. Name: `bookfactory`
4. MCP server URL: the URL above (with `?token=…`).
5. Authentication: **No auth** (the token is already in the URL).
6. Save. In a chat, enable the `bookfactory` connector; ChatGPT will call
   `initialize` → `tools/list` (expect **22 tools**) → `tools/call`.

ChatGPT validates the server by POSTing `initialize` and `tools/list`. Bare
`GET /mcp` returns `405` by design (no server-initiated SSE); that is expected.

### Claude / Claude Code

```bash
claude mcp add --transport http bookfactory \
  "https://bookfactory.sanskrit.help/mcp?token=<TOKEN>"
```

### Local (no tunnel)

```bash
# stdio (local agents)
python3 bf_mcp/server.py

# or HTTP on localhost
BOOKFACTORY_MCP_TOKEN=<TOKEN> \
  python3 bf_mcp/server.py --serve-http --host 127.0.0.1 --port 8932
```

---

## 2. The 22 tools

| # | Tool | Kind | What it does |
|---|------|------|--------------|
| 1 | `factory_overview` | read | Goal, lanes, milestones, doc map, laws — **call first** |
| 2 | `list_lanes` | read | Every lane + stage, entry count, max_pages |
| 3 | `check_lane` | gate | Run `check.py`; `canonical` / `blocking` / `exit` |
| 4 | `next_actions` | read | Ordered worklist (`BLOCKED` / `DUE-LATER` / milestones) |
| 5 | `read_thesis` | read | Lane thesis or `specs/*.thesis.json` |
| 6 | `list_specs` | read | `specs/`, `templates/`, `styles/` |
| 7 | `read_template` | read | Genre template JSON |
| 8 | `read_entries` | read | `prints/<book>/entries.json` |
| 9 | `read_book` | read | `prints/<book>/book.json` |
| 10 | `read_decisions` | read | `decisions.jsonl` (append-only trail) |
| 11 | `read_docs` | read | `FACTORY-SPEC` / `BOOKS` / `PIPELINE` / `AUTONOMY` / `AGENTS` / `CANDIDATES` |
| 12 | `read_file` | read | Any repo-relative file (optional `translation-work`) |
| 13 | `list_dir` | read | Directory listing |
| 14 | `inspect_verse` | read | Exact layer verse + gate (`text` + `ref`) |
| 15 | `read_rule_boxes` | read | Foundational rule boxes |
| 16 | `decide` | **act** | Append a justified construction decision (≥40 chars) |
| 17 | `new_book` | **act** | Scaffold a lane from thesis/spec |
| 18 | `stage` | **act** | Advance `content→structure→formatting→build` (verified) |
| 19 | `audio_plan` | **act** | Write `audio-plan.json` (no paid render) |
| 20 | `epub` | **act** | Build + validate EPUB3 |
| 21 | `package` | **act** | EPUB + PDF + audio + sha256 manifest |
| 22 | `quote_preview` | **act** | Watermarked DRAFT quote/social cards |

All `tools/call` results are `[{type:"text", text:<json>}]`, where `<json>` is
`{"ok": true|false, ...}`.

---

## 3. Run the whole chain

```
factory_overview                      # orient
list_lanes / next_actions             # pick a lane + next step
read_thesis + read_decisions          # know the law before changing anything
# ...content work; every change gets a `decide` with thesis_ref + why...
check_lane {lane}                     # must be clean
stage {book, to:"structure"}          # verified; refuses on failure
stage {book, to:"formatting"}
stage {book, to:"build"}              # PDF is LAST
epub {book}                           # reflowable EPUB3
audio_plan {book}                     # audiobook plan (manifest, not audio)
package {book}                        # customer package + sha256
quote_preview {text, ref}             # social/promo drafts (watermarked)
```

Hard laws enforced by the tools themselves:

- No retyped text — content comes from pinned translation layers.
- Devanagari is transliterated at build; never retyped.
- `decide` refuses justifications under 40 characters; `thesis_ref` must resolve.
- `stage` forward moves are verified by `check.py`; PDF/build is last.
- Path jail: reads stay inside the repo (or `translation-work` on request).

---

## 4. What the agent may and may not do autonomously

**May:** orient, read everything, propose theses, append justified decisions,
scaffold lanes, advance verified stages, write audio plans, build EPUBs,
assemble packages, draft quote cards — and commit its work to a branch/PR.

**Must stop for a human** (from `AUTONOMY.md`):

1. **Structure law** — what a book *is*.
2. **Taste** — owner voice, typography, layout.
3. **Rights** — GRETIL NC, witnesses, permissions.
4. **Spend** — paid APIs, print runs.
5. **Ship** — publishing, live listings, `ship_approved`.
6. **Gate weakening** — `check.py` stays honest; never edit it to pass.

"Contribute autonomously" = take a lane to a built, packaged, validated artefact
with a full decision trail, then stop at these gates.

---

## 5. Add a tool (for contributors / ChatGPT editing its own surface)

1. Write a handler `def my_tool(a: dict) -> dict` in `bf_mcp/tools.py`.
2. Add a `_t(...)` entry to `TOOLS` (name, description, args, required).
3. Add `"my_tool": my_tool` to `HANDLERS`.
4. Smoke:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
     | python3 bf_mcp/server.py | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["result"]["tools"]))'
   ```
5. Restart `bookfactory-mcp.service`. The HTTP and stdio surfaces update
   together (one `dispatch()`).

Rules: reads stay in-process JSON; mutations shell out to `factory.py`; never add
a render/ffmpeg path; keep path jail and fail-closed errors.

---

## 6. Ops

```bash
systemctl status bookfactory-mcp bookfactory-mcp-tunnel
journalctl -u bookfactory-mcp -n 50
tail -f /var/log/bookfactory-mcp.log /var/log/bookfactory-tunnel.log
systemctl restart bookfactory-mcp
```

- **Token rotation:** edit `BOOKFACTORY_MCP_TOKEN` in
  `/root/.config/bookfactory/mcp.env`, then `systemctl restart bookfactory-mcp`.
  Update the connector URL.
- **Stable hostname:** `bookfactory.sanskrit.help` (named tunnel). It does not
  change on restart. Tunnel token: `/root/.config/bookfactory/tunnel.env`.
- `Restart=always` + `enabled` → both services come back after reboot.
- The tunnel connector runs on the hub, so the endpoint is up whenever the hub
  is powered on. For independence from the hub, run the same two units on a
  always-on VPS (see `docs/REMOTE-MCP-PLAN.md` § Permanence).

### Next step: Cloudflare Access

The named tunnel gives a stable URL. Put **Cloudflare Access** (or MCP OAuth) in
front before wider sharing; until then the shared secret in the URL is the only
gate — treat the URL as a password.

### Monitoring schedule (if run by a cron/agent)

| Frequency | Action |
|-----------|--------|
| every 5 min | `GET /mcp` → expect `405` (process alive) |
| every 15 min | `tools/call next_actions {}` → alert on new `BLOCKED` |
| hourly | `check_lane ""` (whole registry) → record canonical/exit |
| daily | `factory_overview` → confirm lanes/stages unchanged unexpectedly |

---

## 7. Apps SDK notes (if wrapping as a ChatGPT App)

Custom **connectors** use this MCP server directly — no manifest required. If you
also build a ChatGPT **App** (widget UI):

```jsonc
{
  "name": "bookfactory",
  "description": "Publishing factory: thesis → decisions → gate → book, EPUB, audio plan, package, social cards",
  "mcp": {
    "server_url": "https://<host>/mcp?token=<TOKEN>",
    "transport": "streamable_http"
  },
  "tools": ["factory_overview", "list_lanes", "check_lane", "next_actions", "..."]
}
```

The MCP server is deployment-agnostic; the same URL serves a connector or an App.
No server-side changes are needed to add an App UI later.

---

## 8. File map

```
bf_mcp/server.py   ← stdio + Streamable HTTP front-ends, shared dispatch()
bf_mcp/tools.py    ← 22 handlers + schemas (TOOLS / HANDLERS / handle)
deploy/            ← systemd units + installer + env example
docs/REMOTE-MCP-PLAN.md ← architecture, acceptance criteria, 10 todos
```

Authoritative policy docs stay `FACTORY-SPEC.md`, `BOOKS.md`, `PIPELINE.md`,
`AUTONOMY.md`, `AGENTS.md`.
