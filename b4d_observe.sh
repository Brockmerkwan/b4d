#!/usr/bin/env bash
set -euo pipefail

# B4D System Observation - Companion Daemon
# Sends a periodic observation to Discord webhook

WEBHOOK="${B4D_DISCORD_WEBHOOK:-}"
[[ -n "$WEBHOOK" ]] || exit 0

LOG_DIR="$HOME/.local/state/b4d"
mkdir -p "$LOG_DIR"

# Gather intelligence
LOAD=$(cut -d' ' -f1 /proc/loadavg 2>/dev/null || echo "?")
MEM=$(free -h 2>/dev/null | awk '/Mem:/ {print $3"/"$2}' || echo "?")
UPTIME=$(uptime -p 2>/dev/null | sed 's/up //' || echo "unknown")
DOCKERS=$(docker ps -q 2>/dev/null | wc -l || echo "?")

MSG=$(cat <<EOF
**B4D Observation**
⚔️ Load: ${LOAD}  |  🧠 Mem: ${MEM}  |  ⏱️ ${UPTIME}
🛠️ Active vessels: ${DOCKERS}
EOF
)

payload=$(printf '{"content": "%s"}' "$(printf '%s' "$MSG" | sed 's/"/\\"/g')")
curl -fsS -X POST -H "Content-Type: application/json" -d "$payload" "$WEBHOOK" >/dev/null || true
