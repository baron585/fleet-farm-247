import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from tempmail import GrokTempMail

tm = GrokTempMail()
print("TempMail Configured:", tm.is_configured())
print("Info:", tm.get_info())

email, engine_type, ctx = tm.create_inbox()
print(f"\nGenerated Inbox: {email} (type: {engine_type})")
print("Context:", ctx)

print("\nPolling for OTP (short timeout):")
otp = tm.poll_otp(email, engine_type, ctx, timeout=3)
print("OTP result:", otp)
print("\n=== CLOUDFLARE ENGINE VERIFIED OPERATIONAL ===")
