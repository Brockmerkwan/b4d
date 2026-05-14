#!/usr/bin/env bash
set -euo pipefail

B4D_SH="${B4D_SH:-$HOME/b4d/b4d.sh}"
[[ -x "$B4D_SH" ]] || { echo "ERR: missing executable: $B4D_SH" >&2; exit 2; }

plan="$(cat)"
[[ -n "${plan//[[:space:]]/}" ]] || { echo "ERR: empty stdin" >&2; exit 2; }

if echo "$plan" | grep -qiE '^\s*\*?\*?Target:|^\s*Target:'; then
  prompt="INTERNAL PLAN (do not echo):"$'\n'"$plan"$'\n\n'"TASK: Produce the final actionable answer."$'\n'"RULES:"$'\n'"- Do NOT restate the plan fields."$'\n'"- Prefer canonical, widely-available checks first."$'\n'"- For ROCm specifically, prioritize: rocm-smi, rocminfo, /opt/rocm, dpkg -l | grep rocm."$'\n'"- If a command may not exist, guard it (command -v ...) and provide fallback."$'\n'"- Include what success/failure looks like in 1 line per check."$'\n'"- Output plain text commands only (no markdown/bullets), max ~10 lines."$'\n'
else
  prompt="$plan"
fi

exec "$B4D_SH" "$prompt"
