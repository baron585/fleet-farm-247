import argparse
import json
import os
import random
import re
import string
import time
from datetime import datetime, timezone
from pathlib import Path
from curl_cffi import requests

KEYS_OUT = Path("ifm_fleet_keys.jsonl")

def log(msg):
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{now}] [IFM-HYPER] {msg}", flush=True)

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def fetch_inboxkitten_otp_or_link(recipient, timeout_sec=45):
    url = f"https://inboxkitten.com/api/v1/mail/list?recipient={recipient}"
    start = time.time()
    log(f"Polling inboxkitten for {recipient}@inboxkitten.com...")
    while time.time() - start < timeout_sec:
        try:
            r = requests.get(url, impersonate="chrome120", timeout=8)
            if r.status_code == 200:
                data = r.json()
                for mail in data:
                    subject = mail.get("message", {}).get("headers", {}).get("subject", "")
                    log(f"Received email: {subject}")
                    storage = mail.get("storage", {})
                    if storage and "key" in storage:
                        s_key = storage["key"]
                        s_region = storage.get("region", "us-west1")
                        body_url = f"https://inboxkitten.com/api/v1/mail/getHtml?region={s_region}&key={s_key}"
                        r_body = requests.get(body_url, impersonate="chrome120", timeout=8)
                        # Check for link or code
                        links = re.findall(r'href=["\'](https?://[a-zA-Z0-9_\-\./\?=&]+)["\']', r_body.text)
                        for l in links:
                            if "verify" in l or "confirm" in l or "token" in l or "auth" in l:
                                return {"type": "link", "val": l}
                        m = re.search(r'\b(\d{6})\b', r_body.text)
                        if m:
                            return {"type": "code", "val": m.group(1)}
        except Exception:
            pass
        time.sleep(2)
    return None

def farm_ifm(browser, worker_id="1"):
    recipient = f"ronfarm_{worker_id}_{random_string(4)}"
    email = f"{recipient}@inboxkitten.com"
    password = f"FleetP@ss{random_string(6)}!"
    
    log(f"Starting IFM 10M Token/day minter for Worker {worker_id} ({email})...")

    context = browser.new_context(viewport={"width": 1280, "height": 900})
    try:
        page = context.new_page()

        log("Navigating to https://platform.ifm.ai/signup?returnTo=%2Fdashboard ...")
        page.goto("https://platform.ifm.ai/signup?returnTo=%2Fdashboard", timeout=45000, wait_until="domcontentloaded")
        time.sleep(3)

        # Fill signup fields
        log("Filling registration form...")
        if page.locator("#displayName").count() > 0:
            page.locator("#displayName").fill(f"Ron Fleet {worker_id}")
        if page.locator("#email").count() > 0:
            page.locator("#email").fill(email)
        if page.locator("#password").count() > 0:
            page.locator("#password").fill(password)
        if page.locator("#confirmPassword").count() > 0:
            page.locator("#confirmPassword").fill(password)

        time.sleep(1)
        submit_btn = page.locator("button:has-text('Create account')")
        if submit_btn.count() > 0:
            log("Clicking 'Create account'...")
            submit_btn.first.click()
            time.sleep(4)

        log(f"Current URL after submit: {page.url}")

        # Check for verification email
        auth_action = fetch_inboxkitten_otp_or_link(recipient, timeout_sec=35)
        if auth_action:
            if auth_action["type"] == "link":
                log(f"Navigating to verification link: {auth_action['val']}")
                page.goto(auth_action["val"], wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
            elif auth_action["type"] == "code":
                log(f"Entering verification code: {auth_action['val']}")
                code_input = page.locator("input[name*='code'], input[type='text']").first
                if code_input.count() > 0:
                    code_input.fill(auth_action["val"])
                    time.sleep(0.5)
                    page.locator("button[type='submit']").click()
                    time.sleep(3)

        # Navigate to API Keys page
        log("Navigating to API Keys console...")
        page.goto("https://platform.ifm.ai/dashboard/api-keys", timeout=30000, wait_until="domcontentloaded")
        time.sleep(3)

        # Attempt to create API Key
        create_btn = page.locator("button:has-text('Create Key'), button:has-text('New Key'), button:has-text('Generate')")
        api_key_val = None
        if create_btn.count() > 0:
            log("Clicking 'Create Key' button...")
            create_btn.first.click()
            time.sleep(2)
            # Check for name prompt if any
            name_input = page.locator("input[placeholder*='name'], input[placeholder*='Key']")
            if name_input.count() > 0:
                name_input.fill("Fleet_9Router_Key")
                page.locator("button:has-text('Create'), button:has-text('Confirm')").click()
                time.sleep(2)
            # Find generated key
            text = page.content()
            key_m = re.search(r'\b(ifm-[a-zA-Z0-9_\-]{24,64}|sk-[a-zA-Z0-9_\-]{24,64})\b', text)
            if key_m:
                api_key_val = key_m.group(1)
                log(f"[★] HARVESTED IFM API KEY: {api_key_val[:10]}...")

        record = {
            "worker_id": worker_id,
            "platform": "IFM_MBZUAI",
            "model": "K2_Horizon_375B",
            "daily_tokens": 10000000,
            "email": email,
            "api_key": api_key_val or "session_registered",
            "final_url": page.url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        with open(KEYS_OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        log(f"[✓] Harvest record logged: {record['email']} ({record['daily_tokens']} tokens)")
        return True
    finally:
        context.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-id", default="1")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    global KEYS_OUT
    if args.output:
        KEYS_OUT = Path(args.output)
    else:
        KEYS_OUT = Path(f"ifm_fleet_keys_cluster_{args.worker_id}.jsonl")

    from camoufox.sync_api import Camoufox
    log(f"Launching Camoufox Browser Engine for Cluster #{args.worker_id} (Target: {args.count} accounts)...")
    with Camoufox(headless=True, humanize=False, geoip=False) as browser:
        for i in range(args.count):
            try:
                farm_ifm(browser, f"{args.worker_id}_{i+1}")
            except Exception as e:
                log(f"[-] Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
