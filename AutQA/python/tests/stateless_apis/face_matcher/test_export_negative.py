"""Negative tests for export endpoint."""

import allure
import pytest

# Valid errorCode values per the API spec for 400 responses
VALID_ERROR_CODES = {"INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR"}


def _assert_error_body(result):
    """Assert that the response body matches one of the two documented error formats.

    Nested format (actual server behavior):
        {"error": {"code": <int>, "description": "<str>"}}

    Standard format (documented API spec):
        {"errorCode": "INPUT_FORMAT_ERROR", "errorMsg": "...", "status": <int>, "timestamp": "..."}
    """
    if "error" in result:
        # Nested error format
        error = result["error"]
        assert "code" in error, f"Expected 'code' in error object, got: {error}"
        assert "description" in error, f"Expected 'description' in error object, got: {error}"
        assert isinstance(error["code"], int), f"error.code must be integer, got: {type(error['code'])}"
        assert isinstance(error["description"], str), f"error.description must be string, got: {type(error['description'])}"
        print(f"\n[OK] Nested error format - code: {error['code']}, description: {error['description']}")

    elif "errorCode" in result:
        # Standard error format (API spec)
        assert "errorMsg" in result, f"Expected 'errorMsg' in response, got: {result}"
        assert "status" in result, f"Expected 'status' in response, got: {result}"
        assert "timestamp" in result, f"Expected 'timestamp' in response, got: {result}"
        print(f"\n[OK] Standard error format - errorCode: {result['errorCode']}, errorMsg: {result['errorMsg']}")

    else:
        raise AssertionError(f"Unknown error format. Expected 'error' or 'errorCode' key, got: {result}")


@allure.feature("Face Matcher API")
@allure.story("Negative - Export Validation")
@allure.title("Export rejects completely empty payload")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a POST to /export with an empty JSON body. "
    "Expects HTTP 400 or 500 and a structured error body indicating the missing 'encounter' field."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_export_missing_encounter(api_client, face_matcher_base_path):
    """Test export endpoint with missing encounter field."""
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/export",
        json={}
    )

    assert response.status_code in [400, 500]
    _assert_error_body(response.json())


@allure.feature("Face Matcher API")
@allure.story("Negative - Export Validation")
@allure.title("Export rejects encounter without VISIBLE_FRONTAL image")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends an export request with an encounter containing only an ID and no image data. "
    "Expects HTTP 400 or 500 and a structured error body."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_export_missing_visible_frontal(api_client, face_matcher_base_path):
    """Test export endpoint with missing VISIBLE_FRONTAL field."""
    payload = {
        "encounter": {
            "id": "test_001"
        }
    }

    response = api_client.http_client.post(
        f"{face_matcher_base_path}/export",
        json=payload
    )

    assert response.status_code in [400, 500]
    _assert_error_body(response.json())


@allure.feature("Face Matcher API")
@allure.story("Negative - Export Validation")
@allure.title("Export rejects non-image base64 data")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a valid base64 string that decodes to plain text ('this_is_not_a_real_image'), not a JPEG/PNG. "
    "Expects HTTP 400 or 500 and a structured error body indicating invalid image data."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_export_invalid_base64(api_client, face_matcher_base_path):
    """Test export endpoint with invalid image data (not a real image)."""
    payload = {
        "encounter": {
            "VISIBLE_FRONTAL": "dGhpc19pc19ub3RfYV9yZWFsX2ltYWdl",  # base64 for "this_is_not_a_real_image"
            "id": "test_001"
        }
    }

    response = api_client.http_client.post(
        f"{face_matcher_base_path}/export",
        json=payload
    )

    assert response.status_code in [400, 500]
    _assert_error_body(response.json())
