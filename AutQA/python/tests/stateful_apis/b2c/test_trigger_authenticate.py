"""
Tests for POST /onboarding/b2c/triggerAuthenticate

Triggers an authentication session via the B2C Authenticator.
Returns a sessionToken, sessionCallbackURL, and a QR code image
that the authenticator app scans to perform the B2C authentication.

Actual API behaviour (consistent with triggerEnroll):
    - Always returns HTTP 200.
    - On success:  status='SUCCESS', sessionToken/sessionCallbackURL/qrcodeImage populated.
    - On failure:  status='FAILURE', those fields are null, errorSummary explains the cause.
    - Missing / empty / unknown username → 200 status='FAILURE' (not 400/500).

Differences from triggerEnroll:
    - Endpoint: /b2c/triggerAuthenticate
    - No 'email' or 'phoneNumber' in request body.
    - notifyOptions supports both notifyByEmail and notifyByPush.

Prerequisites (.env):
    B2C_USERNAME  — already-enrolled username (falls back to RE_ENROLLMENT_USERNAME)
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


# ==============================================================================
# POSITIVE TESTS
# ==============================================================================

@allure.feature("B2C API")
@allure.story("Trigger Authentication")
@allure.title("triggerAuthenticate with enrolled username returns 200 SUCCESS")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Sends the minimum required payload (username only) to POST /b2c/triggerAuthenticate "
    "using an already-enrolled user from B2C_USERNAME (.env). "
    "Expects HTTP 200 with status='SUCCESS', a non-empty sessionToken, "
    "sessionCallbackURL, and a base64 qrcodeImage."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_authenticate(
    api_client,
    b2c_base_path,
    b2c_enrolled_user,
):
    """Enrolled username → 200 SUCCESS with populated session fields."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerAuthenticate",
        json={"username": b2c_enrolled_user["username"]},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_success_response(result)

    print(f"\n[OK] triggerAuthenticate → 200 SUCCESS")
    print(f"     username          : {b2c_enrolled_user['username']}")
    print(f"     sessionToken      : {result['sessionToken'][:20]}...")
    print(f"     sessionCallbackURL: {result['sessionCallbackURL'][:60]}...")
    print(f"     qrcodeImage       : (base64 PNG, length={len(result['qrcodeImage'])})")

    allure.attach(
        f"username:          {b2c_enrolled_user['username']}\n"
        f"status:            {result['status']}\n"
        f"sessionToken:      {result['sessionToken'][:20]}...\n"
        f"sessionCallbackURL:{result['sessionCallbackURL']}\n"
        f"qrcodeImage:       (base64 PNG, length={len(result['qrcodeImage'])})",
        name="triggerAuthenticate Session Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Authentication")
@allure.title("triggerAuthenticate with notifyByEmail=true returns 200 SUCCESS")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends username + notifyOptions.notifyByEmail=true to POST /b2c/triggerAuthenticate. "
    "Expects HTTP 200 status='SUCCESS' — the authentication link is delivered "
    "to dnicolau.aware@gmail.com and a valid session response is returned."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_authenticate_notify_by_email(
    api_client,
    b2c_base_path,
    b2c_enrolled_user,
):
    """username + notifyByEmail=true → 200 SUCCESS, link sent to dnicolau.aware@gmail.com."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerAuthenticate",
        json={
            "username": b2c_enrolled_user["username"],
            "notifyOptions": {"notifyByEmail": True},
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_success_response(result)

    print(f"\n[OK] triggerAuthenticate notifyByEmail=true → 200 SUCCESS")
    print(f"     username     : {b2c_enrolled_user['username']}")
    print(f"     sessionToken : {result['sessionToken'][:20]}...")

    allure.attach(
        f"username:      {b2c_enrolled_user['username']}\n"
        f"notifyByEmail: true\n"
        f"status:        {result['status']}\n"
        f"sessionToken:  {result['sessionToken'][:20]}...",
        name="triggerAuthenticate Notify by Email",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Authentication")
@allure.title("triggerAuthenticate with notifyByPush=true returns 200 SUCCESS")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends username + notifyOptions.notifyByPush=true to POST /b2c/triggerAuthenticate. "
    "Expects HTTP 200 status='SUCCESS' — the server attempts to deliver an "
    "authentication push notification to the user's registered device."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_authenticate_notify_by_push(
    api_client,
    b2c_base_path,
    b2c_enrolled_user,
):
    """username + notifyByPush=true → 200 SUCCESS."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerAuthenticate",
        json={
            "username": b2c_enrolled_user["username"],
            "notifyOptions": {"notifyByPush": True},
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_success_response(result)

    print(f"\n[OK] triggerAuthenticate notifyByPush=true → 200 SUCCESS")
    print(f"     username     : {b2c_enrolled_user['username']}")
    print(f"     sessionToken : {result['sessionToken'][:20]}...")

    allure.attach(
        f"username:     {b2c_enrolled_user['username']}\n"
        f"notifyByPush: true\n"
        f"status:       {result['status']}\n"
        f"sessionToken: {result['sessionToken'][:20]}...",
        name="triggerAuthenticate Notify by Push",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Authentication")
@allure.title("triggerAuthenticate 200 SUCCESS response contains all required fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Validates the complete 200 SUCCESS response structure against the API spec: "
    "status='SUCCESS', sessionToken (non-empty string), "
    "sessionCallbackURL (valid URL starting with 'http'), "
    "qrcodeImage (non-trivial base64 PNG, length > 100)."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_authenticate_response_structure(
    api_client,
    b2c_base_path,
    b2c_enrolled_user,
):
    """Full response structure validation for a successful triggerAuthenticate call."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerAuthenticate",
        json={"username": b2c_enrolled_user["username"]},
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

    print(f"\n[OK] triggerAuthenticate response structure valid")
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
@allure.story("Trigger Authentication - Negative")
@allure.title("triggerAuthenticate with missing username returns 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends an empty JSON body without the required username field. "
    "Unlike triggerEnroll (which returns 200 FAILURE), triggerAuthenticate "
    "returns HTTP 500 with errorCode, errorMsg, status, and timestamp."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_authenticate_missing_username(
    api_client,
    b2c_base_path,
):
    """Missing username → 500 with error structure."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerAuthenticate",
        json={},
    )

    assert response.status_code == 500, (
        f"Expected 500 for missing username, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    for field in ("errorCode", "errorMsg", "status", "timestamp"):
        assert field in result, f"Expected '{field}' in 500 response, got: {result}"

    print(f"\n[OK] Missing username → 500")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")

    allure.attach(
        f"errorCode: {result.get('errorCode')}\n"
        f"errorMsg:  {result.get('errorMsg')}\n"
        f"status:    {result.get('status')}",
        name="500: Missing Username",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Authentication - Negative")
@allure.title("triggerAuthenticate with empty username returns 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends an empty string as username. "
    "triggerAuthenticate returns HTTP 500 with a structured error response."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_authenticate_empty_username(
    api_client,
    b2c_base_path,
):
    """Empty username string → 500 with error structure."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerAuthenticate",
        json={"username": ""},
    )

    assert response.status_code == 500, (
        f"Expected 500 for empty username, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    for field in ("errorCode", "errorMsg", "status", "timestamp"):
        assert field in result, f"Expected '{field}' in 500 response, got: {result}"

    print(f"\n[OK] Empty username → 500")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")

    allure.attach(
        f"errorCode: {result.get('errorCode')}\n"
        f"errorMsg:  {result.get('errorMsg')}\n"
        f"status:    {result.get('status')}",
        name="500: Empty Username",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Trigger Authentication - Negative")
@allure.title("triggerAuthenticate with unknown username returns 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a randomly generated username that does not exist in the system. "
    "triggerAuthenticate returns HTTP 500 — unlike triggerEnroll which returns "
    "200 with status='FAILURE', this endpoint raises a server error for unknown users."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_trigger_authenticate_unknown_username(
    api_client,
    b2c_base_path,
    unique_username,
):
    """Non-existent username → 500 with error structure."""
    response = api_client.http_client.post(
        f"{b2c_base_path}/triggerAuthenticate",
        json={"username": unique_username},
    )

    assert response.status_code == 500, (
        f"Expected 500 for unknown username, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    for field in ("errorCode", "errorMsg", "status", "timestamp"):
        assert field in result, f"Expected '{field}' in 500 response, got: {result}"

    print(f"\n[OK] Unknown username → 500")
    print(f"     username  : {unique_username}")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")

    allure.attach(
        f"username:  {unique_username}\n"
        f"errorCode: {result.get('errorCode')}\n"
        f"errorMsg:  {result.get('errorMsg')}\n"
        f"status:    {result.get('status')}",
        name="500: Unknown Username",
        attachment_type=allure.attachment_type.TEXT,
    )
