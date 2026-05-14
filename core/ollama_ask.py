#!/usr/bin/env python3
import json, os, sys, urllib.request

HOST = os.environ.get("B4D_OLLAMA", "http://127.0.0.1:11434")

def ask(model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    req = urllib.request.Request(
        f"{HOST}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode("utf-8")).get("response", "").strip()

def main():
    if len(sys.argv) < 3:
        print("usage: ollama_ask.py <model> <prompt...>", file=sys.stderr)
        sys.exit(2)

    model = sys.argv[1].strip()
    prompt = " ".join(sys.argv[2:])

    # Optional override per-agent if you want it later:
    # export B4D_MODEL_OVERRIDE=...
    model = os.environ.get("B4D_MODEL_OVERRIDE", model).strip() or model

    out = ask(model, prompt)
    print(out)

if __name__ == "__main__":
    main()
