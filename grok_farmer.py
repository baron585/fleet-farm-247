#!/usr/bin/env python3
"""
🚀 DEDICATED GROK xAI FLEET MINTER (Cloud Edition)
Registers Grok xAI OAuth accounts via Cloudflare Worker @farmon.my.id.
Extracts refresh_token and writes directly to fleet_keys.jsonl.
"""

import os
import sys
import time
import json
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "fleet_keys.jsonl"
GROK_DIR = BASE_DIR / "grok_cli"

def log(msg, symbol="*"):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] [{symbol}] {msg}", flush=True)

def append_key(record):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description="Dedicated Grok xAI Minter")
    parser.add_argument("--count", type=int, default=3, help="Jumlah akun yang akan dicetak")
    args = parser.parse_args()

    log("======================================================================")
    log(f"  ⚡ DEDICATED GROK xAI FLEET MINTER (Target: {args.count} akun)")
    log("======================================================================")

    script = GROK_DIR / "main.py"
    if not script.exists():
        log("grok_cli/main.py tidak ditemukan!", "!")
        return 1

    cmd = [
        sys.executable,
        str(script),
        "--count", str(args.count),
        "--workers", "1",
        "--proxy-mode", "direct",
        "--no-9router"
    ]

    log(f"Menjalankan script: {' '.join(cmd)}...")
    try:
        proc = subprocess.run(cmd, cwd=str(GROK_DIR), capture_output=True, text=True, timeout=600)
        print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
    except Exception as e:
        log(f"Error menjalankan Grok engine: {e}", "!")

    cred_file = GROK_DIR / "grok_credentials.json"
    minted = 0
    if cred_file.exists():
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                creds = json.load(f)
            # Ambil akun terbaru sejumlah target
            recent = creds[-args.count:] if len(creds) >= args.count else creds
            for c in recent:
                email = c.get("email")
                rt = c.get("refresh_token")
                if email and rt:
                    rec = {
                        "provider": "grok-cli",
                        "email": email,
                        "refresh_token": rt,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "github_actions_grok_dedicated"
                    }
                    append_key(rec)
                    minted += 1
                    log(f"[✓] Grok xAI Account: {email} -> {rt[:15]}...")
        except Exception as e:
            log(f"Error membaca credentials Grok: {e}", "!")

    log("======================================================================")
    log(f"  🏁 SELESAI GROK xAI: Berhasil mencetak {minted} akun")
    log("======================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
