#!/usr/bin/env bash
# Install and start the bookfactory MCP HTTP service + a Cloudflare tunnel.
#
# Named tunnel (stable hostname, recommended):
#   put TUNNEL_TOKEN in /root/.config/bookfactory/tunnel.env first
#   (see deploy/tunnel.env.example). Target hostname: bookfactory.sanskrit.help
#
# Run as root from the repo root:  sudo deploy/install-mcp-tunnel.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR=/root/.config/bookfactory
ENV_FILE="$ENV_DIR/mcp.env"
TUNNEL_ENV="$ENV_DIR/tunnel.env"
CLOUDFLARED=/usr/local/bin/cloudflared

if [[ $EUID -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi
if [[ ! -x "$CLOUDFLARED" ]]; then
  echo "missing $CLOUDFLARED (install cloudflared first)" >&2
  exit 1
fi

install -d -m 700 "$ENV_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  install -m 600 "$REPO/deploy/mcp.env.example" "$ENV_FILE"
  TOKEN="bf$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)"
  sed -i "s|^BOOKFACTORY_MCP_TOKEN=.*|BOOKFACTORY_MCP_TOKEN=$TOKEN|" "$ENV_FILE"
  echo "wrote $ENV_FILE (token generated)"
fi

install -m 644 "$REPO/deploy/bookfactory-mcp.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now bookfactory-mcp.service

if [[ -f "$TUNNEL_ENV" ]]; then
  install -m 644 "$REPO/deploy/bookfactory-mcp-tunnel.service" /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable --now bookfactory-mcp-tunnel.service
  sleep 8
  HOST="$(grep -m1 -o 'bookfactory\.[a-z0-9.-]*' "$REPO/deploy/bookfactory-mcp-tunnel.service" || echo 'bookfactory.sanskrit.help')"
else
  echo "no $TUNNEL_ENV — service is local-only (127.0.0.1:8932)."
  echo "Create a named tunnel, copy deploy/tunnel.env.example -> $TUNNEL_ENV,"
  echo "then re-run this script. See CHATGPT-PLUGIN.md § Connect."
  HOST="127.0.0.1:8932"
fi

sleep 2
systemctl --no-pager --lines=0 status bookfactory-mcp.service || true
echo
echo "token:  $(grep '^BOOKFACTORY_MCP_TOKEN=' "$ENV_FILE" | cut -d= -f2-)"
echo "url:    https://${HOST}/mcp?token=<token>"
echo "logs:   /var/log/bookfactory-mcp.log  /var/log/bookfactory-tunnel.log"
