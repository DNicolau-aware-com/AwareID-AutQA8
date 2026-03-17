"""
Shared fixtures for Gallery (1-N Match) API tests.

Base path: /onboarding/gallery
"""

import copy
import time
import uuid
import allure
import json
import pytest


GALLERY_BASE_PATH = "/onboarding/gallery"


@pytest.fixture
def gallery_base_path():
    """Base path for gallery endpoints."""
    return GALLERY_BASE_PATH


@pytest.fixture
def gallery_face_image(env_store):
    """Get face image from .env file (TEST key)."""
    face_b64 = env_store.get("TEST")
    if not face_b64:
        pytest.skip("TEST not found in .env file - add a valid JPEG face image as TEST=<base64>")
    if face_b64.startswith("data:"):
        face_b64 = face_b64.split(",", 1)[1]
    return face_b64


@pytest.fixture
def unique_gallery_name():
    """Generate a unique gallery name for test isolation."""
    return f"test_gallery_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def registered_user(env_store):
    """
    Return a registered user from .env (GALLERY_REGISTRATION_CODE, GALLERY_USERNAME,
    GALLERY_EMAIL).

    Run test_register_user_all_fields once to populate these keys:
        pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_all_fields -v

    The saved data is reused across all subsequent test runs — no new user is registered.
    """
    reg_code = env_store.get("GALLERY_REGISTRATION_CODE")
    username = env_store.get("GALLERY_USERNAME")
    email = env_store.get("GALLERY_EMAIL")

    if not reg_code:
        pytest.skip(
            "GALLERY_REGISTRATION_CODE not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_register_user.py"
            "::test_register_user_all_fields -v"
        )

    print(f"\n[INFO] Using existing user from .env: {username} ({reg_code})")

    yield {
        "username": username,
        "email": email,
        "registrationCode": reg_code,
    }
    # No cleanup — user persists in the default gallery (no delete API)


@pytest.fixture
def custom_gallery(api_client, gallery_base_path, unique_gallery_name):
    """
    Provide a fresh custom gallery for each test.

    Always creates a new gallery — never reuses a name from .env, which
    may reference a gallery that no longer exists on the server after a reset.
    The gallery is deleted in teardown.
    """
    response = api_client.http_client.post(
        f"{gallery_base_path}/addGallery",
        json={"galleryName": unique_gallery_name},
    )

    if response.status_code != 200:
        pytest.skip(
            f"Could not create test gallery '{unique_gallery_name}' "
            f"({response.status_code}): {response.text[:200]}"
        )

    yield unique_gallery_name

    # Teardown: delete the gallery we created
    api_client.http_client.post(
        f"{gallery_base_path}/deleteGallery",
        json={"galleryName": unique_gallery_name},
    )


@pytest.fixture
def registration_codes(env_store):
    """
    Return the list of registration codes from .env (GALLERY_REGISTRATION_CODES, comma-separated).

    Run test_register_user_all_fields multiple times to accumulate at least 2 codes:
        pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_all_fields -v

    Skips the test if fewer than 2 codes are available (multi-user tests need at least 2).
    """
    raw = env_store.get("GALLERY_REGISTRATION_CODES")
    if not raw:
        pytest.skip(
            "GALLERY_REGISTRATION_CODES not found in .env. "
            "Run test_register_user_all_fields at least twice to populate it."
        )

    codes = [c.strip() for c in raw.split(",") if c.strip()]
    if len(codes) < 2:
        pytest.skip(
            f"GALLERY_REGISTRATION_CODES must contain at least 2 codes for multi-user tests. "
            f"Found: {codes}. Run test_register_user_all_fields again to add more."
        )

    print(f"\n[INFO] Using {len(codes)} registration codes from .env: {codes}")
    return codes


@pytest.fixture
def gallery_names(api_client, gallery_base_path):
    """
    Provide at least 2 gallery names for bulk tests.

    Always creates 2 fresh temporary galleries so that bulk tests work even
    after a server reset (stale GALLERY_NAMES in .env are ignored).
    Both galleries are deleted in teardown.
    """
    created = []
    for _ in range(2):
        name = f"tmpgallery_{uuid.uuid4().hex[:8]}"
        r = api_client.http_client.post(
            f"{gallery_base_path}/addGallery",
            json={"galleryName": name},
        )
        if r.status_code != 200:
            # Clean up galleries already created before failing
            for n in created:
                api_client.http_client.post(
                    f"{gallery_base_path}/deleteGallery",
                    json={"galleryName": n},
                )
            pytest.skip(
                f"Could not create temp gallery '{name}' "
                f"({r.status_code}): {r.text[:200]}"
            )
        created.append(name)

    print(f"\n[INFO] Created {len(created)} temporary galleries: {created}")
    yield created

    for name in created:
        api_client.http_client.post(
            f"{gallery_base_path}/deleteGallery",
            json={"galleryName": name},
        )


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
        print(f"\n{'='*80}")
        print(f"[>>] POST {url}")

        log_payload = None
        if "json" in kwargs:
            log_payload = copy.deepcopy(kwargs["json"])
            # Truncate long base64 image fields for readability
            for field in ("image",):
                if field in log_payload and isinstance(log_payload[field], str) and len(log_payload[field]) > 100:
                    log_payload[field] = f"{log_payload[field][:50]}... (truncated, length: {len(log_payload[field])})"

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

        print(f"{'='*80}\n")
        return response

    def logged_get(url, **kwargs):
        print(f"\n{'='*80}")
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

        print(f"{'='*80}\n")
        return response

    api_client.http_client.post = logged_post
    api_client.http_client.get = logged_get

    yield

    api_client.http_client.post = original_post
    api_client.http_client.get = original_get

    # Attach consolidated transaction summary to Allure
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
