import os
import re
import sys
import time
import subprocess
import threading
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TUNNEL_FILE = BASE_DIR / "tunnel_url.txt"
PORT = 8000

def heartbeat_worker(url_holder, stop_event):
    """
    Sends an HTTP GET through the public tunnel every 30 seconds
    to prevent localhost.run 'tunnel activity timeout'.
    """
    while not stop_event.is_set():
        stop_event.wait(30)
        url = url_holder.get("url")
        if url and not stop_event.is_set():
            try:
                ping_url = f"{url}/api/voice/mobile/info"
                req = urllib.request.Request(ping_url, headers={"User-Agent": "TunnelKeeper/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    pass
            except Exception:
                pass

def run_tunnel():
    print("[TunnelKeeper] Starting resilient localhost.run tunnel keeper...", flush=True)
    
    while True:
        url_holder = {"url": None}
        stop_event = threading.Event()
        heartbeat_thread = threading.Thread(target=heartbeat_worker, args=(url_holder, stop_event), daemon=True)
        heartbeat_thread.start()

        cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=20",
            "-o", "ServerAliveCountMax=3",
            "-R", f"80:127.0.0.1:{PORT}",
            "nokey@localhost.run"
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            tunnel_url_pattern = re.compile(r"https://[a-zA-Z0-9]+\.lhr\.life")

            for line in proc.stdout:
                line_str = line.strip()
                if line_str:
                    print(f"[SSH] {line_str}", flush=True)

                match = tunnel_url_pattern.search(line_str)
                if match:
                    found_url = match.group(0)
                    url_holder["url"] = found_url
                    try:
                        TUNNEL_FILE.write_text(found_url, encoding="utf-8")
                        print(f"[TunnelKeeper] Captured & saved active tunnel URL: {found_url}", flush=True)
                    except Exception as e:
                        print(f"[TunnelKeeper] Failed to save tunnel URL: {e}", flush=True)

            proc.wait()
            print("[TunnelKeeper] SSH process ended. Reconnecting in 3 seconds...", flush=True)

        except Exception as ex:
            print(f"[TunnelKeeper] Error during SSH execution: {ex}. Retrying in 5s...", flush=True)
            time.sleep(5)
        finally:
            stop_event.set()

        time.sleep(3)

if __name__ == "__main__":
    run_tunnel()
