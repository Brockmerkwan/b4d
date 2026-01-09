#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/b4d"
LOG_DIR="$STATE_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/b4d_pipe.log"

log(){ printf '%s - %s\n' "$(date '+%F %T')" "$*" >>"$LOG_FILE"; }

prompt=""
if [[ $# -gt 0 ]]; then
  prompt="$*"
else
  # read entire stdin as one prompt (preserves newlines)
  prompt="$(cat)"
fi

[[ -n "${prompt//[[:space:]]/}" ]] || { echo "ERR: empty prompt" >&2; exit 2; }

log "RUN: ${prompt:0:200}"
exec "$HOME/b4d/b4d.sh" "$prompt"
