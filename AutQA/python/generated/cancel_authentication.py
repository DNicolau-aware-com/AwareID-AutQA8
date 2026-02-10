"""
Start authentication, capture authToken, then cancel it properly.
"""

from pathlib import Path
import sys, json, time
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from client import post

env = dotenv_values(ROOT / ".env")

def main():
    username = env.get("USERNAME") or "qa_cancel_test"
    print(f"[TEST] Starting then cancelling authentication for {username}")

    # Step 1️⃣ Start authentication
    start_path = "/onboarding/authentication/authenticate"
    start_payload = {"username": username}
    print(f"[INFO] POST {start_path}")
    resp = post(start_path, json=start_payload)
    print("Start Status:", resp.status_code)

    try:
        j = resp.json()
        print(json.dumps(j, indent=2))
    except Exception:
        print(resp.text)
        j = {}

    if resp.status_code not in (200, 202):
        print("[ERROR] Could not start authentication; aborting.")
        return

    auth_token = j.get("authToken")
    if not auth_token:
        print("[ERROR] No authToken returned — cannot cancel session.")
        return

    print(f"[INFO] Received authToken: {auth_token}")

    # Step 2️⃣ Wait briefly before cancelling
    time.sleep(2)

    # Step 3️⃣ Cancel authentication using the authToken
    cancel_path = "/onboarding/authentication/cancel"
    cancel_payload = {"authToken": auth_token}

    print(f"[INFO] POST {cancel_path}")
    resp_cancel = post(cancel_path, json=cancel_payload)
    print("Cancel Status:", resp_cancel.status_code)

    try:
        data = resp_cancel.json()
        print(json.dumps(data, indent=2))
    except Exception:
        print(resp_cancel.text)

    if resp_cancel.status_code in (200, 202):
        print(f"[✅] Authentication cancel flow succeeded for {username}")
    else:
        print(f"[⚠️] Cancel failed: {resp_cancel.text}")

if __name__ == "__main__":
    main()
