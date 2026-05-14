#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/.local/state/b4d"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/idle_watch.log"

MSG="${B4D_IDLE_MSG:-B4D online. Listening from the shadows.}"

ts(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log(){ printf "[%s] %s\n" "$(ts)" "$*" | tee -a "$LOG"; }

log "Idle startup notify"
"$HOME/b4d/core/notify_discord.sh" "$MSG" || log "notify failed"

# park forever, no spam
while true; do
  sleep 86400
done
