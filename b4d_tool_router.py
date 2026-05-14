#!/usr/bin/env python3
# b4d_tool_router.py — single-file tool router (reads ~/b4d/tools.yaml)
# Usage:
#   python3 ~/b4d/b4d_tool_router.py shell '{"cmd":"git status"}'
#   python3 ~/b4d/b4d_tool_router.py web   '{"query":"amd open source ai models","max_results":5}'
# Returns JSON on stdout. Logs to cfg log_dir (default ~/.local/state/b4d/tools).

import ast
import datetime as dt
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.request
from typing import Any, Dict, List, Tuple


def expand(p: str) -> str:
    return os.path.expanduser(os.path.expandvars(p))


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


# --- Minimal YAML loader (subset) ---
# Supports:
# - indentation-based dicts
# - key: value (value can be: true/false/number/quoted string)
# - inline lists: ["a","b"]   (strings must be quoted)
# - inline dicts: {k: "v"}
# - ignores comments (#...) and blank lines
def _parse_scalar(val: str) -> Any:
    val = val.strip()
    if val == "":
        return None
    if val in ("true", "True"):
        return True
    if val in ("false", "False"):
        return False
    if re.fullmatch(r"-?\d+", val):
        return int(val)
    if re.fullmatch(r"-?\d+\.\d+", val):
        return float(val)
    if (val.startswith("[") and val.endswith("]")) or (val.startswith("{") and val.endswith("}")):
        # NOTE: requires quoted strings for lists/dicts
        return ast.literal_eval(val)
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return ast.literal_eval(val)
    return val


def load_yaml_subset(path: str) -> Dict[str, Any]:
    text = open(path, "r", encoding="utf-8").read().splitlines()
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(0, root)]

    for raw in text:
        line = raw.split("#", 1)[0].rstrip("\n")
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        line = line.strip()

        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()

        if ":" not in line:
            raise ValueError(f"Unsupported YAML line (missing ':'): {raw}")

        key, rest = line.split(":", 1)
        key = key.strip()
        rest = rest.strip()

        cur = stack[-1][1]

        if rest == "":
            newd: Dict[str, Any] = {}
            cur[key] = newd
            stack.append((indent + 2, newd))
        else:
            cur[key] = _parse_scalar(rest)

    return root


def log_event(log_dir: str, obj: Dict[str, Any]) -> None:
    ensure_dir(log_dir)
    day = dt.datetime.now().strftime("%Y-%m-%d")
    fp = os.path.join(log_dir, f"toolrouter.{day}.log.jsonl")
    with open(fp, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def out(obj: Dict[str, Any], log_dir: str) -> None:
    obj.setdefault("ts", now_iso())
    log_event(log_dir, obj)
    print(json.dumps(obj, ensure_ascii=False))


def fail(tool: str, msg: str, log_dir: str, **extra: Any) -> None:
    obj = {"ok": False, "tool": tool, "error": msg}
    obj.update(extra)
    out(obj, log_dir)
    sys.exit(0)


def tool_shell(cfg: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    shell_cfg = cfg["tools"]["shell"]
    cmd = args.get("cmd", "")
    if not isinstance(cmd, str) or not cmd.strip():
        return {"ok": False, "tool": "shell", "error": "missing cmd"}

    for pat in shell_cfg.get("deny_patterns", []) or []:
        if re.search(pat, cmd):
            return {"ok": False, "tool": "shell", "error": f"blocked by deny_patterns: {pat}"}

    try:
        parts = shlex.split(cmd)
    except ValueError as ex:
        return {"ok": False, "tool": "shell", "error": f"bad shell cmd parse: {ex}"}

    if not parts:
        return {"ok": False, "tool": "shell", "error": "empty cmd"}

    first = parts[0]
    allow = shell_cfg.get("allow_cmds", []) or []
    if first not in allow:
        return {"ok": False, "tool": "shell", "error": f"command not allowed: {first}", "allowed": allow}

    timeout_sec = int(cfg.get("timeout_sec", 30))
    cwd = expand(str(args.get("cwd") or shell_cfg.get("workdir_default") or "~"))

    try:
        p = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {"ok": True, "tool": "shell", "stdout": p.stdout, "stderr": p.stderr, "exit_code": p.returncode, "cwd": cwd}
    except subprocess.TimeoutExpired:
        return {"ok": False, "tool": "shell", "error": f"timeout after {timeout_sec}s", "cwd": cwd}


def _http_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout_sec: int) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return json.loads(body)


def tool_web(cfg: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    web_cfg = cfg["tools"]["web"]
    query = args.get("query", "")
    if not isinstance(query, str) or not query.strip():
        return {"ok": False, "tool": "web", "error": "missing query"}

    provider = str(web_cfg.get("provider", "tavily"))
    timeout_sec = int(cfg.get("timeout_sec", 30))
    max_results = args.get("max_results", web_cfg.get("max_results", 8))
    try:
        max_results = int(max_results)
    except Exception:
        max_results = 8

    if provider == "tavily":
        env = str(web_cfg.get("api_key_env", "TAVILY_API_KEY"))
        key = os.environ.get(env, "")
        if not key:
            return {"ok": False, "tool": "web", "error": f"missing env var {env} for tavily"}

        payload = {"api_key": key, "query": query, "max_results": max_results, "include_answer": False, "include_raw_content": False}
        r = _http_json("https://api.tavily.com/search", payload, {"Content-Type": "application/json"}, timeout_sec)

        items = []
        for it in (r.get("results") or []):
            items.append({"title": it.get("title"), "url": it.get("url"), "snippet": it.get("content"), "score": it.get("score")})
        return {"ok": True, "tool": "web", "provider": "tavily", "query": query, "results": items}

    return {"ok": False, "tool": "web", "error": f"provider not implemented: {provider}"}


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: b4d_tool_router.py <tool> '<json-args>'", file=sys.stderr)
        sys.exit(2)

    tool = sys.argv[1].strip()
    arg_s = sys.argv[2].strip()

    cfg_path = expand(os.environ.get("B4D_TOOLS_CFG", "~/b4d/tools.yaml"))
    if not os.path.exists(cfg_path):
        print(f"missing tools config: {cfg_path}", file=sys.stderr)
        sys.exit(2)

    cfg = load_yaml_subset(cfg_path)
    log_dir = expand(str(cfg.get("log_dir", "~/.local/state/b4d/tools")))
    ensure_dir(log_dir)

    try:
        args = json.loads(arg_s) if arg_s else {}
    except Exception as ex:
        fail(tool, f"bad json args: {ex}", log_dir)

    tools = (cfg.get("tools") or {})
    if tool not in tools:
        fail(tool, f"unknown tool: {tool}", log_dir)

    enabled = bool((tools.get(tool) or {}).get("enabled", False))
    if not enabled:
        fail(tool, "tool disabled in tools.yaml", log_dir)

    if tool == "shell":
        out(tool_shell(cfg, args), log_dir)
        return
    if tool == "web":
        out(tool_web(cfg, args), log_dir)
        return

    fail(tool, "tool not implemented in router", log_dir)


if __name__ == "__main__":
    main()
