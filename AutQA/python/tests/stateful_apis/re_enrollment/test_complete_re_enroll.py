"""
Tests for POST /onboarding/reEnrollment/completeReEnroll

Completes the re-enrollment process. Optionally adds or replaces a device
by providing a deviceId, ECDSA publicKey, and addOrUpdate flag.

Prerequisites (set once in .env before running):
    RE_ENROLLMENT_USERNAME  — username of an already-enrolled user

Optional .env key for providing a pre-existing ECDSA public key:
    GET_PUBLIC_KEY_USERNAME — raw base64-encoded ECDSA public key (single line,
                              no PEM headers). If absent or unparsable, tests
                              generate a fresh key dynamically.

    Note: multi-line PEM keys in .env are NOT supported by dotenv.
    Store the raw base64 value on a single line instead:
        GET_PUBLIC_KEY_USERNAME=MFYwEAYH...

All positive tests obtain a fresh reEnrollmentToken inline via the
complete_re_enrollment_token fixture.
"""

import base64
import uuid

import allure
import pytest


def _unique_device_id() -> str:
    """Generate a unique device identifier for test isolation."""
    return f"test_device_{uuid.uuid4().hex[:8]}"


def _assert_error_structure(result: dict) -> None:
    """Assert that a 400/500 response contains all required error fields."""
    for field in ("errorCode", "errorMsg", "status", "timestamp"):
        assert field in result, f"Expected '{field}' in error response, got: {result}"


# ==============================================================================
# POSITIVE TESTS
# ==============================================================================

@allure.feature("Re-Enrollment API")
@allure.story("Complete Re-Enrollment")
@allure.title("completeReEnroll returns registrationCode with token only")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Sends only the reEnrollmentToken (no device fields). "
    "Expects HTTP 200 with a non-empty registrationCode. "
    "This is the minimal valid call — device fields are optional."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_complete_re_enroll(
    api_client,
    re_enrollment_base_path,
    complete_re_enrollment_token,
):
    """Minimal completeReEnroll call (token only) → 200 + registrationCode."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/completeReEnroll",
        json={"reEnrollmentToken": complete_re_enrollment_token},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "registrationCode" in result, (
        f"Expected 'registrationCode' in response, got: {result}"
    )
    assert result["registrationCode"], "registrationCode must not be empty"

    print(f"\n[OK] completeReEnroll → registrationCode: {result['registrationCode']}")

    allure.attach(
        f"registrationCode: {result['registrationCode']}",
        name="Re-Enrollment Result",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Re-Enrollment API")
@allure.story("Complete Re-Enrollment")
@allure.title("completeReEnroll adds a new device (addOrUpdate=0)")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends reEnrollmentToken + deviceId + ECDSA publicKey (from GET_PUBLIC_KEY_USERNAME "
    "in .env as raw base64, or generated dynamically if absent) + addOrUpdate=0 "
    "(add new device without removing existing ones). Expects HTTP 200 with registrationCode."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_complete_re_enroll_add_device(
    api_client,
    re_enrollment_base_path,
    complete_re_enrollment_token,
    re_enrollment_public_key,
):
    """completeReEnroll with addOrUpdate=0 (add device) → 200 + registrationCode."""
    device_id = _unique_device_id()
    public_key = re_enrollment_public_key

    print(f"\n[INFO] deviceId: {device_id}")
    print(f"[INFO] publicKey (first 40 chars): {public_key[:40]}...")

    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/completeReEnroll",
        json={
            "reEnrollmentToken": complete_re_enrollment_token,
            "deviceId": device_id,
            "publicKey": public_key,
            "addOrUpdate": 0,
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "registrationCode" in result, (
        f"Expected 'registrationCode' in response, got: {result}"
    )
    assert result["registrationCode"], "registrationCode must not be empty"

    print(f"\n[OK] Add device → registrationCode: {result['registrationCode']}")

    allure.attach(
        f"deviceId:         {device_id}\n"
        f"addOrUpdate:      0 (add)\n"
        f"registrationCode: {result['registrationCode']}",
        name="Add Device Result",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Re-Enrollment API")
@allure.story("Complete Re-Enrollment")
@allure.title("completeReEnroll replaces existing device (addOrUpdate=1)")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends reEnrollmentToken + deviceId + ECDSA publicKey (from GET_PUBLIC_KEY_USERNAME "
    "in .env as raw base64, or generated dynamically if absent) + addOrUpdate=1 "
    "(replace — removes all existing devices and registers this one). "
    "Expects HTTP 200 with registrationCode."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_complete_re_enroll_replace_device(
    api_client,
    re_enrollment_base_path,
    complete_re_enrollment_token,
    re_enrollment_public_key,
):
    """completeReEnroll with addOrUpdate=1 (replace device) → 200 + registrationCode."""
    device_id = _unique_device_id()
    public_key = re_enrollment_public_key

    print(f"\n[INFO] deviceId: {device_id}")
    print(f"[INFO] publicKey (first 40 chars): {public_key[:40]}...")

    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/completeReEnroll",
        json={
            "reEnrollmentToken": complete_re_enrollment_token,
            "deviceId": device_id,
            "publicKey": public_key,
            "addOrUpdate": 1,
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "registrationCode" in result, (
        f"Expected 'registrationCode' in response, got: {result}"
    )
    assert result["registrationCode"], "registrationCode must not be empty"

    print(f"\n[OK] Replace device → registrationCode: {result['registrationCode']}")

    allure.attach(
        f"deviceId:         {device_id}\n"
        f"addOrUpdate:      1 (replace)\n"
        f"registrationCode: {result['registrationCode']}",
        name="Replace Device Result",
        attachment_type=allure.attachment_type.TEXT,
    )


# ==============================================================================
# NEGATIVE TESTS
# ==============================================================================

@allure.feature("Re-Enrollment API")
@allure.story("Complete Re-Enrollment - Negative")
@allure.title("completeReEnroll with invalid reEnrollmentToken returns 400 or 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a random UUID as reEnrollmentToken. "
    "Expects HTTP 400 or 500 with errorCode, errorMsg, status, and timestamp."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_complete_re_enroll_invalid_token(
    api_client,
    re_enrollment_base_path,
):
    """Invalid reEnrollmentToken → 400/500 with error structure."""
    fake_token = str(uuid.uuid4())

    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/completeReEnroll",
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
@allure.story("Complete Re-Enrollment - Negative")
@allure.title("completeReEnroll with missing reEnrollmentToken returns 400 or 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends an empty JSON body without the reEnrollmentToken field. "
    "Expects HTTP 400 or 500 with a structured error response."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_complete_re_enroll_missing_token(
    api_client,
    re_enrollment_base_path,
):
    """Missing reEnrollmentToken field → 400/500 with error structure."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/completeReEnroll",
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


@allure.feature("Re-Enrollment API")
@allure.story("Complete Re-Enrollment - Negative")
@allure.title("completeReEnroll with malformed publicKey returns 400 or 500")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends a valid reEnrollmentToken with a deviceId and a publicKey that is "
    "not a valid ECDSA key (plain random string). "
    "Expects HTTP 400 or 500 — the server must reject invalid key data."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_complete_re_enroll_invalid_public_key(
    api_client,
    re_enrollment_base_path,
    complete_re_enrollment_token,
):
    """Valid token + malformed publicKey → 400/500 with error structure."""
    malformed_key = base64.b64encode(b"this-is-not-a-valid-ecdsa-key").decode("utf-8")

    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/completeReEnroll",
        json={
            "reEnrollmentToken": complete_re_enrollment_token,
            "deviceId": _unique_device_id(),
            "publicKey": malformed_key,
            "addOrUpdate": 0,
        },
    )

    assert response.status_code in (400, 500), (
        f"Expected 400 or 500 for malformed publicKey, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    _assert_error_structure(result)

    print(f"\n[OK] Malformed publicKey rejected: {response.status_code}")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")
