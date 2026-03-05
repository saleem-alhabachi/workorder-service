#!/usr/bin/env python3
"""Test all API routes against a running server. Usage:
    python scripts/test_routes.py [BASE_URL]
  Default BASE_URL is http://localhost:8000. Set env SECRET_KEY and DATABASE_URL if not in .env.
"""
import sys
from uuid import uuid4

import httpx

# Add project root for app imports
sys.path.insert(0, ".")
from app.core.security import create_access_token

BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")


def ok(name: str, res: httpx.Response, expected: int) -> bool:
    if res.status_code == expected:
        print(f"  \033[92mPASS\033[0m {name} -> {res.status_code}")
        return True
    print(f"  \033[91mFAIL\033[0m {name} -> {res.status_code} (expected {expected})")
    if res.text:
        print(f"         {res.text[:200]}")
    return False


def main() -> None:
    print(f"Testing routes at {BASE_URL}\n")

    token_editor = create_access_token("test-editor", role="editor")
    token_viewer = create_access_token("test-viewer", role="viewer")
    headers_editor = {"Authorization": f"Bearer {token_editor}"}
    headers_viewer = {"Authorization": f"Bearer {token_viewer}"}

    passed = 0
    total = 0
    timeout = 30.0

    try:
        with httpx.Client(base_url=BASE_URL, timeout=timeout) as client:

            # --- Health (no auth) ---
            total += 1
            r = client.get("/health/live")
            if ok("GET /health/live", r, 200):
                passed += 1

            total += 1
            r = client.get("/health/ready")
            if ok("GET /health/ready", r, 200):
                passed += 1
            elif r.status_code == 503:
                print("  \033[93mSKIP\033[0m (DB not connected)")
            else:
                passed += 0

            # --- Metrics (no auth) ---
            total += 1
            r = client.get("/metrics")
            if ok("GET /metrics", r, 200):
                passed += 1

            # --- Create work order (editor) ---
            total += 1
            r = client.post(
                "/api/v1/workorders",
                json={"title": "Route test WO", "description": "Created by test_routes.py"},
                headers=headers_editor,
            )
            if ok("POST /api/v1/workorders (editor)", r, 201):
                passed += 1
                data = r.json()
                wo_id = data.get("id")
            else:
                wo_id = None

            # --- Create as viewer -> 403 ---
            total += 1
            r = client.post(
                "/api/v1/workorders",
                json={"title": "X", "description": "Y"},
                headers=headers_viewer,
            )
            if ok("POST /api/v1/workorders (viewer) -> 403", r, 403):
                passed += 1

            # --- Create without auth -> 401 ---
            total += 1
            r = client.post(
                "/api/v1/workorders",
                json={"title": "X", "description": "Y"},
            )
            if ok("POST /api/v1/workorders (no auth) -> 401", r, 401):
                passed += 1

            # --- List work orders ---
            total += 1
            r = client.get("/api/v1/workorders", headers=headers_viewer)
            if ok("GET /api/v1/workorders", r, 200):
                passed += 1

            # --- Get by id ---
            if wo_id:
                total += 1
                r = client.get(f"/api/v1/workorders/{wo_id}", headers=headers_viewer)
                if ok("GET /api/v1/workorders/{id}", r, 200):
                    passed += 1

                # --- Update status ---
                total += 1
                r = client.patch(
                    f"/api/v1/workorders/{wo_id}/status",
                    json={"status": "in_progress"},
                    headers=headers_editor,
                )
                if ok("PATCH /api/v1/workorders/{id}/status (in_progress)", r, 200):
                    passed += 1

                total += 1
                r = client.patch(
                    f"/api/v1/workorders/{wo_id}/status",
                    json={"status": "completed"},
                    headers=headers_editor,
                )
                if ok("PATCH /api/v1/workorders/{id}/status (completed)", r, 200):
                    passed += 1

            # --- Get nonexistent -> 404 ---
            total += 1
            fake_id = str(uuid4())
            r = client.get(f"/api/v1/workorders/{fake_id}", headers=headers_viewer)
            if ok("GET /api/v1/workorders/{fake_id} -> 404", r, 404):
                passed += 1

            # --- Invalid status transition -> 422 ---
            if wo_id:
                total += 1
                r = client.patch(
                    f"/api/v1/workorders/{wo_id}/status",
                    json={"status": "pending"},
                    headers=headers_editor,
                )
                if ok("PATCH status COMPLETED->PENDING -> 422", r, 422):
                    passed += 1

    except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
        print(f"\033[91mServer not responding at {BASE_URL}\033[0m")
        print(f"  {type(e).__name__}: {e}")
        print("  Make sure the app is running: uvicorn app.main:app --reload")
        sys.exit(1)

    print()
    if passed == total:
        print(f"\033[92mAll {total} route checks passed.\033[0m")
    else:
        print(f"\033[91m{passed}/{total} passed.\033[0m")
        sys.exit(1)


if __name__ == "__main__":
    main()
