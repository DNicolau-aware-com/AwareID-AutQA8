"""
Tests for POST /onboarding/b2c/triggerEnroll

Triggers an enrollment session via the B2C Authenticator.
Returns a sessionToken, sessionCallbackURL, and a QR code image
that the authenticator app scans to begin the enrollment flow.

Actual API behaviour (observed):
    - Always returns HTTP 200.
    - On success:  status='SUCCESS', sessionToken/sessionCallbackURL/qrcodeImage populated.
    - On failure:  status='FAILURE', those fields are null, errorSummary explains the cause.
    - Missing / empty / unknown username → 200 status='FAILURE' (not 400/500).

Each positive test registers a fresh user with email dnicolau.aware@gmail.com
(enroll + addFace) via the b2c_enrolled_user fixture.

Prerequisites (.env):
    FACE      — base64-encoded live JPEG face image
    WORKFLOW  — liveness workflow name (default: charlie4)
"""

import allure
import pytest


# ==============================================================================
# HELPERS
# ==============================================================================

def _assert_success_response(result: dict) -> None:
    """
    Assert a 200 SUCCESS response:
        status             'SUCCESS'
        sessionToken       non-empty string
        sessionCallbackURL non-empty string
        qrcodeImage        non-empty base64 string
    """
    assert result.get("status") == "SUCCESS", (
        f"Expected status='SUCCESS', got '{result.get('status')}'. "
        f"errorSummary: {result.get('errorSummary')}"
    )
    for field in ("sessionToken", "sessionCallbackURL", "qrcodeImage"):
        assert result.get(field), (
            f"'{field}' must be a non-empty string on SUCCESS, got: {result.get(field)!r}"
        )


def _assert_failure_response(result: dict) -> None:
    """
    Assert a 200 FAILURE response:
        status             'FAILURE'
        sessionToken       null
        sessionCallbackURL null
        qrcodeImage        null
    """
    assert result.get("status") == "FAILURE", (
        f"Expected status='FAILURE', got '{result.get('status')}'"
    )
    for field in ("sessionToken", "sessionCallbackURL", "qrcodeImage"):
        assert result.get(field) is None, (
            f"'{field}' must be null on FAILURE, got: {result.get(field)!r}"
        )


# ==============================================================================
# POSITIVE TESTS
# ==============================================================================

@allure.feature("B2C API")
@allure.story("Trigger Enrollment")
@allure.title("triggerEnroll with enrolled username returns 200 SUCCESS")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Sends username + email (dnicolau.aware@gmail.com) to POST /b2c/triggerEnroll "
    "for a Keycloak B2C pre-registered user. "
    "Email is included explicitly because the server may not have it in the "
    "pre-registration event. "
    "Expects HTTP 200 with status='SUCCESS', a non-empty sessionToken, "
    "sessionCallbackURL, and a base64 qrcodeImage."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_enroll(
    api_client,
    b2c_base_path,
    b2c_enrolled_user,
):
    """Freshly enrolled username → 200 SUCCESS with populated session fields."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerEnroll",
        json={
            "username": b2c_enrolled_user["username"],
            "email": b2c_enrolled_user["email"],
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_success_response(result)

    print(f"\n[OK] triggerEnroll → 200 SUCCESS")
    print(f"     username          : {b2c_enrolled_user['username']}")
    print(f"     sessionToken      : {result['sessionToken'][:20]}...")
    print(f"     sessionCallbackURL: {result['sessionCallbackURL'][:60]}...")
    print(f"     qrcodeImage       : (base64 PNG, length={len(result['qrcodeImage'])})")

    allure.attach(
        f"username:          {b2c_enrolled_user['username']}\n"
        f"email:             {b2c_enrolled_user['email']}\n"
        f"status:            {result['status']}\n"
        f"sessionToken:      {result['sessionToken'][:20]}...\n"
        f"sessionCallbackURL:{result['sessionCallbackURL']}\n"
        f"qrcodeImage:       (base64 PNG, length={len(result['qrcodeImage'])})",
        name="triggerEnroll Session Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Enrollment")
@allure.title("triggerEnroll with username and email returns 200 SUCCESS")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Registers a fresh user with dnicolau.aware@gmail.com (enroll + addFace), "
    "then sends username + email to POST /b2c/triggerEnroll. "
    "Expects HTTP 200 status='SUCCESS' with a valid session response."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_enroll_with_email(
    api_client,
    b2c_base_path,
    b2c_enrolled_user,
):
    """username + email → 200 SUCCESS with valid session fields."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerEnroll",
        json={
            "username": b2c_enrolled_user["username"],
            "email": b2c_enrolled_user["email"],
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_success_response(result)

    print(f"\n[OK] triggerEnroll with email → 200 SUCCESS")
    print(f"     username     : {b2c_enrolled_user['username']}")
    print(f"     email        : {b2c_enrolled_user['email']}")
    print(f"     sessionToken : {result['sessionToken'][:20]}...")

    allure.attach(
        f"username: {b2c_enrolled_user['username']}\n"
        f"email:    {b2c_enrolled_user['email']}\n"
        f"status:   {result['status']}",
        name="triggerEnroll with Email",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Enrollment")
@allure.title("triggerEnroll with notifyByEmail=true returns 200 SUCCESS")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Registers a fresh user with dnicolau.aware@gmail.com (enroll + addFace), "
    "then sends username + email + notifyOptions.notifyByEmail=true. "
    "Expects HTTP 200 status='SUCCESS' — the enrollment link is delivered "
    "to dnicolau.aware@gmail.com."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_enroll_notify_by_email(
    api_client,
    b2c_base_path,
    b2c_enrolled_user,
):
    """username + email + notifyByEmail=true → 200 SUCCESS, link sent to dnicolau.aware@gmail.com."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerEnroll",
        json={
            "username": b2c_enrolled_user["username"],
            "email": b2c_enrolled_user["email"],
            "notifyOptions": {"notifyByEmail": True},
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_success_response(result)

    print(f"\n[OK] triggerEnroll notifyByEmail=true → 200 SUCCESS")
    print(f"     email        : {b2c_enrolled_user['email']}")
    print(f"     sessionToken : {result['sessionToken'][:20]}...")

    allure.attach(
        f"username:      {b2c_enrolled_user['username']}\n"
        f"email:         {b2c_enrolled_user['email']}\n"
        f"notifyByEmail: true\n"
        f"status:        {result['status']}",
        name="triggerEnroll Notify by Email",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Enrollment")
@allure.title("triggerEnroll 200 SUCCESS response contains all required fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends username + email to POST /b2c/triggerEnroll and validates the complete "
    "200 SUCCESS response structure against the API spec: "
    "status='SUCCESS', sessionToken (non-empty string), "
    "sessionCallbackURL (valid URL starting with 'http'), "
    "qrcodeImage (non-trivial base64 PNG, length > 100)."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_enroll_response_structure(
    api_client,
    b2c_base_path,
    b2c_enrolled_user,
):
    """Full response structure validation for a successful triggerEnroll call."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerEnroll",
        json={
            "username": b2c_enrolled_user["username"],
            "email": b2c_enrolled_user["email"],
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_success_response(result)

    # qrcodeImage must be a non-trivial base64 string
    qr = result["qrcodeImage"]
    assert len(qr) > 100, (
        f"qrcodeImage looks too short to be a real QR code PNG: length={len(qr)}"
    )

    # sessionCallbackURL must look like a URL
    cb_url = result["sessionCallbackURL"]
    assert cb_url.startswith("http"), (
        f"sessionCallbackURL does not look like a URL: '{cb_url}'"
    )

    print(f"\n[OK] triggerEnroll response structure valid")
    print(f"     status            : {result['status']}")
    print(f"     sessionToken      : {result['sessionToken'][:20]}...")
    print(f"     sessionCallbackURL: {cb_url}")
    print(f"     qrcodeImage len   : {len(qr)} chars")

    allure.attach(
        f"status:            {result['status']}\n"
        f"sessionToken:      {result['sessionToken'][:20]}...\n"
        f"sessionCallbackURL:{cb_url}\n"
        f"qrcodeImage len:   {len(qr)} chars",
        name="Response Structure Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


# ==============================================================================
# NEGATIVE TESTS
# ==============================================================================

@allure.feature("B2C API")
@allure.story("Trigger Enrollment - Negative")
@allure.title("triggerEnroll with missing username returns 200 FAILURE")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends an empty JSON body without the required username field. "
    "The server always returns HTTP 200 — invalid inputs produce "
    "status='FAILURE' with null session fields and a populated errorSummary."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_enroll_missing_username(
    api_client,
    b2c_base_path,
):
    """Missing username → 200 with status='FAILURE' and null session fields."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerEnroll",
        json={},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_failure_response(result)

    print(f"\n[OK] Missing username → 200 FAILURE")
    print(f"     errorSummary : {str(result.get('errorSummary', ''))[:100]}")

    allure.attach(
        f"status:       {result['status']}\n"
        f"errorSummary: {result.get('errorSummary')}",
        name="FAILURE: Missing Username",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Enrollment - Negative")
@allure.title("triggerEnroll with empty username returns 200 FAILURE")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends an empty string as username. "
    "The server returns HTTP 200 with status='FAILURE', null session fields, "
    "and an errorSummary describing the cause."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_enroll_empty_username(
    api_client,
    b2c_base_path,
):
    """Empty username string → 200 with status='FAILURE' and null session fields."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerEnroll",
        json={"username": ""},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_failure_response(result)

    print(f"\n[OK] Empty username → 200 FAILURE")
    print(f"     errorSummary : {str(result.get('errorSummary', ''))[:100]}")

    allure.attach(
        f"status:       {result['status']}\n"
        f"errorSummary: {result.get('errorSummary')}",
        name="FAILURE: Empty Username",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Enrollment - Negative")
@allure.title("triggerEnroll with unknown username returns 200 FAILURE")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a randomly generated username that does not exist in the system. "
    "Expects HTTP 200 with status='FAILURE' and null session fields — "
    "the server cannot find the user and returns an errorSummary."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_enroll_unknown_username(
    api_client,
    b2c_base_path,
    unique_username,
):
    """Non-existent username → 200 with status='FAILURE' and null session fields."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerEnroll",
        json={"username": unique_username},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_failure_response(result)

    print(f"\n[OK] Unknown username → 200 FAILURE")
    print(f"     username     : {unique_username}")
    print(f"     errorSummary : {str(result.get('errorSummary', ''))[:100]}")

    allure.attach(
        f"username:     {unique_username}\n"
        f"status:       {result['status']}\n"
        f"errorSummary: {result.get('errorSummary')}",
        name="FAILURE: Unknown Username",
        attachment_type=allure.attachment_type.TEXT,
    )
