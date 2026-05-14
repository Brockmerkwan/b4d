from datetime import datetime, timezone
import os, json

LOG = os.path.expanduser("~/.local/state/b4d/b4d.log")

def log(event, **data):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **data}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
