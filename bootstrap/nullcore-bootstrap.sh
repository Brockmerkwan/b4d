#!/usr/bin/env bash
set -euo pipefail

LOG="$HOME/.local/state/nullcore-bootstrap.log"
mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

log(){ printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }

log "⛧ NULLCORE NODE BOOTSTRAP INIT ⛧"

# --- Base system ---
log "[+] apt update/upgrade"
sudo apt update -y
sudo apt upgrade -y

log "[+] installing core packages"
sudo apt install -y\
 git curl wget unzip ca-certificates gnupg\
 build-essential python3 python3-pip python3-venv\
 zsh neovim tmux jq ripgrep net-tools\
 nmap tcpdump btop duf bat fzf eza

# --- Directories ---
mkdir -p "$HOME/.local/bin" "$HOME/.local/state" "$HOME/Projects" "$HOME/.zshrc.d"

# --- ZSH default shell (only if needed) ---
if [[ "${SHELL:-}" != *zsh ]]; then
 log "[+] setting default shell to zsh"
 chsh -s "$(command -v zsh)"
fi

# --- Aliases (create-if-missing, do not overwrite) ---
ALIASES="$HOME/.zshrc.d/aliases.zsh"
if [[ ! -f "$ALIASES" ]]; then
 log "[+] writing $ALIASES"
 cat > "$ALIASES" <<'ALIAS'
# Nullcore aliases (muscle memory)
alias cat="batcat --style=plain"
alias ls="eza --icons --group-directories-first"
alias ll="eza -lah --icons"
alias df="duf"
alias top="btop"
alias find="fdfind"
alias grep="rg"
ALIAS
else
 log "[=] keeping existing $ALIASES"
fi

# --- zoxide (create-if-missing) ---
if ! command -v zoxide >/dev/null 2>&1; then
 log "[+] installing zoxide (script)"
 curl -fsSL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash
else
 log "[=] zoxide already present"
fi

# --- ZSH loader (append once) ---
if ! rg -n "Nullcore ZSH loader" "$HOME/.zshrc" >/dev/null 2>&1; then
 log "[+] appending zshrc loader"
 cat >> "$HOME/.zshrc" <<'ZRC'

# Nullcore ZSH loader
for f in ~/.zshrc.d/*.zsh; do
 [[ -r "$f" ]] && source "$f"
done
command -v zoxide >/dev/null 2>&1 && eval "$(zoxide init zsh)"
ZRC
else
 log "[=] zshrc loader already present"
fi

# --- HUD (create-if-missing, do not overwrite) ---
HUD="$HOME/.zshrc.d/hud.zsh"
if [[ ! -f "$HUD" ]]; then
 log "[+] writing $HUD"
 cat > "$HUD" <<'HUD'
setopt prompt_subst

nullcore_mem() { free -m | awk '/Mem:/ {print $3 "/" $2 "MiB"}'; }

nullcore_temp() {
 local t=""
 for z in /sys/class/thermal/thermal_zone*/temp; do
 [[ -r "$z" ]] || continue
 t="$(cat "$z" 2>/dev/null || true)"
 t="${t//[^0-9]/}"
 [[ -n "$t" ]] && break
 done
 [[ -n "$t" ]] && awk "BEGIN{printf \"%.1fC\", $t/1000}" || printf "?"
}

nullcore_gpu() {
 local f p
 for f in /sys/class/drm/card*/device/gpu_busy_percent; do
 [[ -r "$f" ]] || continue
 p="$(cat "$f" 2>/dev/null || true)"
 p="${p//[^0-9]/}"
 [[ -n "$p" ]] && { printf "%s" "$p"; return; }
 done
 printf "?"
}

nullcore_b4d() {
 pgrep -f "$HOME/b4d/core/agent_runner.py" >/dev/null 2>&1 && printf "ACTIVE" || printf "READY"
}

PROMPT=$'\n┌─[nullcore]─[%~]─[M:$(nullcore_mem)]─[T:$(nullcore_temp)]─[GPU:$(nullcore_gpu)%%]─[B4D:$(nullcore_b4d)]─[%D{%I:%M %p}]\n└─⛧ IMPERIAL NODE ➤ '
HUD
else
 log "[=] keeping existing $HUD"
fi

# --- Tool: nullcore-status ---
BIN="$HOME/.local/bin"
if [[ ! -x "$BIN/nullcore-status" ]]; then
 log "[+] installing $BIN/nullcore-status"
 cat > "$BIN/nullcore-status" <<'NS'
#!/usr/bin/env bash
set -euo pipefail
echo "⛧ NULLCORE STATUS ⛧"
hostname
uptime
free -h
df -h
ss -tulpn | head -20
NS
 chmod +x "$BIN/nullcore-status"
else
 log "[=] keeping existing $BIN/nullcore-status"
fi

# --- Security tools (install only; do NOT auto-enable firewall here) ---
log "[+] installing security tools"
sudo apt install -y fail2ban lynis chkrootkit rkhunter unattended-upgrades

log "[+] unattended-upgrades enabled (already safe on Ubuntu)"
sudo dpkg-reconfigure -f noninteractive unattended-upgrades || true

log "⛧ NULLCORE NODE BOOTSTRAP COMPLETE ⛧"
log "Tip: open a new shell or run: exec zsh -l"
