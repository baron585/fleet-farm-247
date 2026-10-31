import argparse
import json
import os
import random
import re
import string
import time
from datetime import datetime, timezone
from pathlib import Path

DOMAINS_OUT = Path("fleet_domains.jsonl")
PROMO_CODE = "30-mTsM-IDH"

TLDS = [".my.id", ".web.id", ".biz.id"]

def random_string(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def log(msg):
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{now}] [IDWEBHOST-FARM] {msg}", flush=True)

def farm_domain(domain_name, worker_id="1"):
    from camoufox.sync_api import Camoufox

    log(f"Initiating domain claim for: {domain_name} using promo: {PROMO_CODE}")
    
    with Camoufox(headless=True, humanize=True, geoip=False) as browser:
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # Step 1: Open landing
        log(f"Navigating to https://order.idwebhost.com/domain-gratis/{domain_name}...")
        page.goto(f"https://order.idwebhost.com/domain-gratis/{domain_name}", timeout=60000, wait_until="domcontentloaded")
        time.sleep(3)

        # Check if domain available
        content = page.content()
        if "Domain tidak valid" in content or "tidak tersedia" in content:
            log(f"[-] Domain {domain_name} unavailable or invalid.")
            return False

        log(f"[+] Domain {domain_name} ready on checkout page.")

        # Step 2: Fill Coupon Code
        coupon_input = page.locator("#order-coupon")
        if coupon_input.count() > 0:
            coupon_input.fill(PROMO_CODE)
            log(f"Filled coupon code: {PROMO_CODE}")
            time.sleep(1)

            # Click 'Pakai' button
            apply_btn = page.locator("button:has-text('Pakai')")
            if apply_btn.count() > 0:
                apply_btn.click()
                log("Clicked 'Pakai' coupon button.")

        # Step 3: Wait for Turnstile auto-solve
        log("Waiting for Turnstile response / coupon validation...")
        deadline = time.time() + 45
        coupon_applied = False
        while time.time() < deadline:
            text = page.content()
            if "berhasil digunakan" in text or "Hapus kupon" in text:
                coupon_applied = True
                log("[✓] Coupon applied successfully!")
                break
            if "wajib masuk grup" in text or "gagal" in text or "habis" in text:
                log(f"Notice from page: {text[:200]}")
                break
            time.sleep(2)

        # Step 4: Submit Save Form
        save_btn = page.locator("form[action*='domain-gratis/save'] button[type='submit']")
        if save_btn.count() > 0:
            log("Clicking save / continue claim button...")
            save_btn.click()
            time.sleep(5)

        # Record record
        record = {
            "worker_id": worker_id,
            "domain": domain_name,
            "promo_code": PROMO_CODE,
            "coupon_applied": coupon_applied,
            "claimed_at": datetime.now(timezone.utc).isoformat(),
            "final_url": page.url
        }

        with open(DOMAINS_OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        log(f"[★] Result saved to {DOMAINS_OUT}: {record}")
        return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-id", default="1")
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--prefix", default="rondev")
    args = parser.parse_args()

    for i in range(args.count):
        tld = random.choice(TLDS)
        domain = f"{args.prefix}{random_string(4)}{tld}"
        try:
            farm_domain(domain, args.worker_id)
        except Exception as e:
            log(f"[-] Error claiming {domain}: {e}")
        time.sleep(3)

if __name__ == "__main__":
    main()
