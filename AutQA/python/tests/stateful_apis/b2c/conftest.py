"""
Shared fixtures for B2C API tests.

Base path: /onboarding/b2c

The b2c_enrolled_user fixture resolves to an already-enrolled user from .env
(B2C_USERNAME or RE_ENROLLMENT_USERNAME) and pairs it with the fixed email
dnicolau.aware@gmail.com used in triggerEnroll payloads.

Required .env keys:
    B2C_USERNAME          — already-enrolled username (falls back to RE_ENROLLMENT_USERNAME)

Optional .env keys:
    B2C_PHONE             — phone number for phone-notify tests
"""

import copy
import json
import time

import allure
import pytest


B2C_BASE_PATH = "/onboarding/b2c"
B2C_EMAIL = "dnicolau.aware@gmail.com"


# ==============================================================================
# PATH FIXTURE
# ==============================================================================

@pytest.fixture
def b2c_base_path():
    """Base path for B2C endpoints."""
    return B2C_BASE_PATH


# ==============================================================================
# ENROLLED USER FIXTURE
# ==============================================================================

@pytest.fixture
def b2c_enrolled_user(env_store):
    """
    Resolve an already-enrolled username from .env for B2C positive tests.

    Reads B2C_USERNAME first, then falls back to RE_ENROLLMENT_USERNAME.
    Skips if neither is set — triggerEnroll requires an enrolled user.

    Returns a dict:
        {
            "username": "<enrolled_username>",
            "email":    "dnicolau.aware@gmail.com",
        }
    """
    username = env_store.get("B2C_USERNAME")
    if not username:
        pytest.skip(
            "B2C_USERNAME not set in .env. "
            "Set it to a user registered via the Keycloak B2C pre-registration flow "
            "(not just enrolled via the enrollment API). "
            "Example: B2C_USERNAME=<keycloak_preregistered_username>"
        )

    print(f"\n[B2C SETUP] Using B2C pre-registered user '{username}' with email {B2C_EMAIL}")
    return {
        "username": username,
        "email": B2C_EMAIL,
    }


# ==============================================================================
# SESSION TOKEN FIXTURE
# ==============================================================================

@pytest.fixture
def b2c_session_token(api_client, b2c_base_path, b2c_enrolled_user):
    """
    Obtain a fresh B2C sessionToken by calling POST /b2c/triggerAuthenticate.

    Used as a path parameter for GET /b2c/operationStatus/{sessionToken}.
    Skips if triggerAuthenticate does not return status='SUCCESS'.
    """
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerAuthenticate",
        json={"username": b2c_enrolled_user["username"]},
    )
    if response.status_code != 200:
        pytest.skip(
            f"triggerAuthenticate failed ({response.status_code}): {response.text[:200]}"
        )

    data = response.json()
    if data.get("status") != "SUCCESS":
        pytest.skip(
            f"triggerAuthenticate returned FAILURE. errorSummary: {data.get('errorSummary')}"
        )

    token = data.get("sessionToken")
    if not token:
        pytest.skip("No sessionToken in triggerAuthenticate response")

    print(f"\n[B2C SETUP] sessionToken obtained: {token[:20]}...")
    return token


@pytest.fixture
def b2c_phone(env_store):
    """
    Phone number for B2C notify tests.

    Reads B2C_PHONE from .env; skips the test if absent.
    """
    val = env_store.get("B2C_PHONE")
    if not val:
        pytest.skip("B2C_PHONE not set in .env — add a phone number as B2C_PHONE=+1XXXXXXXXXX")
    return val


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
    - Collects every transaction into request.node._api_transactions so the
      pytest_runtest_makereport hookwrapper can write the artifact JSON file.
    - Attaches a consolidated transaction summary to Allure after the test.
    """
    if not hasattr(request.node, "_api_transactions"):
        request.node._api_transactions = []

    original_post = api_client.http_client.post
    original_get = api_client.http_client.get

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
            display = raw if raw else "(empty response body — server returned no content)"
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
        display = raw if raw else "(empty response body — server returned no content)"
        print(f"[RS] Response Status: {response.status_code}  [{elapsed:.3f}s]")
        print(f"[RS] Response: {display[:1000]}")

        response_body = None
        try:
            response_body = response.json()
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

    api_client.http_client.post = logged_post
    api_client.http_client.get = logged_get

    yield

    api_client.http_client.post = original_post
    api_client.http_client.get = original_get

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
