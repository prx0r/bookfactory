# Remote MCP plan — bookfactory as an autonomous agent endpoint

Status: **live via Streamable HTTP + Cloudflare tunnel; stable in-repo HTTP mode
shipped on `feat/remote-mcp`.** Deployment for the repo's own systemd units is
in `deploy/`.

## Goal

Let a remote agent (ChatGPT connector/plugin, Claude, opencode, Hermes) drive the
**whole bookfactory chain** — not just the book: books, audiobooks, customer
packages and social/promo cards — while keeping every factory law intact.

```
translation layers → thesis → append-only decisions → staged gate
   → build (PDF, last) → EPUB → audio plan → customer package → quote/social cards
```

bookfactory is a **local-filesystem + subprocess** tool: it reads repo files and
shells out to `factory.py` / `check.py` / `compile.py` with the patala venv. It
cannot run on Cloudflare Workers, so the correct exposure is a local HTTP server
plus a tunnel — exactly the pattern used for the other MCPs on this box.

## Architecture

| Piece | Path / host |
|---|---|
| Tool surface | `bf_mcp/tools.py` (22 tools, `TOOLS` / `HANDLERS` / `handle`) |
| stdio front-end | `bf_mcp/server.py` (default) |
| Streamable HTTP front-end | `bf_mcp/server.py --serve-http --host 127.0.0.1 --port 8932` |
| systemd | `bookfactory-mcp.service` (`Restart=always`, enabled) |
| Public edge | `bookfactory-mcp-tunnel.service` (named tunnel → `bookfactory.sanskrit.help`) |
| State guarded | git repo `/home/box/repos/bookfactory` |

Why not bundle the Python SDK: the existing server is a dependency-free JSON-RPC
loop with a proven tool surface. The HTTP mode reuses the **same `dispatch()`**
as stdio, so stdio, HTTP and the CLI can never drift. No new runtime deps.

### Transport

Stateless Streamable HTTP: `POST` one JSON-RPC message (or a batch), get JSON
back; notifications → `202`; `GET` → `405` (no server-initiated SSE); `OPTIONS`
→ `204` + CORS. `initialize` echoes the client's `protocolVersion`, so both
`2024-11-05` and `2025-06-18` clients work.

### Auth

Optional shared secret `BOOKFACTORY_MCP_TOKEN`:

- `Authorization: Bearer <token>` for standard MCP clients;
- `?token=<token>` in the URL for the ChatGPT "no auth" connector UI.

If unset the server is open (local-only default). Fail-safe, not fail-closed —
this is a deliberate trade-off documented in `CHATGPT-PLUGIN.md`.

## The chain as tools

| Step | Tool(s) |
|---|---|
| Orient | `factory_overview`, `list_lanes`, `next_actions`, `check_lane` |
| Read the law | `read_thesis`, `read_decisions`, `read_docs`, `read_template`, `read_rule_boxes` |
| Read content | `read_entries`, `read_book`, `read_file`, `list_dir`, `inspect_verse`, `list_specs` |
| Change (gated) | `decide` (≥40-char justification), `new_book` |
| Advance | `stage` (`content→structure→formatting→build`, PDF last, verified) |
| Audiobook | `audio_plan` (writes `audio-plan.json`; **no Fish/API render**) |
| Ebook | `epub` |
| Customer product | `package` (EPUB + PDF + audio + sha256 manifest) |
| Social/promo | `quote_preview` (watermarked DRAFT; never a ship approval) |

Hard limits the tools keep: no retyped text; Devanagari transliterated at build;
path jail to the repo; `decide` refuses short justifications; `stage` refuses
forward moves that fail the gate; **PDF/build is last**.

## What "contribute autonomously" means

The agent may freely: orient, read, propose theses, append justified decisions,
scaffold lanes, write audio plans, build EPUBs, assemble packages, and draft
quote cards. The six things that never automate (from `AUTONOMY.md`) stay human:

1. structure law (what a book *is*)  4. spend (paid APIs / print runs)
2. taste (owner's voice/typography) 5. ship (publish / live listings)
3. rights (GRETIL NC, witnesses)    6. gate weakening (`check.py` stays honest)

So "autonomous" = it can take a lane from content to a built, packaged artefact
and stop at the human gates, with a full decision trail.

## Deploy (repo systemd units)

```bash
# 1. secrets
install -d -m 700 /root/.config/bookfactory
cat > /root/.config/bookfactory/mcp.env <<'EOF'
BOOKFACTORY_ROOT=/home/box/repos/bookfactory
BOOKFACTORY_TRANSLATIONS=/home/box/repos/translation-work
BOOKFACTORY_PY=/home/box/Documents/patala/.venv/bin/python3
BOOKFACTORY_MCP_TOKEN=<long random secret>
EOF
chmod 600 /root/.config/bookfactory/mcp.env

# 2. install units
sudo deploy/install-mcp-tunnel.sh

# 3. URL
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /var/log/bookfactory-tunnel.log | tail -1
```

## Acceptance criteria

- [x] `bf_mcp/server.py --serve-http` serves all 22 tools.
- [x] `initialize` + `tools/list` + `tools/call factory_overview` succeed.
- [x] `check_lane practical-prayers` returns `canonical: true`, `exit: 0`.
- [x] Public URL reachable; bare `GET` → `405` (server up).
- [x] systemd units active **and enabled at boot**; tunnel auto-restarts.
- [x] Named tunnel `bookfactory` → stable `bookfactory.sanskrit.help`.
- [ ] Cloudflare Access / OAuth in front of the public URL for wider sharing.

## 10 todos

1. Recon the chain + choose local-HTTP+tunnel over Worker (done).
2. Add `--serve-http` Streamable HTTP mode reusing `dispatch()` (done).
3. Optional `BOOKFACTORY_MCP_TOKEN` (bearer or `?token=`) (done).
4. `BOOKFACTORY_ROOT` env override in `tools.py` (done).
5. Ship `deploy/` systemd units + installer (done).
6. Add `CHATGPT-PLUGIN.md` (connect, 22 tools, file map, monitoring, auth) (done).
7. Update `bf_mcp/README.md` + `AGENTS.md` with the HTTP mode (done).
8. Smoke: 22 tools + `factory_overview` + `check_lane` through the public URL (done).
9. Commit `feat/remote-mcp`, push, open PR (done).
10. Named tunnel done (`bookfactory.sanskrit.help`); Access/OAuth before
    sharing widely (pending).

## Permanence

- **Stable URL:** named Cloudflare Tunnel (done). Survives restarts/reboots.
- **Always-on host:** the MCP is a local-filesystem + subprocess service, so it
  runs on a machine with the repo. The hub is a desktop; a 24/7 VPS (debz,
  8 GB/80 GB) can run the same two units for true uptime — clone the repo,
  install the venv deps, copy `mcp.env`/`tunnel.env`, enable the units, and
  point a tunnel at it. Edits then land on that VPS and reach `master` as PRs.
- **R2 is storage, not compute.** It cannot run Python or `factory.py`; it is
  the right place for backups, built packages and rendered artefacts (and can
  serve static files via a custom domain). Keep R2 for artefacts, not the MCP.
