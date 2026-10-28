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

def log(msg, symbol="*"):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] [{symbol}] {msg}", flush=True)

def append_key(record, worker_id=1):
    output_file = BASE_DIR / f"fleet_keys_worker_{worker_id}.jsonl"
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def mint_dahl_account(browser):
    try:
        page = browser.new_page()
        page.goto('https://inference.dahl.global/account', wait_until='load', timeout=35000)
        time.sleep(1.5)

        # Clear cookies for fresh account session
        page.context.clear_cookies()
        page.goto('https://inference.dahl.global/account', wait_until='load', timeout=35000)
        time.sleep(1.2)

        # Klik "Create account" pada desktop dialog / modal
        btn = page.locator('p:has-text("No account yet?") button')
        if not btn.is_visible(timeout=3000):
            btn = page.locator('button:has-text("Create account"):visible').first
        btn.click()
        time.sleep(1.0)

        # Submit form pendaftaran
        submit_btn = page.locator('button[type="submit"]').first
        for _ in range(12):
            t = submit_btn.inner_text().strip()
            if "CHECKING" not in t.upper() and len(t) > 0:
                submit_btn.click()
                break
            time.sleep(0.5)

        time.sleep(2.5)

        # Ekstrak akun, token penuh, dan alokasikan 100M token
        res = page.evaluate("""async () => {
            try {
                const acc = await fetch('/v1/account', { credentials: 'include' }).then(r => r.json());
                const keys = await fetch('/v1/account/keys', { credentials: 'include' }).then(r => r.json());
                
                let full_token = null;
                let key_id = null;
                if (keys && keys.keys && keys.keys.length > 0) {
                    key_id = keys.keys[0].id;
                    full_token = keys.keys[0].token;
                }
                
                let alloc = null;
                if (key_id) {
                    alloc = await fetch('/v1/account/allocate', {
                        method: 'POST',
                        credentials: 'include',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ amount: 100000000, key_id: key_id })
                    }).then(r => r.json());
                }
                
                return {
                    ok: !!full_token,
                    username: acc?.user?.username || ('dahl_' + key_id),
                    token: full_token
                };
            } catch (e) {
                return { ok: false, error: e.toString() };
            }
        }""")
        page.close()
        if res and res.get("ok"):
            return res.get("token"), res.get("username")
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
                append_key(rec, worker_id=args.worker_id)
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
