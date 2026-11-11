# HANDOVER — bookfactory remote MCP

**Written:** 2026-11-11 · **Branch/PR:** `feat/remote-mcp` → PR #2
<https://github.com/prx0r/bookfactory/pull/2> · **Base:** `master` @ `38ad2a5`

Read this first if you are picking up the remote-MCP work. For the factory
itself (thesis → decisions → gate → books), read `AGENTS.md` and
`bf_mcp/README.md`.

---

## TL;DR — what is live right now

The factory's 22-tool MCP is served over **Streamable HTTP** at a **stable,
permanent hostname**:

```
https://bookfactory.sanskrit.help/mcp?token=<BOOKFACTORY_MCP_TOKEN>
```

- Runs on this hub, `127.0.0.1:8932`, under systemd (`enabled` at boot).
- Public edge: named Cloudflare Tunnel `bookfactory`
  (id `a18b49d9-03ba-411f-a2fe-1c9727270c82`), DNS
  `bookfactory.sanskrit.help` → `<id>.cfargotunnel.com` (proxied).
- Auth: shared secret `BOOKFACTORY_MCP_TOKEN` via `Authorization: Bearer` or
  `?token=`. If unset, the service is open (localhost only).
- **22 tools** verified through the public URL. `check_lane practical-prayers`
  = `canonical:true`, `exit:0`.
- No secret is committed. Tokens live in `/root/.config/bookfactory/`.

R2 **cannot** host this (storage only, no compute). See § Permanence.

---

## Files changed in this work

| File | What |
|---|---|
| `bf_mcp/server.py` | `--serve-http` Streamable HTTP front-end; shares `dispatch()` with stdio |
| `bf_mcp/tools.py` | `BOOKFACTORY_ROOT` env override |
| `deploy/bookfactory-mcp.service` | HTTP service, `127.0.0.1:8932`, `Restart=always` |
| `deploy/bookfactory-mcp-tunnel.service` | named tunnel `cloudflared tunnel run --token` |
| `deploy/install-mcp-tunnel.sh` | installer (named tunnel if `tunnel.env` present) |
| `deploy/mcp.env.example`, `deploy/tunnel.env.example` | env templates |
| `CHATGPT-PLUGIN.md` | connect steps, 22 tools, full chain, autonomy, ops, Apps SDK |
| `docs/REMOTE-MCP-PLAN.md` | architecture, acceptance criteria, 10 todos, permanence |
| `bf_mcp/README.md`, `AGENTS.md` | document the HTTP mode |
| `HANDOVER.md` | this file |

---

## Secrets & state (paths only — do not commit values)

| What | Where |
|---|---|
| MCP shared secret | `/root/.config/bookfactory/mcp.env` → `BOOKFACTORY_MCP_TOKEN` |
| Tunnel token | `/root/.config/bookfactory/tunnel.env` → `TUNNEL_TOKEN` |
| Cloudflare API token + account id | `/root/.config/goodgrails/cloudflare.env` |
| R2 creds | `/root/.r2-env`, `/root/.r2-s3.env`; rclone `r2:` |
| Factory root | `/home/box/repos/bookfactory` (env `BOOKFACTORY_ROOT`) |
| Translation layers | `/home/box/repos/translation-work` (`BOOKFACTORY_TRANSLATIONS`) |
| Python | `/home/box/Documents/patala/.venv/bin/python3` (`BOOKFACTORY_PY`) |

If `/root/.config/bookfactory/mcp.env` is missing, regenerate:
`bf` + 40 random alnum, then `systemctl restart bookfactory-mcp`.

---

## How to connect a client

**ChatGPT:** Settings → Connectors → Advanced → Developer mode → Add custom
connector → URL above, auth “No auth” → enable in chat.

**Claude:**
```bash
claude mcp add --transport http bookfactory \
  "https://bookfactory.sanskrit.help/mcp?token=<TOKEN>"
```

**Local stdio:** `python3 bf_mcp/server.py`

---

## Operations

```bash
systemctl status bookfactory-mcp bookfactory-mcp-tunnel
journalctl -u bookfactory-mcp -n 50
tail -f /var/log/bookfactory-mcp.log /var/log/bookfactory-tunnel.log
systemctl restart bookfactory-mcp          # after tools.py changes
systemctl is-enabled bookfactory-mcp bookfactory-mcp-tunnel   # must be enabled
```

Health check (expect `405` — process is up, no SSE):
```bash
curl -s -o /dev/null -w '%{http_code}\n' https://bookfactory.sanskrit.help/mcp
```

Full smoke (expect `22`):
```bash
TOK=$(grep '^BOOKFACTORY_MCP_TOKEN=' /root/.config/bookfactory/mcp.env | cut -d= -f2-)
curl -s -X POST "https://bookfactory.sanskrit.help/mcp?token=$TOK" \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["result"]["tools"]))'
```

---

## Architecture (why this shape)

bookfactory reads the filesystem and shells out to `factory.py` / `check.py`
with the patala venv. It cannot run on Cloudflare Workers. So: a small stdlib
HTTP server locally + a Cloudflare tunnel. HTTP and stdio share **one**
`dispatch()`, so they cannot drift. Adding a tool = handler in `tools.py` +
entry in `TOOLS` + `HANDLERS`; both transports update together.

Transport details: stateless `POST` (message or batch) → JSON; notifications →
`202`; `GET` → `405`; `OPTIONS` → `204` + CORS; `initialize` echoes the client's
`protocolVersion` (2024-11-05 / 2025-06-18 both work).

---

## Permanence — the honest answer

1. **Stable URL:** done via a named tunnel. Survives restarts and reboots; the
   hostname never changes.
2. **Always-on:** the tunnel connector runs on the hub, so the endpoint is only
   up while the hub is on. For true 24/7, run the **same two units on debz**
   (Hetzner, 4 cores / 8 GB / 80 GB, up 6 weeks): clone the repo, create the
   venv deps, copy `mcp.env` + `tunnel.env`, enable the units, and either point
   the existing named tunnel there or create a second one. Edits then land on
   that host and reach `master` as PRs.
3. **R2:** object storage — good for backups, built packages and artefacts
   (`r2:opencode2-root/packages/`), optionally served via a custom domain. It
   **cannot execute** Python or `factory.py`, so it is not the server.

---

## Next steps (in order)

1. **Cloudflare Access / MCP OAuth** in front of the URL before sharing beyond
   the owner (the token-in-URL is the only gate today).
2. Decide **hub vs debz** for uptime. If debz: migrate the two units + env files,
   verify `bookfactory.sanskrit.help` still resolves to a healthy tunnel, and
   confirm PDF build deps (Chrome) exist there.
3. Optionally wire **R2 backups** of `prints/` + `projects/` (artefact
   persistence, not compute).
4. Keep the **six human gates** intact when extending tools: structure law,
   taste, rights, spend, ship, gate weakening (`AUTONOMY.md`).

---

## Guardrails (do not break)

- `check.py` is the only gate; never weaken it to pass.
- PDF/build is last; `stage` verifies forward moves.
- Every construction change goes through `decide` (≥40-char justification,
  resolvable `thesis_ref`).
- Never retype content; read pinned translation layers; never write Sanskrit.
- Path jail: reads stay inside the repo (or `translation-work` on request).
- No render/ffmpeg in tools.
- **Never delete** volumes/repos/data without the owner's written approval.
- Repo is **public** — no secrets in commits; only `<token>` placeholders.
