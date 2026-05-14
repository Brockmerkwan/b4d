#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/.local/state/b4d"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/discord_notify.log"

ts(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log(){ printf "[%s] %s\n" "$(ts)" "$*" | tee -a "$LOG"; }

WEBHOOK="${B4D_DISCORD_WEBHOOK:-}"
[[ -n "$WEBHOOK" ]] || { log "ERROR: B4D_DISCORD_WEBHOOK not set"; exit 1; }

MSG="${*:-B4D ping.}"
payload=$(printf '{"content": "%s"}' "$(printf '%s' "$MSG" | sed 's/"/\\"/g')")

curl -fsS -X POST \
  -H "Content-Type: application/json" \
  -d "$payload" \
  "$WEBHOOK" >/dev/null

log "sent"
