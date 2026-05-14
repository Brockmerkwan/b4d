#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="${HOME}/.local/state/b4d"
BOOT_LOG="${LOG_DIR}/bootstrap.log"
mkdir -p "$LOG_DIR"
exec > >(tee -a "$BOOT_LOG") 2>&1

echo "==> apt deps"
sudo apt-get update -y
sudo apt-get install -y python3-yaml

echo "==> directories"
mkdir -p ~/b4d/{agents,core,logs,models,scripts,venvs}
mkdir -p ~/.local/state/b4d

echo "==> core package marker"
touch ~/b4d/core/__init__.py

echo "==> core logger"
cat > ~/b4d/core/log.py <<'PY'
from datetime import datetime, timezone
import os, json

LOG = os.path.expanduser("~/.local/state/b4d/b4d.log")

def log(event, **data):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **data}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
PY

echo "==> ollama_ask"
cat > ~/b4d/core/ollama_ask.py <<'PY'
#!/usr/bin/env python3
import json, os, sys, urllib.request

HOST  = os.environ.get("B4D_OLLAMA", "http://127.0.0.1:11434")
MODEL = os.environ.get("B4D_MODEL", "llama3.2:3b")

def ask(prompt: str) -> str:
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    req = urllib.request.Request(
        f"{HOST}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode("utf-8")).get("response", "").strip()

def main():
    if len(sys.argv) < 2:
        print("usage: ollama_ask.py <prompt>", file=sys.stderr)
        sys.exit(2)
    print(ask(" ".join(sys.argv[1:])))

if __name__ == "__main__":
    main()
PY
chmod +x ~/b4d/core/ollama_ask.py

echo "==> agent registry (safe defaults)"
cat > ~/b4d/agents/registry.yaml <<'YAML'
agents:
  echo:
    description: "Fast"
    model: llama3.2:3b
  think:
    description: "Better accuracy"
    model: qwen2.5:7b
YAML

echo "==> agent runner (self-contained sys.path)"
cat > ~/b4d/core/agent_runner.py <<'PY'
#!/usr/bin/env python3
import os, sys, subprocess, yaml
sys.path.insert(0, os.path.expanduser("~/b4d"))

from core.log import log

BASE = os.path.expanduser("~/b4d")
REG  = f"{BASE}/agents/registry.yaml"
ASK  = f"{BASE}/core/ollama_ask.py"

def load_agents():
    with open(REG) as f:
        return yaml.safe_load(f)["agents"]

def main():
    if len(sys.argv) < 3:
        print("usage: agent_runner.py <agent> <prompt>")
        sys.exit(2)

    agent = sys.argv[1]
    prompt = " ".join(sys.argv[2:])

    agents = load_agents()
    if agent not in agents:
        print(f"unknown agent: {agent}")
        sys.exit(1)

    model = agents[agent]["model"]
    os.environ["B4D_MODEL"] = model

    log("agent_call", agent=agent, model=model, prompt=prompt)

    # prompt passed as one arg; ollama_ask joins argv anyway
    subprocess.run([ASK, prompt], check=False)

if __name__ == "__main__":
    main()
PY
chmod +x ~/b4d/core/agent_runner.py

echo "==> tmux menu launcher"
cat > ~/b4d/core/menu.sh <<'SH'
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
SH
chmod +x ~/b4d/core/menu.sh

echo "==> sanity checks"
command -v ollama >/dev/null
curl -fsS http://127.0.0.1:11434/api/tags >/dev/null || true

echo "==> done"
echo "Try: ~/b4d/core/agent_runner.py echo 'Say exactly: B4D online.'"
echo "Logs: tail -n 1 ~/.local/state/b4d/b4d.log"
