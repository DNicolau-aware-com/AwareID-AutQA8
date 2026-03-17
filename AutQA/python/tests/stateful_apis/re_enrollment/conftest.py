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


@pytest.fixture(autouse=True)
def setup_re_enrollment_config(apply_server_config):
    """Apply re_enrollment_face config before every re-enrollment test and restore after."""
    apply_server_config("re_enrollment_face")


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

def _create_re_enrollment_token(api_client, env_store, label: str, verify_face_first: bool = False, enable_add_device: bool = False) -> str:
    """
    Self-contained helper: enroll a fresh user, add their face (saving them to the
    subject manager), then call /enroll again with the same username to obtain a
    reEnrollmentToken.  Skips the test on any failure.

    Does NOT depend on a pre-existing .env username.  The fresh user is created
    with a unique name so parallel test runs don't collide.
    """
    import uuid

    face_image = env_store.get("FACE") or env_store.get("TEST")
    if not face_image:
        pytest.skip("FACE not found in .env — required to create a fresh enrolled user")
    if face_image.startswith("data:"):
        face_image = face_image.split(",", 1)[1]

    workflow = env_store.get("WORKFLOW") or "charlie4"
    username = f"retest_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"

    # Step 1: initial enrollment
    enroll_resp = api_client.http_client.post(
        f"{_ENROLLMENT_BASE_PATH}/enroll",
        json={"username": username, "email": email, "firstName": "Test", "lastName": "User"},
    )
    if enroll_resp.status_code != 200:
        pytest.skip(f"[{label}] Could not enroll fresh user '{username}': {enroll_resp.status_code}")

    enrollment_token = enroll_resp.json().get("enrollmentToken")
    if not enrollment_token:
        pytest.skip(f"[{label}] No enrollmentToken in /enroll response")

    # Step 2: add face — saves user to subject manager and returns registrationCode
    now_ms = int(time.time() * 1000)
    frames = [{"data": face_image, "tags": [], "timestamp": now_ms + i * 30} for i in range(3)]
    face_resp = api_client.http_client.post(
        f"{_ENROLLMENT_BASE_PATH}/addFace",
        json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": username},
                    "workflow_data": {"workflow": workflow, "frames": frames},
                }
            },
        },
    )
    if face_resp.status_code != 200:
        pytest.skip(f"[{label}] addFace failed for '{username}': {face_resp.status_code}")

    registration_code = face_resp.json().get("registrationCode")
    if not registration_code:
        pytest.skip(
            f"[{label}] No registrationCode returned for '{username}' — "
            "user not saved to subject manager. Check saveToSubjectManager config."
        )

    print(f"\n[INFO] Fresh enrolled user '{username}' — registrationCode: {registration_code[:20]}...")

    # Step 3: call /enroll again — server should now return reEnrollmentToken
    re_resp = api_client.http_client.post(
        f"{_ENROLLMENT_BASE_PATH}/enroll",
        json={"username": username, "email": email, "firstName": "Test", "lastName": "User"},
    )
    if re_resp.status_code != 200:
        pytest.skip(f"[{label}] Second /enroll call failed for '{username}': {re_resp.status_code}")

    data = re_resp.json()
    token = data.get("reEnrollmentToken")
    if not token:
        pytest.skip(
            f"[{label}] reEnrollmentToken not returned for '{username}'. "
            f"Response keys: {list(data.keys())}"
        )

    print(f"\n[INFO] reEnrollmentToken for {label} '{username}': {token[:20]}...")

    # Optional step 4: enable addDevice in the server config (one-change-per-POST rule).
    # Required for completeReEnroll tests that register a device — without this the
    # server throws a Hibernate NPE ("null id in ModelRegisteredDevice").
    if enable_add_device:
        r = api_client.http_client.get("/onboarding/admin/customerConfig")
        c = copy.deepcopy(r.json().get("onboardingConfig", {}))
        c.setdefault("onboardingOptions", {}).setdefault("enrollment", {})["addDevice"] = True
        r2 = api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": c})
        if r2.status_code != 200:
            pytest.skip(f"[{label}] Could not enable addDevice config: {r2.status_code} — {r2.text[:200]}")
        time.sleep(1)
        print(f"[INFO] addDevice enabled in config for {label}")

    # Optional step 5: call verifyFace to advance the token to the state required
    # by completeReEnroll.  The server requires verifyFace to succeed before
    # completeReEnroll will accept the token ("token not for re-enrollment" otherwise).
    if verify_face_first:
        now_ms2 = int(time.time() * 1000)
        vf_frames = [{"data": face_image, "tags": [], "timestamp": now_ms2 + i * 30} for i in range(3)]
        vf_resp = api_client.http_client.post(
            f"{RE_ENROLLMENT_BASE_PATH}/verifyFace",
            json={
                "reEnrollmentToken": token,
                "faceLivenessData": {
                    "video": {
                        "meta_data": {"username": username},
                        "workflow_data": {"workflow": workflow, "frames": vf_frames},
                    }
                },
            },
        )
        if vf_resp.status_code != 200:
            pytest.skip(
                f"[{label}] verifyFace failed (needed before completeReEnroll): "
                f"{vf_resp.status_code} — {vf_resp.text[:300]}"
            )
        print(f"[INFO] verifyFace passed — token ready for completeReEnroll")

    return token


@pytest.fixture
def re_enrollment_token(api_client, env_store):
    """
    Obtain a reEnrollmentToken for verifyFace tests.

    Creates a fresh enrolled user inline (enroll + addFace → registrationCode),
    then calls /enroll again to get the reEnrollmentToken.  Self-contained —
    does not depend on any pre-existing .env username.
    """
    yield _create_re_enrollment_token(api_client, env_store, "verifyFace", verify_face_first=False)


@pytest.fixture
def complete_re_enrollment_token(api_client, env_store):
    """
    Obtain a reEnrollmentToken for completeReEnroll tests.

    Creates a fresh enrolled user inline (enroll + addFace → registrationCode),
    calls /enroll again to get the reEnrollmentToken, then calls verifyFace to
    advance the token to the state required by completeReEnroll.  Self-contained.
    """
    yield _create_re_enrollment_token(api_client, env_store, "completeReEnroll", verify_face_first=True, enable_add_device=True)


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
