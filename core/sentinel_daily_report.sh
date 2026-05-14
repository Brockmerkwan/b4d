#!/usr/bin/env bash
# Sentinel Daily Health Check Script
# Sends daily infrastructure status to Discord via webhook

set -euo pipefail

LOG_FILE="$HOME/.local/state/sentinel_health.log"
WEBHOOK_URL="${B4D_DISCORD_WEBHOOK:-}"

# Logging function
log() {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*" | tee -a "$LOG_FILE"
}

# Check if webhook is configured
if [[ -z "$WEBHOOK_URL" ]]; then
    log "ERROR: B4D_DISCORD_WEBHOOK environment variable not set"
    exit 1
fi

# Run sentinel monitor and capture output
log "Running sentinel health check..."
STATUS_OUTPUT=""
STATUS_ERROR=""

if STATUS_OUTPUT=$(python3 "$HOME/bin/sentinel_monitor.py" 2>/tmp/sentinel_stderr.log); then
    log "Sentinel check completed successfully"
else
    STATUS_ERROR=$(cat /tmp/sentinel_stderr.log)
    log "Sentinel check failed: $STATUS_ERROR"
fi

# Parse the status data
if [[ -n "$STATUS_OUTPUT" && "$STATUS_OUTPUT" == {*}* ]]; then
    # Parse JSON using jq
    CPU_LOAD=$(echo "$STATUS_OUTPUT" | jq -r .cpu_usage_percent // Unknown)
    DISK_FREE=$(echo "$STATUS_OUTPUT" | jq -r .disk_free_percent // Unknown)
    TAILSCALE_STATUS=$(echo "$STATUS_OUTPUT" | jq -r .tailscale_status // Unknown)
    OLLAMA_STATUS=$(echo "$STATUS_OUTPUT" | jq -r .ollama_status // Unknown)
    CONTAINERS=$(echo "$STATUS_OUTPUT" | jq -r .docker_containers_running // Unknown)
else
    CPU_LOAD="Error"
    DISK_FREE="Error"
    TAILSCALE_STATUS="Error"
    OLLAMA_STATUS="Error"
    CONTAINERS="Error"
fi

# Send to Discord
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
MESSAGE_CONTENT="🔔 **Daily Infrastructure Status Report**
🗓️ ${TIMESTAMP}

**CPU Usage**:     ${CPU_LOAD}%
**Disk Free**:     ${DISK_FREE}%
**Tailscale**:     ${TAILSCALE_STATUS}
**Ollama API**:    ${OLLAMA_STATUS}
**Containers**:    ${CONTAINERS}

Status: Health check completed"

# Escape quotes for JSON
ESCAPED_CONTENT=$(printf %s "$MESSAGE_CONTENT" | sed s//\/g)

# Send to Discord
log "Sending status report to Discord..."
PAYLOAD="{\"content\": \"$ESCAPED_CONTENT\"}"

if curl -fsS -X POST \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$WEBHOOK_URL" >/dev/null 2>&1; then
    log "Status report sent successfully"
else
    log "Failed to send status report to Discord"
fi
