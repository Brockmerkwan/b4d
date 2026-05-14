#!/usr/bin/env python3
"""
B4D LIFE-AWARENESS MODULE
=========================
Tracks Lord Voros's life metrics: calendar, health, creative output.
Runs on nullcore, queries Mac via SSH for local data.

DATA_STORE: ~/.local/state/b4d/life_awareness.json
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import os

# ── Configuration ────────────────────────────────────────────────

DATA_DIR = Path.home() / ".local/state/b4d"
DATA_FILE = DATA_DIR / "life_awareness.json"
MAC_USER = "brockmerkwan"
MAC_HOST = "100.80.91.41"

# Creative project paths on Mac
CREATIVE_PATHS = {
    "prescribed_passion": "/Users/brockmerkwan/PrescribedPassion",
    "aimedia": "/Volumes/halacron/aimedia",
    "notes": "/Users/brockmerkwan/Documents/Notes",
}

# ── Data Structure ──────────────────────────────────────────────

def init_db() -> Dict:
    """Initialize or load the life awareness database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    
    return {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "calendar": {
            "today_events": [],
            "upcoming": [],
            "last_sync": None,
        },
        "fasting": {
            "current_window": None,
            "history": [],
            "streak_days": 0,
        },
        "health": {
            "weight": [],
            "sleep": [],
            "mood": [],
        },
        "creative": {
            "writing": {},
            "art": {},
            "code": {},
        },
        "daily_summary": {},
    }

def save_db(db: Dict):
    """Save database to disk."""
    db["last_updated"] = datetime.now().isoformat()
    DATA_FILE.write_text(json.dumps(db, indent=2, default=str))

# ── Calendar Integration ────────────────────────────────────────

def get_simple_calendar() -> List[Dict]:
    """Fetch calendar events from Mac via SSH."""
    try:
        cmd = [
            "ssh", f"{MAC_USER}@{MAC_HOST}",
            "icalbuddy -nc -n eventsToday 2>/dev/null || echo 'No icalbuddy'"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        events = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("No icalbuddy"):
                events.append({"summary": line, "source": "icalbuddy"})
        
        return events
    except Exception as e:
        return [{"error": str(e), "note": "Install icalbuddy on Mac for calendar"}]

# ── Intermittent Fasting Tracker ────────────────────────────────

def start_fast(db: Dict) -> Dict:
    """Mark the start of a fasting window."""
    now = datetime.now()
    db["fasting"]["current_window"] = {
        "start": now.isoformat(),
        "expected_end": (now + timedelta(hours=16)).isoformat(),
        "status": "active",
        "type": "16:8",
    }
    return db

def end_fast(db: Dict) -> Dict:
    """Mark the end of current fast, add to history."""
    window = db["fasting"].get("current_window")
    if not window:
        return db
    
    window["status"] = "completed"
    window["actual_end"] = datetime.now().isoformat()
    
    start = datetime.fromisoformat(window["start"])
    end = datetime.fromisoformat(window["actual_end"])
    window["duration_hours"] = round((end - start).total_seconds() / 3600, 2)
    
    db["fasting"]["history"].append(window)
    db["fasting"]["current_window"] = None
    db["fasting"]["streak_days"] += 1
    
    return db

def get_fast_status(db: Dict) -> Dict:
    """Get current fasting status."""
    window = db["fasting"].get("current_window")
    if window and window["status"] == "active":
        start = datetime.fromisoformat(window["start"])
        elapsed = datetime.now() - start
        expected = datetime.fromisoformat(window["expected_end"])
        remaining = expected - datetime.now()
        
        return {
            "status": "fasting",
            "elapsed_hours": round(elapsed.total_seconds() / 3600, 2),
            "remaining_hours": max(0, round(remaining.total_seconds() / 3600, 2)),
            "progress_pct": min(100, round(elapsed.total_seconds() / (16 * 3600) * 100, 1)),
        }
    
    return {"status": "not_fasting"}

# ── Health Metrics ─────────────────────────────────────────────

def log_weight(db: Dict, weight: float, unit: str = "lbs") -> Dict:
    """Log a weight measurement."""
    entry = {
        "date": datetime.now().isoformat(),
        "value": weight,
        "unit": unit,
    }
    db["health"]["weight"].append(entry)
    
    cutoff = datetime.now() - timedelta(days=90)
    db["health"]["weight"] = [
        w for w in db["health"]["weight"]
        if datetime.fromisoformat(w["date"]) > cutoff
    ]
    return db

def get_weight_trend(db: Dict) -> Optional[Dict]:
    """Calculate weight trend from last 7 days."""
    weights = db["health"]["weight"]
    if len(weights) < 1:
        return None
    
    cutoff = datetime.now() - timedelta(days=7)
    recent = [w for w in weights if datetime.fromisoformat(w["date"]) > cutoff]
    
    if len(recent) < 1:
        return None
    
    values = [w["value"] for w in recent]
    return {
        "current": values[-1],
        "average_7d": round(sum(values) / len(values), 1) if len(values) > 1 else values[0],
        "min_7d": min(values),
        "max_7d": max(values),
        "measurements": len(values),
    }

def log_sleep(db: Dict, hours: float, quality: int = None) -> Dict:
    """Log sleep duration and quality (1-10)."""
    entry = {
        "date": datetime.now().isoformat(),
        "hours": hours,
        "quality": quality,
    }
    db["health"]["sleep"].append(entry)
    return db

# ── Creative Tracking ─────────────────────────────────────────

def run_ssh_command(remote_cmd: str, timeout: int = 30) -> str:
    """Run command on Mac via SSH."""
    try:
        cmd = ["ssh", f"{MAC_USER}@{MAC_HOST}", remote_cmd]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except Exception as e:
        return ""

def count_words_mac(path: str) -> int:
    """Count words in markdown files on Mac."""
    try:
        remote = f"find {path} -name '*.md' -exec wc -w {{}} \\; 2>/dev/null | tail -1 | awk '{{print $1}}'"
        output = run_ssh_command(remote, timeout=30)
        return int(output) if output.isdigit() else 0
    except:
        return 0

def scan_creative_directories(db: Dict) -> Dict:
    """Update creative metrics from file system."""
    for name, path in CREATIVE_PATHS.items():
        if name == "prescribed_passion":
            words = count_words_mac(path)
            db["creative"]["writing"][name] = {
                "words_total": words,
                "last_scan": datetime.now().isoformat(),
            }
    
    try:
        aimedia_path = CREATIVE_PATHS.get("aimedia", "/Volumes/halacron/aimedia")
        remote = f"find {aimedia_path} -type f | wc -l"
        output = run_ssh_command(remote, timeout=10)
        db["creative"]["art"]["total_files"] = int(output) if output.isdigit() else 0
    except:
        pass
    
    return db

# ── Daily Summary ──────────────────────────────────────────────

def generate_daily_summary(db: Dict) -> Dict:
    """Generate today's summary."""
    today = datetime.now().date().isoformat()
    
    summary = {
        "date": today,
        "generated_at": datetime.now().isoformat(),
        "fasting": get_fast_status(db),
        "weight": get_weight_trend(db),
        "creative": db.get("creative", {}),
        "calendar": get_simple_calendar(),
    }
    
    db["daily_summary"][today] = summary
    return summary

# ── CLI Interface ─────────────────────────────────────────────

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="B4D Life-Awareness Module")
    parser.add_argument("action", choices=[
        "status", "start-fast", "end-fast", "log-weight", "log-sleep",
        "scan-creative", "summary", "calendar"
    ])
    parser.add_argument("--value", type=float, help="Numeric value (weight, hours)")
    parser.add_argument("--note", help="Additional notes")
    
    args = parser.parse_args()
    
    db = init_db()
    
    if args.action == "status":
        fast = get_fast_status(db)
        weight = get_weight_trend(db)
        
        print("=" * 50)
        print("B4D LIFE-AWARENESS STATUS")
        print("=" * 50)
        print(f"\nFasting: {fast['status'].upper()}")
        if fast['status'] == 'fasting':
            print(f"  Elapsed: {fast['elapsed_hours']}h")
            print(f"  Remaining: {fast['remaining_hours']}h")
            print(f"  Progress: {fast['progress_pct']}%")
        
        if weight:
            print(f"\nWeight (7-day): {weight['current']} lbs")
            print(f"  Avg: {weight['average_7d']} | Range: {weight['min_7d']}-{weight['max_7d']}")
        
        print(f"\nStreak: {db['fasting']['streak_days']} days")
        print("=" * 50)
    
    elif args.action == "start-fast":
        db = start_fast(db)
        save_db(db)
        print("Fasting window started. 16-hour countdown begins.")
    
    elif args.action == "end-fast":
        db = end_fast(db)
        save_db(db)
        window = db["fasting"]["history"][-1]
        print(f"Fast completed: {window.get('duration_hours', 'unknown')} hours")
    
    elif args.action == "log-weight":
        if not args.value:
            print("Error: --value required (weight in lbs)")
            sys.exit(1)
        db = log_weight(db, args.value)
        save_db(db)
        print(f"Logged weight: {args.value} lbs")
    
    elif args.action == "log-sleep":
        if not args.value:
            print("Error: --value required (hours slept)")
            sys.exit(1)
        quality = int(args.note) if args.note and args.note.isdigit() else None
        db = log_sleep(db, args.value, quality)
        save_db(db)
        print(f"Logged sleep: {args.value} hours")
    
    elif args.action == "scan-creative":
        db = scan_creative_directories(db)
        save_db(db)
        print("Creative metrics updated:")
        for k, v in db["creative"].items():
            print(f"  {k}: {v}")
    
    elif args.action == "summary":
        summary = generate_daily_summary(db)
        save_db(db)
        print(json.dumps(summary, indent=2, default=str))
    
    elif args.action == "calendar":
        events = get_simple_calendar()
        print("Today's Calendar:")
        for evt in events:
            print(f"  - {evt.get('summary', 'Unknown')}")

if __name__ == "__main__":
    main()
