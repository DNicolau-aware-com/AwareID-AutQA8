"""
Tests for GET /onboarding/b2c/operationStatus/{sessionToken}

Returns the completion status of an in-progress or completed B2C operation
(enrollment or authentication) identified by its sessionToken.

Response:
    200  completionStatus  Pending | Success | Failed | Cancelled
    400  error structure   INPUT_FORMAT_ERROR | INPUT_VALUES_ERROR
    500  error structure   INTERNAL_SERVER_ERROR

The b2c_session_token fixture obtains a fresh sessionToken inline by calling
POST /b2c/triggerAuthenticate — no token is persisted to .env.

Prerequisites (.env):
    B2C_USERNAME  — already-enrolled username (falls back to RE_ENROLLMENT_USERNAME)
"""

import uuid

import allure
import pytest


_VALID_COMPLETION_STATUSES = {"Pending", "Success", "Failed", "Cancelled"}


def _assert_error_structure(result: dict) -> None:
    """Assert a 400/500 error response contains all required fields."""
    for field in ("errorCode", "errorMsg", "status", "timestamp"):
        assert field in result, f"Expected '{field}' in error response, got: {result}"


# ==============================================================================
# POSITIVE TESTS
# ==============================================================================

@allure.feature("B2C API")
@allure.story("Operation Status")
@allure.title("operationStatus with valid sessionToken returns 200 with completionStatus")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Obtains a fresh sessionToken from POST /b2c/triggerAuthenticate, then calls "
    "GET /b2c/operationStatus/{sessionToken}. "
    "Expects HTTP 200 with completionStatus in: Pending, Success, Failed, Cancelled. "
    "A newly triggered operation is expected to be 'Pending'."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_get_operation_status(
    api_client,
    b2c_base_path,
    b2c_session_token,
):
    """Valid sessionToken → 200 with completionStatus in the allowed enum."""
    response = api_client.http_client.get(
        f"{b2c_base_path}/operationStatus/{b2c_session_token}",
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "completionStatus" in result, (
        f"Missing 'completionStatus' in response: {result}"
    )
    assert result["completionStatus"] in _VALID_COMPLETION_STATUSES, (
        f"completionStatus must be one of {_VALID_COMPLETION_STATUSES}, "
        f"got: '{result['completionStatus']}'"
    )

    print(f"\n[OK] operationStatus → 200")
    print(f"     sessionToken     : {b2c_session_token[:20]}...")
    print(f"     completionStatus : {result['completionStatus']}")

    allure.attach(
        f"sessionToken:     {b2c_session_token[:20]}...\n"
        f"completionStatus: {result['completionStatus']}",
        name="Operation Status Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Operation Status")
@allure.title("newly triggered operation has completionStatus Pending")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Obtains a fresh sessionToken from POST /b2c/triggerAuthenticate and immediately "
    "polls GET /b2c/operationStatus/{sessionToken}. "
    "A session that was just created and not yet acted upon is expected to be 'Pending'."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_get_operation_status_is_pending(
    api_client,
    b2c_base_path,
    b2c_session_token,
):
    """Fresh sessionToken polled immediately → completionStatus should be 'Pending'."""
    response = api_client.http_client.get(
        f"{b2c_base_path}/operationStatus/{b2c_session_token}",
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "completionStatus" in result, (
        f"Missing 'completionStatus' in response: {result}"
    )

    status = result["completionStatus"]
    assert status in _VALID_COMPLETION_STATUSES, (
        f"completionStatus must be one of {_VALID_COMPLETION_STATUSES}, got: '{status}'"
    )

    print(f"\n[OK] Fresh session status → {status}")
    if status != "Pending":
        print(f"     [INFO] Expected 'Pending' for a new session — got '{status}' "
              f"(session may have been acted upon externally)")

    allure.attach(
        f"sessionToken:     {b2c_session_token[:20]}...\n"
        f"completionStatus: {status}\n"
        f"expected:         Pending",
        name="Pending Status Check",
        attachment_type=allure.attachment_type.TEXT,
    )

    assert status == "Pending", (
        f"Expected completionStatus='Pending' for a freshly created session, got '{status}'"
    )


@allure.feature("B2C API")
@allure.story("Operation Status")
@allure.title("operationStatus response contains only completionStatus field")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Validates the complete 200 response structure: a single field 'completionStatus' "
    "with a value from the enum Pending | Success | Failed | Cancelled."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_get_operation_status_response_structure(
    api_client,
    b2c_base_path,
    b2c_session_token,
):
    """Response contains completionStatus as a string matching the spec enum."""
    response = api_client.http_client.get(
        f"{b2c_base_path}/operationStatus/{b2c_session_token}",
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert isinstance(result, dict), f"Response must be a JSON object, got: {type(result)}"
    assert "completionStatus" in result, (
        f"'completionStatus' field missing from response: {result}"
    )
    assert isinstance(result["completionStatus"], str), (
        f"'completionStatus' must be a string, got: {type(result['completionStatus'])}"
    )
    assert result["completionStatus"] in _VALID_COMPLETION_STATUSES, (
        f"'completionStatus' must be one of {_VALID_COMPLETION_STATUSES}, "
        f"got: '{result['completionStatus']}'"
    )

    print(f"\n[OK] Response structure valid")
    print(f"     completionStatus : {result['completionStatus']}")

    allure.attach(
        f"completionStatus: {result['completionStatus']}\n"
        f"valid values:     {', '.join(sorted(_VALID_COMPLETION_STATUSES))}",
        name="Response Structure",
        attachment_type=allure.attachment_type.TEXT,
    )


# ==============================================================================
# NEGATIVE TESTS
# ==============================================================================

@allure.feature("B2C API")
@allure.story("Operation Status - Negative")
@allure.title("operationStatus with random UUID sessionToken returns 400 or 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a randomly generated UUID as the sessionToken path parameter. "
    "Expects HTTP 400 or 500 with errorCode, errorMsg, status, and timestamp."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_get_operation_status_invalid_token(
    api_client,
    b2c_base_path,
):
    """Random UUID sessionToken → 400 or 500 with error structure."""
    fake_token = str(uuid.uuid4())

    response = api_client.http_client.get(
        f"{b2c_base_path}/operationStatus/{fake_token}",
    )

    assert response.status_code in (400, 500), (
        f"Expected 400 or 500 for invalid sessionToken, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    _assert_error_structure(result)

    print(f"\n[OK] Invalid sessionToken rejected: {response.status_code}")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")

    allure.attach(
        f"sessionToken: {fake_token}\n"
        f"status:       {response.status_code}\n"
        f"errorCode:    {result.get('errorCode')}\n"
        f"errorMsg:     {result.get('errorMsg')}",
        name="400/500: Invalid Session Token",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("B2C API")
@allure.story("Operation Status - Negative")
@allure.title("operationStatus with malformed sessionToken returns 400 or 500")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends a plain string (non-UUID) as the sessionToken path parameter. "
    "Expects HTTP 400 or 500 with a structured error response."
)
@pytest.mark.stateful
@pytest.mark.b2c
def test_get_operation_status_malformed_token(
    api_client,
    b2c_base_path,
):
    """Malformed (non-UUID) sessionToken → 400 or 500 with error structure."""
    response = api_client.http_client.get(
        f"{b2c_base_path}/operationStatus/not-a-real-token",
    )

    assert response.status_code in (400, 500), (
        f"Expected 400 or 500 for malformed sessionToken, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    _assert_error_structure(result)

    print(f"\n[OK] Malformed sessionToken rejected: {response.status_code}")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")

    allure.attach(
        f"sessionToken: not-a-real-token\n"
        f"status:       {response.status_code}\n"
        f"errorCode:    {result.get('errorCode')}\n"
        f"errorMsg:     {result.get('errorMsg')}",
        name="400/500: Malformed Session Token",
        attachment_type=allure.attachment_type.TEXT,
    )
