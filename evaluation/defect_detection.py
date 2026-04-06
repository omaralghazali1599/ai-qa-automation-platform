import httpx
import json
from typing import List, Dict

# -------------------------------------------------------
# DEFECT REGISTRY
# Known bugs seeded into each test app.
# Each defect has an id, description, app, endpoint,
# a request that SHOULD catch it, and what a passing
# (non-buggy) response looks like.
# -------------------------------------------------------

DEFECTS = [
    # --- AUTH APP defects (5) ---
    {
        "id": "DEF-A01",
        "app": "auth",
        "description": "Register accepts password shorter than 8 chars",
        "base_url": "http://127.0.0.1:5001",
        "method": "POST",
        "endpoint": "/register",
        "payload": {
            "name": "Test User",
            "email": "defect1@test.com",
            "password": "123"
        },
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-A02",
        "app": "auth",
        "description": "Register accepts invalid email format",
        "base_url": "http://127.0.0.1:5001",
        "method": "POST",
        "endpoint": "/register",
        "payload": {
            "name": "Test User",
            "email": "notanemail",
            "password": "pass1234"
        },
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-A03",
        "app": "auth",
        "description": "Login succeeds with empty password",
        "base_url": "http://127.0.0.1:5001",
        "method": "POST",
        "endpoint": "/login",
        "payload": {
            "email": "omar@test.com",
            "password": ""
        },
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-A04",
        "app": "auth",
        "description": "Forgot password accepts empty email",
        "base_url": "http://127.0.0.1:5001",
        "method": "POST",
        "endpoint": "/forgot-password",
        "payload": {"email": ""},
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-A05",
        "app": "auth",
        "description": "Reset password accepts password shorter than 8 chars",
        "base_url": "http://127.0.0.1:5001",
        "method": "POST",
        "endpoint": "/reset-password",
        "payload": {
            "token": "invalid-token",
            "new_password": "123"
        },
        "expected_status": 400,
        "expected_error_key": "error"
    },

    # --- TASK APP defects (5) ---
    {
        "id": "DEF-T01",
        "app": "task",
        "description": "Create task succeeds with empty title",
        "base_url": "http://127.0.0.1:5002",
        "method": "POST",
        "endpoint": "/tasks",
        "payload": {"title": "", "category": "work"},
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-T02",
        "app": "task",
        "description": "Create task accepts invalid category",
        "base_url": "http://127.0.0.1:5002",
        "method": "POST",
        "endpoint": "/tasks",
        "payload": {
            "title": "Test task",
            "category": "invalid_category"
        },
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-T03",
        "app": "task",
        "description": "Create task accepts invalid priority",
        "base_url": "http://127.0.0.1:5002",
        "method": "POST",
        "endpoint": "/tasks",
        "payload": {
            "title": "Test task",
            "priority": "critical"
        },
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-T04",
        "app": "task",
        "description": "Get non-existent task returns 200 instead of 404",
        "base_url": "http://127.0.0.1:5002",
        "method": "GET",
        "endpoint": "/tasks/99999",
        "payload": None,
        "expected_status": 404,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-T05",
        "app": "task",
        "description": "Create task accepts title exceeding 200 characters",
        "base_url": "http://127.0.0.1:5002",
        "method": "POST",
        "endpoint": "/tasks",
        "payload": {"title": "A" * 201},
        "expected_status": 400,
        "expected_error_key": "error"
    },

    # --- BOOKING API defects (5) ---
    {
        "id": "DEF-B01",
        "app": "booking",
        "description": "Create booking accepts checkout before checkin",
        "base_url": "http://127.0.0.1:5003",
        "method": "POST",
        "endpoint": "/bookings",
        "payload": {
            "guest_name": "Test",
            "room_type": "single",
            "check_in": "2026-06-10",
            "check_out": "2026-06-05",
            "guests": 1
        },
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-B02",
        "app": "booking",
        "description": "Create booking accepts more than 10 guests",
        "base_url": "http://127.0.0.1:5003",
        "method": "POST",
        "endpoint": "/bookings",
        "payload": {
            "guest_name": "Test",
            "room_type": "suite",
            "check_in": "2026-06-01",
            "check_out": "2026-06-05",
            "guests": 15
        },
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-B03",
        "app": "booking",
        "description": "Create booking accepts invalid date format",
        "base_url": "http://127.0.0.1:5003",
        "method": "POST",
        "endpoint": "/bookings",
        "payload": {
            "guest_name": "Test",
            "room_type": "single",
            "check_in": "01-06-2026",
            "check_out": "05-06-2026",
            "guests": 1
        },
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-B04",
        "app": "booking",
        "description": "Booking created with missing required fields",
        "base_url": "http://127.0.0.1:5003",
        "method": "POST",
        "endpoint": "/bookings",
        "payload": {"guest_name": "Test"},
        "expected_status": 400,
        "expected_error_key": "error"
    },
    {
        "id": "DEF-B05",
        "app": "booking",
        "description": "Get non-existent booking returns 200 instead of 404",
        "base_url": "http://127.0.0.1:5003",
        "method": "GET",
        "endpoint": "/bookings/99999",
        "payload": None,
        "expected_status": 404,
        "expected_error_key": "error"
    },
]


def run_defect_detection(app_filter: str = None) -> dict:
    """
    Run all defect detection checks against the live apps.
    app_filter: 'auth', 'task', or 'booking' to test one app only.
    Returns detection results per defect.
    """
    defects_to_run = DEFECTS
    if app_filter:
        defects_to_run = [d for d in DEFECTS if d["app"] == app_filter]

    results = []
    caught = 0
    missed = 0

    for defect in defects_to_run:
        try:
            if defect["method"] == "POST":
                response = httpx.post(
                    f"{defect['base_url']}{defect['endpoint']}",
                    json=defect["payload"],
                    timeout=5.0
                )
            else:
                response = httpx.get(
                    f"{defect['base_url']}{defect['endpoint']}",
                    timeout=5.0
                )

            status_matches = response.status_code == defect["expected_status"]
            has_error_key = defect["expected_error_key"] in response.json()
            detected = status_matches and has_error_key

            if detected:
                caught += 1
            else:
                missed += 1

            results.append({
                "defect_id": defect["id"],
                "app": defect["app"],
                "description": defect["description"],
                "detected": detected,
                "expected_status": defect["expected_status"],
                "actual_status": response.status_code,
                "response": response.json()
            })

        except httpx.ConnectError:
            missed += 1
            results.append({
                "defect_id": defect["id"],
                "app": defect["app"],
                "description": defect["description"],
                "detected": False,
                "error": f"Could not connect to {defect['base_url']} — is the app running?"
            })
        except Exception as e:
            missed += 1
            results.append({
                "defect_id": defect["id"],
                "app": defect["app"],
                "description": defect["description"],
                "detected": False,
                "error": str(e)
            })

    total = caught + missed
    detection_rate = round((caught / total) * 100, 2) if total > 0 else 0.0

    return {
        "scorer": "defect_detection",
        "score": detection_rate,
        "total_defects": total,
        "caught": caught,
        "missed": missed,
        "results": results
    }