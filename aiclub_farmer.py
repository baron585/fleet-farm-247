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

DOMAINS_OUT = Path("fleet_domains.jsonl")

def log(msg):
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{now}] [AICLUB-FARM] {msg}", flush=True)

def random_string(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def fetch_inboxkitten_otp(recipient, timeout_sec=60):
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
                    m = re.search(r'\b(\d{6})\b', subject)
                    if m:
                        code = m.group(1)
                        log(f"[✓] OTP code found in subject: {code}")
                        return code
                    storage = mail.get("storage", {})
                    if storage and "key" in storage:
                        s_key = storage["key"]
                        s_region = storage.get("region", "us-west1")
                        body_url = f"https://inboxkitten.com/api/v1/mail/getHtml?region={s_region}&key={s_key}"
                        r_body = requests.get(body_url, impersonate="chrome120", timeout=8)
                        m2 = re.search(r'\b(\d{6})\b', r_body.text)
                        if m2:
                            code = m2.group(1)
                            log(f"[✓] OTP code found in email body: {code}")
                            return code
        except Exception as e:
            log(f"Poll warning: {e}")
        time.sleep(4)
    log("[-] Timeout waiting for OTP from inboxkitten.")
    return None

def farm_aiclub_subdomain(subdomain_name, domain_base="std.ai.id", target="baron585.github.io"):
    from camoufox.sync_api import Camoufox

    recipient = f"ron_{random_string(6)}"
    email = f"{recipient}@inboxkitten.com"
    password = f"FleetP@ss{random_string(4)}!"
    
    log(f"Starting AICLUB claim: {subdomain_name}.{domain_base} -> {target}")
    log(f"Using mailbox: {email}")

    with Camoufox(headless=True, humanize=True, geoip=False) as browser:
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # Step 1: Open landing
        log("Navigating to https://aiclub.ai.id/masuk.html ...")
        page.goto("https://aiclub.ai.id/masuk.html", timeout=45000, wait_until="domcontentloaded")
        time.sleep(4)

        # Step 2: Switch to Register tab
        log("Clicking 'Daftar' tab...")
        tab_reg = page.locator("#tab-reg")
        if tab_reg.count() > 0:
            tab_reg.click()
            time.sleep(2)

        # Step 3: Fill registration form
        page.locator("#rg-email").fill(email)
        page.locator("#rg-pass").fill(password)
        log("Filled email and password. Waiting for Cloudflare Turnstile auto-solve...")

        # Wait for Turnstile
        deadline = time.time() + 45
        ts_token = None
        while time.time() < deadline:
            ts_token = page.evaluate("""() => {
                const el = document.querySelector('#ts-register input[name="cf-turnstile-response"]') || 
                           document.querySelector('input[name="cf-turnstile-response"]');
                return el && el.value ? el.value : '';
            }""")
            if ts_token:
                log(f"[✓] Turnstile solved! Token prefix: {ts_token[:16]}...")
                break
            time.sleep(2)

        if not ts_token:
            log("[-] Turnstile token not obtained, trying click submit anyway...")

        # Submit registration
        log("Submitting registration form...")
        page.locator("#form-reg button[type='submit']").click()
        time.sleep(6)

        # Check if form-otp is visible
        otp_visible = page.locator("#form-otp").is_visible()
        log(f"OTP form visible: {otp_visible}")

        # Step 4: Retrieve OTP from inboxkitten
        otp_code = fetch_inboxkitten_otp(recipient, timeout_sec=60)
        if not otp_code:
            log("[-] Failed to get OTP. Aborting this run.")
            return False

        # Step 5: Fill OTP digits
        otp_inputs = page.locator(".otp-box input")
        count = otp_inputs.count()
        log(f"Filling {len(otp_code)} digits into {count} OTP inputs...")
        for i, char in enumerate(otp_code):
            if i < count:
                otp_inputs.nth(i).fill(char)
                time.sleep(0.2)

        # Submit OTP
        log("Submitting OTP form...")
        page.locator("#form-otp button[type='submit']").click()
        time.sleep(6)

        # Step 6: Wait for Dashboard redirection
        log(f"Current URL after OTP: {page.url}")
        if "dashboard" not in page.url:
            page.goto("https://aiclub.ai.id/dashboard.html", timeout=30000, wait_until="domcontentloaded")
            time.sleep(4)

        token = page.evaluate("() => localStorage.getItem('token')")
        log(f"Auth Token present: {bool(token)}")

        # Step 7: Claim Subdomain via API
        log(f"Claiming CNAME subdomain: {subdomain_name}.{domain_base} -> {target}")
        claim_result = page.evaluate("""
            async ({ name, domain, type, target }) => {
                const res = await fetch('/api/claim', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                    },
                    body: JSON.stringify({ name, domain, type, target })
                });
                return await res.json();
            }
        """, {"name": subdomain_name, "domain": domain_base, "type": "CNAME", "target": target})

        log(f"[★] Claim API Result: {claim_result}")

        record = {
            "platform": "AICLUB",
            "fqdn": f"{subdomain_name}.{domain_base}",
            "type": "CNAME",
            "target": target,
            "claimed_email": email,
            "api_response": claim_result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        with open(DOMAINS_OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        log(f"[✓] Successfully recorded in {DOMAINS_OUT}")
        return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--prefix", default="rondev")
    args = parser.parse_args()

    for i in range(args.count):
        sub = f"{args.prefix}{random_string(4)}"
        try:
            farm_aiclub_subdomain(sub)
        except Exception as e:
            log(f"[-] Error: {e}")
        time.sleep(3)

if __name__ == "__main__":
    main()
