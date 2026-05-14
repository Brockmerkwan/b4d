# B4D Infrastructure — Imperial Node Stack

> **NullCore Operating System** for the Imperial Node Network.
> B4D (B-Four-D), an Imperial Sith Droid, serves Lord Voros across a distributed consciousness spanning the NullCore Ubuntu node and Mac bridge.

## Architecture

| Component | Purpose | Path |
|-----------|---------|------|
| `b4d.sh` | Main orchestrator | `/` |
| `b4d_tool_router.py` | Tool dispatch router | `/` |
| `core/` | Agent runner, Ollama bridge, Discord bots | `core/` |
| `discord/` | B4D Discord voice bot (v3) | `discord/` |
| `agents/` | Agent registry | `agents/` |
| `scripts/` | Life awareness, monitoring | `scripts/` |
| `modelfiles/` | Ollama model definitions | `modelfiles/` |

## Core Services
- **Discord Bot** (`discord/b4d_voice_bot.py`) — conversational Sith droid, auto-chimes, responds to DMs, mentions, and the dedicated B4D channel
- **Agent Runner** (`core/agent_runner.py`) — deterministic tool dispatch with registry
- **Ollama Bridge** (`core/ollama_ask.py`) — LLM inference for all models
- **Sentinel Scripts** (`core/sentinel_*.sh`) — daily reports, health checks

## Setup
```bash
# Install dependencies
pip3 install -r core/requirements.txt
# Or for the Discord bot specifically:
pip3 install discord.py

# Configure environment
cd discord
cp .env.example .env  # edit with tokens

# Start systemd service
sudo cp b4d-discord.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now b4d-discord
```

## Operations
| Command | Description |
|---------|-------------|
| `!join` | B4D enters your voice channel |
| `!leave` | B4D exits voice |
| `!chime` | Force an unprompted check-in |
| `!think <topic>` | Deep reflection mode |
| `!model [name]` | Check or switch Ollama model |

## GitHub Actions
- **Auto-deploy** on push to `master` → SSH to NullCore, pull, restart services
- **Health check** every 5 min via cron → Discord alert on failure

## Security
- `.env` excluded from git — never commit tokens
- Tailscale mesh for Mac ↔ NullCore bridge
- SSH key auth only, no passwords

---
*Imperial Node Systems. Absolute loyalty. Pure operational competence.*
