import requests
import uuid
import time

URL = "http://localhost:19090/commands/user/dual-create"
CID = str(uuid.uuid4())

payload = {
    "command_id": CID,
    "email": f"dual-{uuid.uuid4().hex[:4]}@example.com",
    "first_name": "Dual",
    "last_name": "Test",
    "age": 42
}

print(f"Sending first request (cid={CID})...")
r1 = requests.post(URL, json=payload)
print(f"Response 1: {r1.status_code} - {r1.json()}")

print(f"\nSending second request (same cid={CID})...")
r2 = requests.post(URL, json=payload)
print(f"Response 2: {r2.status_code} - {r2.json()}")

if r1.json()['event_id'] == r2.json()['event_id']:
    print("\nSUCCESS: Idempotency works (received same event_id)")
else:
    print("\nFAILURE: Idempotency failed (received different event_id)")
