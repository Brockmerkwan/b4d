#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/b4d"
RUNNER="$BASE/core/agent_runner.py"
LOG_DIR="$HOME/.local/state/b4d"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/b4d_router.log"

ts(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log(){ printf "[%s] %s\n" "$(ts)" "$*" | tee -a "$LOG" >/dev/null; }
die(){ echo "ERR: $*" >&2; exit 1; }

[[ -f "$RUNNER" ]] || die "missing runner: $RUNNER"

SESSION_ON="${B4D_SESSION_ON:-0}"
SESSION_FILE="${B4D_SESSION_FILE:-$LOG_DIR/session.txt}"
SESSION_TAIL="${B4D_SESSION_TAIL:-20}"

PROMPT="${*:-}"
[[ -n "$PROMPT" ]] || die "usage: b4d.sh '<prompt>'"

CTX=""
if [[ "$SESSION_ON" == "1" && -f "$SESSION_FILE" ]]; then
  CTX="$(tail -n "$SESSION_TAIL" "$SESSION_FILE" | sed 's/\r$//')"
fi

cmd="$PROMPT"
agent="b4d"
cmd="${cmd#"${cmd%%[![:space:]]*}"}"

if [[ "$cmd" =~ ^raw:[[:space:]]*(.*)$ ]]; then
  cmd="${BASH_REMATCH[1]}"
  CTX=""
elif [[ "$cmd" =~ ^b4d:[[:space:]]*(.*)$ ]]; then
  cmd="${BASH_REMATCH[1]}"
elif [[ "$cmd" =~ ^math:[[:space:]]*(.*)$ ]]; then
  expr="${BASH_REMATCH[1]}"
  agent="tools"
  cmd="math {\"expr\":\"${expr//\"/\\\"}\"}"
elif [[ "$cmd" =~ ^tools[[:space:]]+ ]]; then
  agent="tools"
  cmd="${cmd#tools }"
fi

if [[ "$SESSION_ON" == "1" && -n "$CTX" && "$agent" == "b4d" ]]; then
  cmd=$'Context (recent):\n'"$CTX"$'\n\nUser:\n'"$cmd"
fi

log "agent=$agent"

if [[ "$agent" == "tools" ]]; then
  tool="${cmd%% *}"
  payload="${cmd#${tool} }"
  [[ -n "$tool" && "$payload" != "$cmd" ]] || die "tools usage: tools <tool> <json>"
  python3 "$RUNNER" tools "$tool" "$payload" | tee "$LOG_DIR/b4d_last.out"
else
  python3 "$RUNNER" b4d "$cmd" | tee "$LOG_DIR/b4d_last.out"
fi

if [[ "$SESSION_ON" == "1" && "$agent" == "b4d" ]]; then
  {
    echo "U: ${PROMPT}"
    echo "----"
    cat "$LOG_DIR/b4d_last.out" 2>/dev/null || true
    echo ""
  } >> "$SESSION_FILE"
fi
