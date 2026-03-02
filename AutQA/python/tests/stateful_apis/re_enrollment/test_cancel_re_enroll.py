"""
Tests for POST /onboarding/reEnrollment/cancel

Cancels an in-progress re-enrollment session, invalidating the reEnrollmentToken.

Prerequisites (set once in .env before running):
    RE_ENROLLMENT_USERNAME  — username of an already-enrolled user

The re_enrollment_token fixture obtains a fresh reEnrollmentToken inline
by calling /onboarding/enrollment/enroll — no token is persisted to .env.
"""

import uuid

import allure
import pytest


def _assert_error_structure(result: dict) -> None:
    """Assert that a 400/500 response contains all required error fields."""
    for field in ("errorCode", "errorMsg", "status", "timestamp"):
        assert field in result, f"Expected '{field}' in error response, got: {result}"


# ==============================================================================
# POSITIVE TESTS
# ==============================================================================

@allure.feature("Re-Enrollment API")
@allure.story("Cancel Re-Enrollment")
@allure.title("cancel with valid token returns 200")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Sends a valid reEnrollmentToken obtained from /enrollment/enroll for an "
    "already-enrolled user. Expects HTTP 200 — the re-enrollment session is cancelled."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_cancel_re_enroll(
    api_client,
    re_enrollment_base_path,
    re_enrollment_token,
):
    """Valid reEnrollmentToken → 200 (session cancelled)."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/cancel",
        json={"reEnrollmentToken": re_enrollment_token},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    print(f"\n[OK] cancel → 200")


# ==============================================================================
# NEGATIVE TESTS
# ==============================================================================

@allure.feature("Re-Enrollment API")
@allure.story("Cancel Re-Enrollment - Negative")
@allure.title("cancel with invalid token returns 400 or 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a random UUID as reEnrollmentToken. "
    "Expects HTTP 400 or 500 with errorCode, errorMsg, status, and timestamp."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_cancel_re_enroll_invalid_token(
    api_client,
    re_enrollment_base_path,
):
    """Invalid reEnrollmentToken → 400/500 with error structure."""
    fake_token = str(uuid.uuid4())

    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/cancel",
        json={"reEnrollmentToken": fake_token},
    )

    assert response.status_code in (400, 500), (
        f"Expected 400 or 500 for invalid token, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    _assert_error_structure(result)

    print(f"\n[OK] Invalid token rejected: {response.status_code}")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")


@allure.feature("Re-Enrollment API")
@allure.story("Cancel Re-Enrollment - Negative")
@allure.title("cancel with missing token returns 400 or 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends an empty JSON body without the reEnrollmentToken field. "
    "Expects HTTP 400 or 500 with a structured error response."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_cancel_re_enroll_missing_token(
    api_client,
    re_enrollment_base_path,
):
    """Missing reEnrollmentToken field → 400/500 with error structure."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/cancel",
        json={},
    )

    assert response.status_code in (400, 500), (
        f"Expected 400 or 500 for missing token, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    _assert_error_structure(result)

    print(f"\n[OK] Missing token rejected: {response.status_code}")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")
