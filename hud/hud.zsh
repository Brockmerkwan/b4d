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
