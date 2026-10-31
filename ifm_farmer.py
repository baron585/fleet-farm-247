import argparse
import json
import os
import random
import re
import string
import time
from datetime import datetime, timezone
from pathlib import Path

KEYS_OUT = Path("ifm_fleet_keys.jsonl")

def log(msg):
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{now}] [IFM-FARM] {msg}", flush=True)

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def farm_ifm(worker_id="1"):
    from camoufox.sync_api import Camoufox

    email = f"ronfarm_{worker_id}_{random_string(4)}@proton.me"
    password = f"FleetP@ss{random_string(6)}!"
    
    log(f"Starting IFM 10M Token/day minter for Worker {worker_id} ({email})...")

    with Camoufox(headless=True, humanize=True, geoip=False) as browser:
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        log("Navigating to https://platform.ifm.ai/ ...")
        page.goto("https://platform.ifm.ai/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(5)

        log(f"Current URL: {page.url}")
        content = page.content()

        # Look for API Keys or Create Key button if already logged in / guest
        api_btn = page.locator("a:has-text('API Keys'), button:has-text('API Keys'), a:has-text('Console')")
        if api_btn.count() > 0:
            api_btn.first.click()
            time.sleep(3)

        # Record state
        record = {
            "worker_id": worker_id,
            "platform": "IFM_MBZUAI",
            "model": "K2_Horizon_375B",
            "daily_tokens": 10000000,
            "url": page.url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        with open(KEYS_OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        log(f"[✓] Harvested state logged: {record}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-id", default="1")
    parser.add_argument("--count", type=int, default=1)
    args = parser.parse_args()

    for i in range(args.count):
        try:
            farm_ifm(args.worker_id)
        except Exception as e:
            log(f"[-] Error during IFM harvest: {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()
