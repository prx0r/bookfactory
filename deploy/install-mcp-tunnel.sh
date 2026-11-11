#!/usr/bin/env bash
# Install and start the bookfactory MCP HTTP service + Cloudflare quick tunnel.
# Run as root from the repo root:  sudo deploy/install-mcp-tunnel.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR=/root/.config/bookfactory
ENV_FILE="$ENV_DIR/mcp.env"
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
  # generate a real token unless the placeholder was deliberately emptied
  TOKEN="bf$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)"
  sed -i "s|^BOOKFACTORY_MCP_TOKEN=.*|BOOKFACTORY_MCP_TOKEN=$TOKEN|" "$ENV_FILE"
  echo "wrote $ENV_FILE (token generated)"
fi

install -m 644 "$REPO/deploy/bookfactory-mcp.service" /etc/systemd/system/
install -m 644 "$REPO/deploy/bookfactory-mcp-tunnel.service" /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now bookfactory-mcp.service
systemctl enable --now bookfactory-mcp-tunnel.service

sleep 3
systemctl --no-pager --lines=0 status bookfactory-mcp.service || true
sleep 8
HOSTURL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /var/log/bookfactory-tunnel.log | tail -1 || true)"
echo
echo "token:  $(grep '^BOOKFACTORY_MCP_TOKEN=' "$ENV_FILE" | cut -d= -f2-)"
echo "url:    ${HOSTURL}/mcp?token=<token>"
echo "logs:   /var/log/bookfactory-mcp.log  /var/log/bookfactory-tunnel.log"
