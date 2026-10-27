#!/usr/bin/env python3
"""
⚡ 24/7 ALL-IN-ONE AUTONOMOUS FLEET MINTER (Complete Cloud Runner Edition)
Integrated Farm Engines:
1. Dahl Inference (100M Tokens per account)
2. Gonka24 (Zero-Captcha REST + Firebase Session -> sk-... API Keys)
3. TokenHarbor (Automated Turnstile / Tempmail Collector)
4. Grok xAI (xAI OAuth Signup via farmon.my.id)
5. Jio Gemini Farm (Firebase Panel Interception & Google One Links)
"""

import os
import sys
import time
import json
import random
import string
import urllib.request
import urllib.error
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "fleet_keys.jsonl"
JIO_LINKS_FILE = BASE_DIR / "jio_activation_links.txt"

def log(msg, symbol="*"):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] [{symbol}] {msg}", flush=True)

def append_key(record):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ─────────────────────────────────────────────────────────────────────────────
# 1. DAHL INFERENCE ENGINE (100M Tokens / Akun)
# ─────────────────────────────────────────────────────────────────────────────
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
    except Exception as e:
        log(f"Dahl error: {e}", symbol="-")
    return None, None

def run_dahl_farm(browser, count=8):
    log(f"--- [ENGINE 1] DAHL INFERENCE (Target: {count} akun / {count * 100}M Tokens) ---")
    minted = 0
    for i in range(count):
        token, uname = mint_dahl_account(browser)
        if token:
            rec = {
                "provider": "openai-compatible-chat-dahl",
                "username": uname,
                "api_key": token,
                "tokens": 100000000,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "github_actions_cloud"
            }
            append_key(rec)
            minted += 1
            log(f"  [✓] Dahl #{i+1}: {uname} -> {token[:16]}... (100M Tokens)")
        time.sleep(random.uniform(2.0, 3.5))
    return minted

# ─────────────────────────────────────────────────────────────────────────────
# 2. GONKA24 ENGINE (Minimax & DeepSeek sk-... Keys)
# ─────────────────────────────────────────────────────────────────────────────
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

def mint_gonka_key_via_browser(browser, email, password, key_name="cloud-key"):
    page = browser.new_page()
    try:
        page.goto("https://gonka24.com/auth/login", timeout=30000)
        page.wait_for_selector('input[type="email"]', timeout=15000)
        page.fill('input[type="email"]', email)
        page.fill('input[type="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard**", timeout=25000)
        time.sleep(1.5)

        creation_script = f"""async () => {{
            let token = await new Promise((resolve) => {{
                const req = indexedDB.open('firebaseLocalStorageDb');
                req.onsuccess = () => {{
                    const db = req.result;
                    if (!db.objectStoreNames.contains('firebaseLocalStorage')) return resolve(null);
                    const tx = db.transaction('firebaseLocalStorage', 'readonly');
                    const store = tx.objectStore('firebaseLocalStorage');
                    const getAll = store.getAll();
                    getAll.onsuccess = () => {{
                        for (let item of getAll.result || []) {{
                            if (item.value && item.value.stsTokenManager) {{
                                return resolve(item.value.stsTokenManager.accessToken);
                            }}
                        }}
                        resolve(null);
                    }};
                    getAll.onerror = () => resolve(null);
                }};
                req.onerror = () => resolve(null);
            }});
            if (!token) return {{ ok: false, error: 'Firebase session token not found' }};
            const resp = await fetch('/api/keys', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token }},
                body: JSON.stringify({{ name: '{key_name}' }})
            }});
            if (!resp.ok) return {{ ok: false, status: resp.status, error: await resp.text() }};
            const data = await resp.json();
            return {{ ok: true, keyData: data }};
        }}"""

        res = page.evaluate(creation_script)
        page.close()
        return res
    except Exception as e:
        page.close()
        return {"ok": False, "error": str(e)}

def run_gonka_farm(browser, count=2):
    log(f"--- [ENGINE 2] GONKA24 OPENAI-COMPATIBLE (Target: {count} akun) ---")
    minted = 0
    for i in range(count):
        prefix = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"user_{prefix}@gmail.com"
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(random.choices(chars, k=16))

        reg = register_gonka_rest(email, password)
        if not reg.get("success"):
            continue

        key_res = mint_gonka_key_via_browser(browser, email, password)
        if key_res and key_res.get("ok"):
            raw_key = key_res.get("keyData", {}).get("rawKey")
            if raw_key:
                rec = {
                    "provider": "openai-compatible-chat-gonka24",
                    "email": email,
                    "api_key": raw_key,
                    "models": ["minimax-m2.7", "deepseek-v4-flash-0731", "glm-5.3-flash"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "github_actions_cloud"
                }
                append_key(rec)
                minted += 1
                log(f"  [✓] Gonka #{i+1}: {email} -> {raw_key[:20]}...")
        time.sleep(random.uniform(2.0, 3.5))
    return minted

# ─────────────────────────────────────────────────────────────────────────────
# 3. TOKENHARBOR ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def run_tokenharbor_farm(count=2):
    log(f"--- [ENGINE 3] TOKENHARBOR HARVESTER (Target: {count} akun) ---")
    script = BASE_DIR / "tokenharbor_farmer.py"
    if not script.exists():
        log("[!] tokenharbor_farmer.py tidak ditemukan, lewati.")
        return 0
    cmd = [sys.executable, str(script), "--count", str(count)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        added = 0
        import re
        keys = re.findall(r"(thk_live_[A-Za-z0-9_-]{20,})", res.stdout)
        for k in set(keys):
            rec = {
                "provider": "openai-compatible-chat-tokenharbor",
                "api_key": k,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "github_actions_cloud"
            }
            append_key(rec)
            added += 1
            log(f"  [✓] TokenHarbor: {k[:18]}...")
        return added
    except Exception as e:
        log(f"TokenHarbor error: {e}", symbol="-")
        return 0

# ─────────────────────────────────────────────────────────────────────────────
# 4. GROK xAI ENGINE (via farmon.my.id)
# ─────────────────────────────────────────────────────────────────────────────
def run_grok_farm(count=1):
    log(f"--- [ENGINE 4] GROK xAI CLI ENGINE (Target: {count} akun) ---")
    script = BASE_DIR / "grok_cli" / "main.py"
    if not script.exists():
        log("[!] grok_cli/main.py tidak ditemukan, lewati.")
        return 0
    cmd = [sys.executable, str(script), "--count", str(count), "--workers", "1", "--proxy-mode", "direct", "--no-9router"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        # Parse created credentials
        cred_file = BASE_DIR / "grok_cli" / "grok_credentials.json"
        if cred_file.exists():
            with open(cred_file, "r", encoding="utf-8") as f:
                creds = json.load(f)
                if creds:
                    latest = creds[-1]
                    rec = {
                        "provider": "grok-cli",
                        "email": latest.get("email"),
                        "refresh_token": latest.get("refresh_token"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "github_actions_cloud"
                    }
                    append_key(rec)
                    log(f"  [✓] Grok xAI Account: {latest.get('email')}")
                    return 1
    except Exception as e:
        log(f"Grok error: {e}", symbol="-")
    return 0

# ─────────────────────────────────────────────────────────────────────────────
# 5. JIO GEMINI FARM ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def run_jio_farm(sweep_count=3):
    log(f"--- [ENGINE 5] JIO GEMINI PROMO SWEEPER ({sweep_count} sweeps) ---")
    script = BASE_DIR / "jio_gemini_farm.py"
    if not script.exists():
        log("[!] jio_gemini_farm.py tidak ditemukan, lewati.")
        return 0
    cmd = [sys.executable, str(script), "--target", "1", "--sweep", str(sweep_count)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        # Check if fresh links generated
        links_file = BASE_DIR / "fresh_links.txt"
        if links_file.exists():
            with open(links_file, "r", encoding="utf-8") as f:
                links = [l.strip() for l in f if l.strip()]
                for l in links:
                    with open(JIO_LINKS_FILE, "a", encoding="utf-8") as out_f:
                        out_f.write(l + "\n")
                    log(f"  [✓] JIO GEMINI LINK: {l}")
                return len(links)
    except Exception as e:
        log(f"Jio error: {e}", symbol="-")
    return 0

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ALL-IN-ONE ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="24/7 Complete Cloud Fleet Minter")
    parser.add_argument("--dahl-count", type=int, default=35, help="Target Dahl akun")
    parser.add_argument("--gonka-count", type=int, default=2, help="Target Gonka24 akun")
    parser.add_argument("--th-count", type=int, default=1, help="Target TokenHarbor akun")
    parser.add_argument("--grok-count", type=int, default=1, help="Target Grok xAI akun")
    parser.add_argument("--jio-sweeps", type=int, default=3, help="Jumlah sweep Jio panel")
    args = parser.parse_args()

    log("======================================================================")
    log("  🚀 COMPLETE MULTI-ENGINE 24/7 CLOUD FLEET MINTER (GITHUB ACTIONS)   ")
    log("======================================================================")

    from camoufox.sync_api import Camoufox

    with Camoufox(headless=True, humanize=False, geoip=False) as browser:
        # 1. Harvest Dahl (100M per akun)
        dahl_total = run_dahl_farm(browser, count=args.dahl_count)

        # 2. Harvest Gonka24
        gonka_total = run_gonka_farm(browser, count=args.gonka_count)

    # 3. Harvest TokenHarbor
    th_total = run_tokenharbor_farm(count=args.th_count)

    # 4. Harvest Grok xAI via Cloudflare Worker
    grok_total = run_grok_farm(count=args.grok_count)

    # 5. Sweep Jio Gemini
    jio_total = run_jio_farm(sweep_count=args.jio_sweeps)

    log("======================================================================")
    log(f"🎉 SIKLUS CLOUD SELESAI:")
    log(f"  • Dahl: +{dahl_total} akun (+{dahl_total * 100}M Tokens)")
    log(f"  • Gonka24: +{gonka_total} akun")
    log(f"  • TokenHarbor: +{th_total} akun")
    log(f"  • Grok xAI: +{grok_total} akun")
    log(f"  • Jio Gemini: +{jio_total} links")
    log("======================================================================")

if __name__ == "__main__":
    main()
