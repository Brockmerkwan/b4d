#!/usr/bin/env bash
set -euo pipefail

echo "B4D Menu"
echo "1) echo  (fast)"
echo "2) think (better accuracy)"
read -rp "Select: " sel
read -rp "Prompt: " prompt

case "$sel" in
  1) agent=echo ;;
  2) agent=think ;;
  *) echo "Invalid"; exit 1 ;;
esac

~/b4d/core/agent_runner.py "$agent" "$prompt"
