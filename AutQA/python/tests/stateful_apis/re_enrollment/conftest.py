"""
Shared fixtures for Re-Enrollment API tests.

Base path: /onboarding/reEnrollment

Prerequisites (.env keys):
    RE_ENROLLMENT_USERNAME  — username of an already-enrolled user (verifyFace tests)
    GET_PUBLIC_KEY_USERNAME — username of an already-enrolled user (completeReEnroll tests)
    FACE                    — base64-encoded live face JPEG
    SPOOF                   — base64-encoded spoof image (optional)
    WORKFLOW                — liveness workflow name (default: charlie4)
"""

import copy
import time
import allure
import json
import pytest


RE_ENROLLMENT_BASE_PATH = "/onboarding/reEnrollment"
_ENROLLMENT_BASE_PATH = "/onboarding/enrollment"


# ==============================================================================
# PATH & IMAGE FIXTURES
# ==============================================================================

@pytest.fixture
def re_enrollment_base_path():
    """Base path for re-enrollment endpoints."""
    return RE_ENROLLMENT_BASE_PATH


@pytest.fixture
def re_enrollment_face_image(env_store):
    """
    Live face image from .env (FACE key, TEST as fallback).
    Skips the test if absent.
    """
    val = env_store.get("FACE") or env_store.get("TEST")
    if not val:
        pytest.skip(
            "FACE not found in .env — add a valid JPEG face image as FACE=<base64>"
        )
    return val.split(",", 1)[1] if val.startswith("data:") else val


@pytest.fixture
def re_enrollment_spoof_image(env_store):
    """
    Spoof image from .env (SPOOF key).
    Skips the test if absent.
    """
    val = env_store.get("SPOOF")
    if not val:
        pytest.skip("SPOOF not found in .env — add a spoof image as SPOOF=<base64>")
    return val.split(",", 1)[1] if val.startswith("data:") else val


@pytest.fixture
def re_enrollment_workflow(env_store):
    """
    Liveness workflow name from .env (WORKFLOW key).
    Defaults to 'charlie4' if not set.
    """
    return env_store.get("WORKFLOW") or "charlie4"


# ==============================================================================
# TOKEN FIXTURE
# ==============================================================================

@pytest.fixture
def re_enrollment_token(api_client, env_store):
    """
    Obtain a fresh reEnrollmentToken by calling /onboarding/enrollment/enroll
    with an already-enrolled username.

    Reads RE_ENROLLMENT_USERNAME from .env (falls back to userEnroll).
    Email is read from RE_ENROLLMENT_EMAIL, then EMAIL, then defaults to
    <username>@example.com. firstName/lastName default to 'Test'/'User'.

    Skips if the username is absent or if the server does not return
    a reEnrollmentToken (i.e., the user is not enrolled yet).

    Required .env keys:
        RE_ENROLLMENT_USERNAME  — already-enrolled username
        RE_ENROLLMENT_EMAIL     — (optional) email used during original enrollment
    """
    username_key = (
        "RE_ENROLLMENT_USERNAME"
        if env_store.get("RE_ENROLLMENT_USERNAME")
        else "userEnroll"
    )
    yield _fetch_re_enrollment_token(api_client, env_store, username_key, "verifyFace")


def _fetch_re_enrollment_token(api_client, env_store, username_key: str, label: str) -> str:
    """
    Internal helper — call /onboarding/enrollment/enroll for an already-enrolled
    user and return the reEnrollmentToken. Calls pytest.skip on any failure.
    """
    username = env_store.get(username_key)
    if not username:
        pytest.skip(
            f"{username_key} not found in .env. "
            f"Set it to an already-enrolled username:\n"
            f"  {username_key}=<your_enrolled_username>"
        )

    email = (
        env_store.get("RE_ENROLLMENT_EMAIL")
        or env_store.get("EMAIL")
        or f"{username}@example.com"
    )

    response = api_client.http_client.post(
        f"{_ENROLLMENT_BASE_PATH}/enroll",
        json={
            "username": username,
            "email": email,
            "firstName": env_store.get("FIRSTNAME") or "Test",
            "lastName": env_store.get("LASTNAME") or "User",
        },
    )
    if response.status_code != 200:
        pytest.skip(
            f"Could not obtain reEnrollmentToken for {label} '{username}' "
            f"({response.status_code}): {response.text[:300]}"
        )

    data = response.json()
    token = data.get("reEnrollmentToken")
    if not token:
        pytest.skip(
            f"reEnrollmentToken not returned for {label} '{username}'. "
            f"Ensure the user is already enrolled. "
            f"Response keys: {list(data.keys())}"
        )

    print(f"\n[INFO] reEnrollmentToken for {label} '{username}': {token[:20]}...")
    return token


@pytest.fixture
def complete_re_enrollment_token(api_client, env_store):
    """
    Obtain a fresh reEnrollmentToken for completeReEnroll tests.

    Reads RE_ENROLLMENT_USERNAME from .env — set it to any already-enrolled user
    (e.g. dantest_20260302_124405_3bfc82). Calls /enrollment/enroll with that
    username to get a fresh reEnrollmentToken, then yields it for the test.

    Required .env keys:
        RE_ENROLLMENT_USERNAME  — already-enrolled username
    """
    yield _fetch_re_enrollment_token(api_client, env_store, "RE_ENROLLMENT_USERNAME", "completeReEnroll")


@pytest.fixture
def re_enrollment_public_key(env_store):
    """
    ECDSA public key for completeReEnroll device tests.

    Reads GET_PUBLIC_KEY_USERNAME from .env and interprets its value as a
    PEM-encoded public key (strips '-----BEGIN/END PUBLIC KEY-----' headers
    and returns the raw base64 DER content the API expects).

    Dotenv limitation: multi-line PEM keys stored in .env are only partially
    read (first line only). Store the key as a single-line base64 value instead:

        GET_PUBLIC_KEY_USERNAME=MFYwEAYH...  (raw base64, no PEM headers)

    Falls back to a freshly generated ECDSA secp256k1 key if the env value
    is absent or is only a PEM header line (not a usable key).
    """
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    import base64

    raw = env_store.get("GET_PUBLIC_KEY_USERNAME") or ""

    # Strip PEM headers if present and join all lines into a single base64 string
    cleaned = (
        raw
        .replace("-----BEGIN PUBLIC KEY-----", "")
        .replace("-----END PUBLIC KEY-----", "")
        .replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
        .strip()
    )

    # If what remains is a valid non-trivial base64 string, use it
    if len(cleaned) > 50:
        print(f"\n[INFO] Using public key from .env (GET_PUBLIC_KEY_USERNAME)")
        return cleaned

    # Dotenv could only read the PEM header line — generate a fresh key instead
    print(
        "\n[INFO] GET_PUBLIC_KEY_USERNAME is absent or only a PEM header "
        "(multi-line .env values are not supported). Generating a fresh ECDSA key."
    )
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key_der = private_key.public_key().public_bytes(
        encoding=Encoding.DER,
        format=PublicFormat.SubjectPublicKeyInfo,
    )
    return base64.b64encode(public_key_der).decode("utf-8")


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
