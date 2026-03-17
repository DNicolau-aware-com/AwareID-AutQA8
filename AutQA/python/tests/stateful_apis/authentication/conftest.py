"""
Shared fixtures for Authentication API tests.

Base path: /onboarding/authentication

The enrolled_username fixture creates a fresh fully-enrolled user inline
(enroll + addFace → registrationCode) so that authentication tests always
have a user with biometric data in the subject manager.

It depends explicitly on setup_authentication_config to guarantee face flags
are enabled (via apply_server_config) before calling addFace.

Required .env keys:
    FACE      — base64-encoded live face JPEG
    WORKFLOW  — liveness workflow name (default: charlie4)
"""

import time
import uuid

import pytest


_ENROLLMENT_BASE_PATH = "/onboarding/enrollment"


# ==============================================================================
# CONFIG FIXTURE (autouse)
# ==============================================================================

@pytest.fixture(autouse=True)
def setup_authentication_config(apply_server_config):
    """Apply authentication_face config before every authentication test and restore after."""
    apply_server_config("authentication_face")


# ==============================================================================
# ENROLLED USER FIXTURE
# ==============================================================================

@pytest.fixture
def enrolled_username(api_client, env_store, setup_authentication_config):
    """
    Create a fresh fully-enrolled user (enroll + addFace → registrationCode)
    for authentication tests.

    Authentication requires a user whose biometric data is stored in the subject
    manager (the server looks up the registrationCode on authenticate).  A static
    .env username may not have biometric data, so this fixture creates a fresh
    user inline instead.

    Depends on setup_authentication_config so face flags are guaranteed to be
    enabled before addFace is called.

    Returns the username string.
    """
    face_image = env_store.get("FACE") or env_store.get("TEST")
    if not face_image:
        pytest.skip("FACE not found in .env — required for authentication tests")
    if face_image.startswith("data:"):
        face_image = face_image.split(",", 1)[1]

    workflow = env_store.get("WORKFLOW") or "charlie4"
    username = f"authtest_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"

    # Step 1: initial enrollment
    enroll_resp = api_client.http_client.post(
        f"{_ENROLLMENT_BASE_PATH}/enroll",
        json={"username": username, "email": email, "firstName": "Test", "lastName": "User"},
    )
    if enroll_resp.status_code != 200:
        pytest.skip(
            f"[enrolled_username] Could not enroll fresh user '{username}': "
            f"{enroll_resp.status_code} — {enroll_resp.text[:200]}"
        )

    enrollment_token = enroll_resp.json().get("enrollmentToken")
    if not enrollment_token:
        pytest.skip("[enrolled_username] No enrollmentToken in /enroll response")

    # Step 2: addFace — saves user to subject manager and returns registrationCode
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
        pytest.skip(
            f"[enrolled_username] addFace failed for '{username}': "
            f"{face_resp.status_code} — {face_resp.text[:200]}"
        )

    registration_code = face_resp.json().get("registrationCode")
    if not registration_code:
        pytest.skip(
            f"[enrolled_username] No registrationCode for '{username}' — "
            "check saveToSubjectManager in server config."
        )

    print(f"\n[AUTH SETUP] Fresh enrolled user '{username}' — registrationCode: {registration_code[:20]}...")
    return username
