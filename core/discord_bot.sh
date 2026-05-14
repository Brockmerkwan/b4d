#!/usr/bin/env bash
set -euo pipefail
BOT_DIR="$HOME/.local/share/b4d-discord"
set -a
[ -f "$BOT_DIR/b4d-discord.env" ] && . "$BOT_DIR/b4d-discord.env"
set +a
export PYTHONUNBUFFERED=1
exec "$BOT_DIR/venv/bin/python" -u "$HOME/b4d/core/discord_bot.py"
