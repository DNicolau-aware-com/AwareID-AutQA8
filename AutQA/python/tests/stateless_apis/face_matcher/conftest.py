"""
Shared fixtures for Face Matcher (Nexaface) tests.
"""

import copy
import time
import pytest
import json
import allure


SUPPORTED_ALGORITHMS = ["F200", "F500"]


@pytest.fixture
def face_matcher_base_path():
    """Base path for nexaface endpoints."""
    return "/nexaface"


@pytest.fixture
def face_image_base64(env_store):
    """Get face image from .env file (TEST)."""
    face_b64 = env_store.get("TEST")
    if not face_b64:
        pytest.skip("TEST not found in .env file")
    # Strip data URI prefix if present (e.g. "data:image/jpeg;base64,...")
    if face_b64.startswith("data:"):
        face_b64 = face_b64.split(",", 1)[1]
    return face_b64


@pytest.fixture
def probe_face_image(face_image_base64):
    """Get probe face image - uses TEST."""
    return face_image_base64


@pytest.fixture
def gallery_face_image(face_image_base64):
    """Get gallery face image - uses TEST."""
    return face_image_base64


@pytest.fixture(autouse=True)
def log_api_responses(api_client):
    """
    Automatically log all API requests and responses.

    This fixture runs for every test in this directory (autouse=True).
    """
    original_post = api_client.http_client.post
    original_get = api_client.http_client.get

    def logged_post(url, **kwargs):
        print(f"\n{'='*80}")
        print(f"[>>] POST {url}")

        log_payload = None
        if 'json' in kwargs:
            log_payload = copy.deepcopy(kwargs['json'])
            # Truncate long base64 strings for readability
            for field in ('probe', 'gallery', 'encounter'):
                if field in log_payload and 'VISIBLE_FRONTAL' in log_payload.get(field, {}):
                    img = log_payload[field]['VISIBLE_FRONTAL']
                    log_payload[field]['VISIBLE_FRONTAL'] = f"{img[:50]}... (truncated, length: {len(img)})"

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
        try:
            response_data = response.json()
            # Truncate long template exports for console only
            log_response = copy.deepcopy(response_data)
            if 'export' in log_response and len(log_response.get('export', '')) > 100:
                log_response['export'] = (
                    f"{log_response['export'][:50]}... "
                    f"(truncated, length: {len(log_response['export'])})"
                )
            print("[RS] Response Body:")
            print(json.dumps(log_response, indent=2))
            allure.attach(
                json.dumps(response_data, indent=2),
                name=f"Response {response.status_code} [{elapsed:.3f}s]",
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception:
            print(f"[RS] Response Text: {response.text[:500]}")
            allure.attach(
                response.text,
                name=f"Response {response.status_code} [{elapsed:.3f}s] (text)",
                attachment_type=allure.attachment_type.TEXT,
            )

        print(f"{'='*80}\n")
        return response

    def logged_get(url, **kwargs):
        print(f"\n{'='*80}")
        print(f"[>>] GET {url}")

        start = time.time()
        response = original_get(url, **kwargs)
        elapsed = time.time() - start

        print(f"[RS] Response Status: {response.status_code}  [{elapsed:.3f}s]")
        print(f"[RS] Response: {response.text}")
        allure.attach(
            response.text,
            name=f"Response GET {url} {response.status_code} [{elapsed:.3f}s]",
            attachment_type=allure.attachment_type.TEXT,
        )
        print(f"{'='*80}\n")

        return response

    api_client.http_client.post = logged_post
    api_client.http_client.get = logged_get

    yield  # Test runs here

    # Restore original methods after test
    api_client.http_client.post = original_post
    api_client.http_client.get = original_get
