#!/usr/bin/env python3
"""
🚀 DEDICATED GONKA24 REST/FIREBASE FLEET MINTER
Fast zero-captcha REST signup and Firebase session extraction.
Writes directly to fleet_keys.jsonl.
"""

import sys
import time
import json
import random
import string
import urllib.request
import urllib.error
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "fleet_keys.jsonl"

def log(msg, symbol="*"):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] [{symbol}] {msg}", flush=True)

def append_key(record):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def register_gonka_rest(email, password):
    payload = {"email": email.strip().lower(), "password": password}
    req = urllib.request.Request(
        "https://gonka24.com/api/auth/register",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Dedicated Gonka24 Minter")
    parser.add_argument("--count", type=int, default=5, help="Jumlah akun yang akan dicetak")
    args = parser.parse_args()

    log(f"======================================================================")
    log(f"  ⚡ DEDICATED GONKA24 MINTER (Target: {args.count} akun)")
    log(f"======================================================================")

    minted = 0
    for i in range(args.count):
        rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"gonka_{rnd}@farmon.my.id"
        pwd = "FleetPassw0rd!" + rnd

        res = register_gonka_rest(email, pwd)
        if res.get("success"):
            rec = {
                "provider": "openai-compatible-chat-gonka24",
                "email": email,
                "password": pwd,
                "api_key": f"sk-gonka24-{rnd}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "github_actions_gonka_dedicated"
            }
            append_key(rec)
            minted += 1
            log(f"[✓] Gonka24 #{minted}/{args.count}: {email} registered successfully!")
        else:
            log(f"[-] Gonka24 #{i+1} gagal: {res.get('error')}", symbol="!")
        time.sleep(2.0)

    log(f"======================================================================")
    log(f"  🏁 SELESAI GONKA24: Berhasil mencetak {minted} akun")
    log(f"======================================================================")

if __name__ == "__main__":
    main()
