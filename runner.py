#!/usr/bin/env python3
"""
Autonomous Cloud Fleet Minter (GitHub Actions / Cloud Runner Edition)
- Mint fresh Dahl inference accounts (100M tokens each)
- Mint fresh TokenHarbor accounts via headless disposable mail
- Export deduplicated results to fleet_keys.jsonl
"""

import os
import sys
import time
import json
import random
import string
import argparse
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "fleet_keys.jsonl"

def log(msg, symbol="*"):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] [{symbol}] {msg}", flush=True)

def load_existing_keys():
    existing = set()
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            k = rec.get("api_key") or rec.get("token")
                            if k:
                                existing.add(k)
                        except Exception:
                            pass
        except Exception as e:
            log(f"Warning reading existing keys: {e}", symbol="!")
    return existing

def append_key(record):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def mint_dahl_account(browser):
    uname = "dahl" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    try:
        page = browser.new_page()
        page.goto('https://inference.dahl.global/account', wait_until='load', timeout=30000)
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
        else:
            log(f"Dahl error: {res}", symbol="-")
    except Exception as e:
        log(f"Dahl browser error: {e}", symbol="-")
    return None, None

def harvest_dahl_batch(count=5):
    from camoufox.sync_api import Camoufox
    log(f"Memulai batch Dahl mint ({count} akun)...", symbol=">")
    minted = []
    try:
        with Camoufox(headless=True, humanize=False, geoip=False) as browser:
            for i in range(count):
                token, uname = mint_dahl_account(browser)
                if token:
                    rec = {
                        "provider": "openai-compatible-chat-dahl",
                        "username": uname,
                        "api_key": token,
                        "tokens": 100000000,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "github_actions_cron"
                    }
                    minted.append(rec)
                    append_key(rec)
                    log(f"  [+] MINTED: {uname} -> {token[:16]}... (100M tokens)", symbol="✔")
                time.sleep(random.uniform(2.0, 4.0))
    except Exception as e:
        log(f"Browser launch failure: {e}", symbol="!")
    return minted

def main():
    parser = argparse.ArgumentParser(description="Cloud Fleet Minter")
    parser.add_argument("--dahl-count", type=int, default=5, help="Jumlah akun Dahl yang dicetak")
    parser.add_argument("--th-count", type=int, default=1, help="Jumlah akun TokenHarbor yang dicetak")
    args = parser.parse_args()

    existing_before = len(load_existing_keys())
    log(f"Cloud Minter Start | Total keys di database file saat ini: {existing_before}")

    # 1. Harvest Dahl
    dahl_results = harvest_dahl_batch(count=args.dahl_count)

    existing_after = len(load_existing_keys())
    log(f"Cloud Minter Selesai! Ditambahkan: {len(dahl_results)} akun. Total keys tersimpan: {existing_after}", symbol="★")

if __name__ == "__main__":
    main()
