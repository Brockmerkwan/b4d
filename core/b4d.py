#!/usr/bin/env python3
import socket, platform
from datetime import datetime, timezone

def banner():
    print("=" * 52)
    print("B4D :: NullCore")
    print(f"Host : {socket.gethostname()}")
    print(f"OS   : {platform.system()} {platform.release()}")
    print(f"UTC  : {datetime.now(timezone.utc).isoformat()}Z")
    print("=" * 52)

def main():
    banner()

if __name__ == "__main__":
    main()
