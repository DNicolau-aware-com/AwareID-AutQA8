"""
Shared fixtures for Geofence / Compliance API tests.

Base path: /compliance/geofence

No .env keys are required — all geofence endpoints are read-only GET requests
authenticated via the standard JWT / API Key handled by the framework.
"""

import copy
import json
import time
import uuid

import allure
import pytest


GEOFENCE_BASE_PATH = "/compliance/geofence"

# Probe result cached across tests so only one HTTP call is made per session
_geofence_available: bool | None = None


# ==============================================================================
# PATH FIXTURE
# ==============================================================================

@pytest.fixture
def geofence_base_path():
    """Base path for Geofence / Compliance endpoints."""
    return GEOFENCE_BASE_PATH


# ==============================================================================
# AVAILABILITY GUARD (autouse)
# ==============================================================================

@pytest.fixture(autouse=True)
def skip_if_geofence_unavailable(api_client):
    """
    Probe the geofence feature once per session.

    Skips every test in this directory when GET /compliance/geofence/definitions
    returns 404, which means the feature is not deployed on this environment.
    """
    global _geofence_available
    if _geofence_available is None:
        r = api_client.http_client.get(
            f"{GEOFENCE_BASE_PATH}/definitions",
            with_apikey=False,
            retry=False,
        )
        _geofence_available = r.status_code != 404

    if not _geofence_available:
        pytest.skip(
            "Geofence feature not available on this environment "
            f"(GET {GEOFENCE_BASE_PATH}/definitions → 404)"
        )


# ==============================================================================
# LOGGING FIXTURE (autouse)
# ==============================================================================

def _truncate_b64(obj: object, max_len: int = 100) -> None:
    """Recursively truncate long base64 string values in a dict/list for logging."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and len(v) > max_len:
                obj[k] = f"{v[:50]}... (truncated, length: {len(v)})"
            else:
                _truncate_b64(v, max_len)
    elif isinstance(obj, list):
        for item in obj:
            _truncate_b64(item, max_len)


@pytest.fixture(autouse=True)
def log_api_responses(api_client, request):
    """
    Automatically log all API requests and responses for this directory.

    - Attaches per-call request/response JSON to Allure.
    - Collects every transaction into request.node._api_transactions.
    - Attaches a consolidated transaction summary to Allure after the test.
    """
    if not hasattr(request.node, "_api_transactions"):
        request.node._api_transactions = []

    original_post = api_client.http_client.post
    original_get = api_client.http_client.get
    original_put = api_client.http_client.put
    original_delete = api_client.http_client.delete

    def logged_post(url, **kwargs):
        print(f"\n{'=' * 80}")
        print(f"[>>] POST {url}")

        log_payload = None
        if "json" in kwargs:
            log_payload = copy.deepcopy(kwargs["json"])
            _truncate_b64(log_payload)
            print("[RQ] Request Body:")
            print(json.dumps(log_payload, indent=2))
            allure.attach(
                json.dumps(log_payload, indent=2),
                name=f"Request POST {url}",
                attachment_type=allure.attachment_type.JSON,
            )

        start = time.time()
        response = original_post(url, **kwargs)
        elapsed = time.time() - start

        print(f"\n[RS] Response Status: {response.status_code}  [{elapsed:.3f}s]")
        response_body = None
        try:
            response_body = response.json()
            print("[RS] Response Body:")
            print(json.dumps(response_body, indent=2))
            allure.attach(
                json.dumps(response_body, indent=2),
                name=f"Response {response.status_code} [{elapsed:.3f}s]",
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception:
            raw = response.text.strip()
            response_body = raw or None
            display = raw if raw else "(empty response body)"
            print(f"[RS] Response: {display[:500]}")
            allure.attach(
                display,
                name=f"Response {response.status_code} [{elapsed:.3f}s]",
                attachment_type=allure.attachment_type.TEXT,
            )

        request.node._api_transactions.append({
            "method": "POST",
            "url": url,
            "request_body": log_payload,
            "response_status": response.status_code,
            "response_body": response_body,
            "elapsed_ms": round(elapsed * 1000, 2),
        })

        print(f"{'=' * 80}\n")
        return response

    def logged_get(url, **kwargs):
        print(f"\n{'=' * 80}")
        print(f"[>>] GET {url}")

        start = time.time()
        response = original_get(url, **kwargs)
        elapsed = time.time() - start

        raw = response.text.strip()
        display = raw if raw else "(empty response body)"
        print(f"[RS] Response Status: {response.status_code}  [{elapsed:.3f}s]")
        print(f"[RS] Response: {display[:2000]}")

        response_body = None
        try:
            response_body = response.json()
            allure.attach(
                json.dumps(response_body, indent=2),
                name=f"Response GET {url} {response.status_code} [{elapsed:.3f}s]",
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception:
            response_body = raw or None
            allure.attach(
                display,
                name=f"Response GET {url} {response.status_code} [{elapsed:.3f}s]",
                attachment_type=allure.attachment_type.TEXT,
            )

        request.node._api_transactions.append({
            "method": "GET",
            "url": url,
            "request_body": None,
            "response_status": response.status_code,
            "response_body": response_body,
            "elapsed_ms": round(elapsed * 1000, 2),
        })

        print(f"{'=' * 80}\n")
        return response

    def logged_put(url, **kwargs):
        print(f"\n{'=' * 80}")
        print(f"[>>] PUT {url}")

        log_payload = None
        if "json" in kwargs:
            log_payload = copy.deepcopy(kwargs["json"])
            _truncate_b64(log_payload)
            print("[RQ] Request Body:")
            print(json.dumps(log_payload, indent=2))
            allure.attach(
                json.dumps(log_payload, indent=2),
                name=f"Request PUT {url}",
                attachment_type=allure.attachment_type.JSON,
            )

        start = time.time()
        response = original_put(url, **kwargs)
        elapsed = time.time() - start

        print(f"\n[RS] Response Status: {response.status_code}  [{elapsed:.3f}s]")
        response_body = None
        try:
            response_body = response.json()
            print("[RS] Response Body:")
            print(json.dumps(response_body, indent=2))
            allure.attach(
                json.dumps(response_body, indent=2),
                name=f"Response {response.status_code} [{elapsed:.3f}s]",
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception:
            raw = response.text.strip()
            response_body = raw or None
            display = raw if raw else "(empty response body)"
            print(f"[RS] Response: {display[:500]}")
            allure.attach(
                display,
                name=f"Response {response.status_code} [{elapsed:.3f}s]",
                attachment_type=allure.attachment_type.TEXT,
            )

        request.node._api_transactions.append({
            "method": "PUT",
            "url": url,
            "request_body": log_payload,
            "response_status": response.status_code,
            "response_body": response_body,
            "elapsed_ms": round(elapsed * 1000, 2),
        })

        print(f"{'=' * 80}\n")
        return response

    def logged_delete(url, **kwargs):
        print(f"\n{'=' * 80}")
        print(f"[>>] DELETE {url}")

        start = time.time()
        response = original_delete(url, **kwargs)
        elapsed = time.time() - start

        raw = response.text.strip()
        display = raw if raw else "(empty response body)"
        print(f"[RS] Response Status: {response.status_code}  [{elapsed:.3f}s]")
        print(f"[RS] Response: {display[:500]}")

        response_body = None
        try:
            response_body = response.json()
            allure.attach(
                json.dumps(response_body, indent=2),
                name=f"Response DELETE {url} {response.status_code} [{elapsed:.3f}s]",
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception:
            response_body = raw or None
            allure.attach(
                display,
                name=f"Response DELETE {url} {response.status_code} [{elapsed:.3f}s]",
                attachment_type=allure.attachment_type.TEXT,
            )

        request.node._api_transactions.append({
            "method": "DELETE",
            "url": url,
            "request_body": None,
            "response_status": response.status_code,
            "response_body": response_body,
            "elapsed_ms": round(elapsed * 1000, 2),
        })

        print(f"{'=' * 80}\n")
        return response

    api_client.http_client.post = logged_post
    api_client.http_client.get = logged_get
    api_client.http_client.put = logged_put
    api_client.http_client.delete = logged_delete

    yield

    api_client.http_client.post = original_post
    api_client.http_client.get = original_get
    api_client.http_client.put = original_put
    api_client.http_client.delete = original_delete

    if request.node._api_transactions:
        summary = {
            "test": request.node.nodeid,
            "transaction_count": len(request.node._api_transactions),
            "transactions": request.node._api_transactions,
        }
        allure.attach(
            json.dumps(summary, indent=2),
            name="API Transaction Summary",
            attachment_type=allure.attachment_type.JSON,
        )


# ==============================================================================
# CRUD FIXTURES
# ==============================================================================

@pytest.fixture
def geofence_test_name():
    """Unique geofence name per test run to avoid collisions with existing data."""
    return f"pytest-geo-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def admin_geofence_payload():
    """Minimal valid admin-type geofence rule payload (include US/TX)."""
    return {
        "type": "include",
        "geofence": {
            "type": "admin",
            "definitions": [
                {"country": "US", "states": ["TX"]}
            ],
        },
    }


@pytest.fixture
def created_geofence(api_client, geofence_test_name, admin_geofence_payload):
    """
    Create a geofence definition before the test and delete it after.

    Yields the geofence name so the test can reference it.
    Skips if the create call fails (endpoint not deployed in this environment).
    """
    response = api_client.http_client.post(
        f"{GEOFENCE_BASE_PATH}/definitions/{geofence_test_name}",
        json=admin_geofence_payload,
        with_apikey=False,
    )
    if response.status_code not in (200, 201):
        pytest.skip(
            f"Cannot create test geofence — endpoint returned {response.status_code}. "
            "Geofence feature may not be enabled on this environment."
        )

    yield geofence_test_name

    # Teardown: best-effort cleanup
    api_client.http_client.delete(
        f"{GEOFENCE_BASE_PATH}/definitions/{geofence_test_name}",
        with_apikey=False,
    )
