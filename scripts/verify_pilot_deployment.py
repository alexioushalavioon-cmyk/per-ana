from __future__ import annotations

import json
import os
import sys
import httpx

API = os.environ.get("PILOT_API_URL", "").rstrip("/")
TOKEN = os.environ.get("PILOT_USER_ACCESS_TOKEN")
if not API or not TOKEN:
    raise SystemExit("PILOT_API_URL and PILOT_USER_ACCESS_TOKEN are required")

headers = {"Authorization": f"Bearer {TOKEN}"}
results = {}
with httpx.Client(timeout=30.0, follow_redirects=True) as client:
    for path in ("/health", "/ready"):
        r = client.get(API + path)
        results[path] = r.status_code
        r.raise_for_status()
    p = client.get(API + "/api/v1/governance/usage-policy", headers=headers)
    p.raise_for_status(); version = p.json()["version"]
    a = client.post(API + "/api/v1/governance/usage-policy/accept", headers=headers, json={"version": version})
    a.raise_for_status()
    c = client.post(API + "/api/v1/cases", headers=headers, json={
        "title": "Pilot verification case",
        "description": "External deployment smoke test",
        "analytical_question": "کدام بازیگران بر اجرای سیاست اثر می‌گذارند؟",
        "processing_mode": "quick",
        "sensitivity": "internal",
    })
    c.raise_for_status(); case_id = c.json()["id"]
    results["case_id"] = case_id
    listed = client.get(API + "/api/v1/cases", headers=headers)
    listed.raise_for_status(); assert any(x["id"] == case_id for x in listed.json())
    results["authenticated_case_flow"] = "pass"
print(json.dumps(results, ensure_ascii=False, indent=2))
