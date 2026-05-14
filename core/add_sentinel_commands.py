import subprocess
import os
import sys

def add_sentinel_commands(bot_file_int_line: int):
    """Add Sentinel commands to the existing bot at the specified line"""
    bot_file_path = "/home/nullcore/b4d/core/discord_bot.py"
    
    with open(bot_file_path, "r") as f:
        lines = f.readlines()

    # The insertion point lines
    sentinel_functions = """
# ─── Sentinel Integration Functions ───────────────────────────────────────

def run_sentinel_check():
    \"\"\"Run sentinel_monitor.py and return parsed status\"\"\"
    try:
        result = subprocess.run(
            ["python3", os.path.expanduser("~/bin/sentinel_monitor.py")],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if output.startswith("{") and output.endswith("}"):
                import json
                return json.loads(output)
            else:
                return {"raw_output": output}
        else:
            return {"error": f"Exit code {result.returncode}", "stderr": result.stderr}
    except Exception as e:
        return {"error": str(e)}

def format_sentinel_summary(status_data):
    \"\"\"Format sentinel status as a text summary\"\"\"
    if "error" in status_data:
        return f"❌ **Sentinel Check Failed**: {status_data[error]}"
    
    cpu_load = status_data.get("cpu_usage_percent", "Unknown")
    disk_free = status_data.get("disk_free_percent", "Unknown")
    ts_status = status_data.get("tailscale_status", "Unknown")
    ollama_status = status_data.get("ollama_status", "Unknown")
    containers = status_data.get("docker_containers_running", "Unknown")
    
    cpu_indicator = "🟢" if isinstance(cpu_load, (int, float)) and cpu_load < 80 else "🔴"
    disk_indicator = "🟢" if isinstance(disk_free, (int, float)) and disk_free > 15 else "🔴"
    ts_indicator = "..." if ts_status == "connected" else "🔴"
    ollama_indicator = "🟢" if ollama_status == "healthy" else "🔴"
    
    return (
        f"🔔 **Infrastructure Status Report**\\n"
        f"\\n"
        f"{cpu_indicator} **CPU Usage**:     {cpu_load}%\\n"
        f"{disk_indicator} **Disk Free**:     {disk_free}%\\n"
        f"{ts_indicator} **Tailscale**:    {ts_status}\\n"
        f"{ollama_indicator} **Ollama API**:   {ollama_status}\\n"
        f"🔧 **Containers**:   {containers}\\n"
        f"\\n"
        f"{🟢 All systems nominal. if all([cpu_indicator == 🟢, disk_indicator == 🟢, ts_indicator == 🟢, ollama_indicator == 🟢]) else ⚠️ Attention required.}"
    )

def cpu_scale_indicator(val):
    if isinstance(val, (int, float)) and val < 80: return "🟢"
    return "🔴"
"""
        # The command handler logic to be inserted in the loop
        command_handlers = """    # ── Sentinel Diagnostics ──
    if cmd in ("sentinel", "infrastructure"):
        if not is_owner(author.id):
            await reply("🚫 That command is .......................")
            return
        async with message.channel.typing():
            try:
                import json
                result = await asyncio.to_thread(run_sentinel_check)
                status_text = format_sentinel_summary(result)
                await reply(status_text)
            except Exception as e:
                await reply(f"⚠️ Sentinel check failed: {e}")
        return

    if cmd == "analyze":
        if not is_owner(author.id):
            await reply("🚫 That command is .......................")
            return
        async with message.channel.typing():
            try:
                import json
                status_result = await asyncio.to_thread(run_sentinel_check)
                context = f"System Status: {json.dumps(status_result) if isinstance(status_result, dict) else str(status_result)}"
                full_prompt = f"{context}\\n\\nAnalyze this system status and provide recommendations: {arg if arg else general assessment}"
                result = await asyncio.to_thread(run_b4d, full_prompt)
                await reply(result)
            except Exception as e:
                await reply(f"⚠️ Analysis failed: {e}")
        return
"""
        # 1. Insert functions before the target line
        lines.insert(bot_file_int_line - 1, sentinel_functions + "\n")

        # 2. Find the command handler loop start and insert the handler
        # Searching for the line where if cmd ==  is used
        found_handler_idx = -1
        for i, line in enumerate(lines):
            if "if cmd ==" in line and "is_owner" in line: # Finding an existing command check
                found_handler_idx = i
                break
        
        if found_handler_idx != -1:
            # We want to insert BEFORE the next if cmd block or at least in the same area
            # To be safe, we find the index of the FIRST command check if cmd == ... and insert here.
            # But the logic is easier: find the if cmd == line and insert it after the block? 
            # No, lets find where the command check block starts.