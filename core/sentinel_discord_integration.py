#!/usr/bin/env python3
"""
Sentinel Discord Integration for B4D Bot
Adds !status command and periodic health checks
"""

import asyncio
import discord
import json
import subprocess
import os
from pathlib import Path

# Configuration
SENTINEL_MONITOR_PATH = Path("~/bin/sentinel_monitor.py").expanduser()
HEALTH_REPORTS_DIR = Path("~/Documents/health_reports").expanduser()
HEALTH_REPORTS_DIR.mkdir(exist_ok=True)

def get_sentinel_status():
    """Run sentinel_monitor.py and return parsed status"""
    try:
        result = subprocess.run(
            ["python3", str(SENTINEL_MONITOR_PATH)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            # Parse JSON output
            output = result.stdout.strip()
            if output.startswith({):
                return json.loads(output)
            else:
                return {"error": "Non-JSON output", "raw": output}
        else:
            return {"error": f"Exit code {result.returncode}", "stderr": result.stderr}
    except Exception as e:
        return {"error": str(e)}

def format_status_embed(status_data):
    """Format sentinel status as Discord embed"""
    if "error" in status_data:
        return {
            "title": "❌ Sentinel Status Check Failed",
            "description": f"```{status_data[error]}```",
            "color": 0xff0000
        }
    
    # Extract key metrics
    cpu_load = status_data.get("cpu_usage_percent", "Unknown")
    disk_free = status_data.get("disk_free_percent", "Unknown")
    tailscale = status_data.get("tailscale_status", "Unknown")
    ollama = status_data.get("ollama_status", "Unknown")
    containers = status_data.get("docker_containers_running", "Unknown")
    
    # Determine overall status
    status_color = 0x00ff00  # Green
    status_emoji = "✅"
    
    if isinstance(cpu_load, (int, float)) and cpu_load > 80:
        status_color = 0xff9900  # Orange
        status_emoji = "⚠️"
    if isinstance(disk_free, (int, float)) and disk_free < 10:
        status_color = 0xff0000  # Red
        status_emoji = "🚨"
    if tailscale != "connected":
        status_color = 0xff0000  # Red
        status_emoji = "🚨"
    if ollama != "healthy":
        status_color = 0xff0000  # Red
        status_emoji = "🚨"
    
    return {
        "title": f"{status_emoji} Infrastructure Status Report",
        "fields": [
            {"name": "🖥️ CPU Usage", "value": f"{cpu_load}%", "inline": True},
            {"name": "💾 Disk Free", "value": f"{disk_free}%", "inline": True},
            {"name": "📡 Tailscale", "value": tailscale, "inline": True},
            {"name": "🧠 Ollama", "value": ollama, "inline": True},
            {"name": "🐳 Containers", "value": str(containers), "inline": True},
        ],
        "color": status_color,
        "footer": {"text": "Sentinel Visibility Layer Active"}
    }

def format_daily_summary(status_data):
    """Format daily summary for periodic pings"""
    if "error" in status_data:
        return f"❌ **Sentinel Check Failed**: {status_data[error]}"
    
    cpu_load = status_data.get("cpu_usage_percent", "Unknown")
    disk_free = status_data.get("disk_free_percent", "Unknown")
    tailscale = status_data.get("tailscale_status", "Unknown")
    ollama = status_data.get("ollama_status", "Unknown")
    containers = status_data.get("docker_containers_running", "Unknown")
    
    # Simple status indicators
    cpu_indicator = "🟢" if isinstance(cpu_load, (int, float)) and cpu_load < 80 else "🔴"
    disk_indicator = "🟢" if isinstance(disk_free, (int, float)) and disk_free > 15 else "🔴"
    ts_indicator = "🟢" if tailscale == "connected" else "🔴"
    ollama_indicator = "🟢" if ollama == "healthy" else "🔴"
    
    return (
        f"🔔 **Daily Infrastructure Status Report**\n"
        f"\n"
        f"{cpu_indicator} **CPU Usage**:     {cpu_load}%\n"
        f"{disk_indicator} **Disk Free**:     {disk_free}%\n"
        f"{ts_indicator} **Tailscale**:    {tailscale}\n"
        f"{ollama_indicator} **Ollama API**:   {ollama}\n"
        f"🔧 **Containers**:   {containers}\n"
        f"\n"
        f"{🟢 All systems nominal. if all([cpu_indicator == 🟢, disk_indicator == 🟢, ts_indicator == 🟢, ollama_indicator == 🟢]) else ⚠️ Attention required.}"
    )

if __name__ == "__main__":
    # Test the integration
    print("Testing Sentinel Discord Integration...")
    status = get_sentinel_status()
    print("Status data:", json.dumps(status, indent=2))
    embed = format_status_embed(status)
    print("Embed format:", json.dumps(embed, indent=2))
    summary = format_daily_summary(status)
    print("Summary format:")
    print(summary)
