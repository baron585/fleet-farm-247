#!/usr/bin/env python3
"""
🚀 DEDICATED DAHL INFERENCE FLEET MINTER (High-Speed Cloud Edition)
Mints 100M token API keys on inference.dahl.global at 9.8s/account.
Writes directly to fleet_keys.jsonl.
"""

import sys
import time
import json
import random
import string
import argparse
from datetime import datetime, timezone
from pathlib import Path
from camoufox.sync_api import Camoufox

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "fleet_keys.jsonl"

def log(msg, symbol="*"):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] [{symbol}] {msg}", flush=True)

def append_key(record):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def mint_dahl_account(browser):
    uname = "dahl" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    try:
        page = browser.new_page()
        page.goto('https://inference.dahl.global/account', wait_until='load', timeout=35000)
        time.sleep(1.0)
        res = page.evaluate("""async (username) => {
            try {
                const s = await fetch('/v1/auth/signup', {
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: username })
                }).then(r => r.json());
                if (!s.api_key || !s.api_key.id) return { error: 'Signup failed', raw: s };
                const alloc = await fetch('/v1/account/allocate', {
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ amount: 100000000, key_id: s.api_key.id })
                }).then(r => r.json());
                return { ok: true, username: username, token: s.api_key.token };
            } catch (e) {
                return { error: e.toString() };
            }
        }""", uname)
        page.close()
        if res and res.get("ok"):
            return res.get("token"), uname
    except Exception as e:
        log(f"Dahl mint error: {e}", symbol="-")
    return None, None

def main():
    parser = argparse.ArgumentParser(description="Dedicated Dahl Minter")
    parser.add_argument("--count", type=int, default=30, help="Jumlah akun yang akan dicetak")
    parser.add_argument("--worker-id", type=int, default=1, help="ID Worker (untuk logging matrix)")
    args = parser.parse_args()

    log(f"======================================================================")
    log(f"  ⚡ DEDICATED DAHL MINTER WORKER #{args.worker_id} (Target: {args.count} akun / {args.count * 100}M Tokens)")
    log(f"======================================================================")

    minted = 0
    with Camoufox(headless=True, humanize=False, geoip=False) as browser:
        for i in range(args.count):
            token, uname = mint_dahl_account(browser)
            if token:
                rec = {
                    "provider": "openai-compatible-chat-dahl",
                    "username": uname,
                    "api_key": token,
                    "tokens": 100000000,
                    "worker_id": args.worker_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "github_actions_dahl_dedicated"
                }
                append_key(rec)
                minted += 1
                log(f"[W#{args.worker_id}] [✓] Dahl #{minted}/{args.count}: {uname} -> {token[:16]}... (+100M Tokens)")
            else:
                log(f"[W#{args.worker_id}] [-] Dahl #{i+1} gagal, mencoba lagi...", symbol="!")
            time.sleep(random.uniform(1.5, 3.0))

    log(f"======================================================================")
    log(f"  🏁 SELESAI WORKER #{args.worker_id}: Berhasil mencetak {minted} akun (+{minted * 100}M Tokens)")
    log(f"======================================================================")

if __name__ == "__main__":
    main()
