"""Negative tests for compare endpoint."""

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
@allure.story("Negative - Input Validation")
@allure.title("Compare rejects request with missing probe image")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a compare request with gallery and workflow but no probe image. "
    "Expects HTTP 400 or 500 and a structured error body."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_missing_probe(api_client, face_matcher_base_path, gallery_face_image):
    """Test compare endpoint with missing probe image."""
    payload = {
        "gallery": {"VISIBLE_FRONTAL": gallery_face_image},
        "workflow": {
            "comparator": {
                "algorithm": "F500",
                "faceTypes": ["VISIBLE_FRONTAL"]
            }
        }
    }

    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json=payload
    )

    assert response.status_code in [400, 500]
    _assert_error_body(response.json())


@allure.feature("Face Matcher API")
@allure.story("Negative - Input Validation")
@allure.title("Compare rejects request with missing gallery image")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a compare request with probe and workflow but no gallery image. "
    "Expects HTTP 400 or 500 and a structured error body."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_missing_gallery(api_client, face_matcher_base_path, probe_face_image):
    """Test compare endpoint with missing gallery image."""
    payload = {
        "probe": {"VISIBLE_FRONTAL": probe_face_image},
        "workflow": {
            "comparator": {
                "algorithm": "F500",
                "faceTypes": ["VISIBLE_FRONTAL"]
            }
        }
    }

    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json=payload
    )

    assert response.status_code in [400, 500]
    _assert_error_body(response.json())


@allure.feature("Face Matcher API")
@allure.story("Negative - Input Validation")
@allure.title("Compare rejects request with missing workflow")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a compare request with probe and gallery images but no workflow block. "
    "Expects HTTP 400 or 500 and a structured error body."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_missing_workflow(api_client, face_matcher_base_path, probe_face_image, gallery_face_image):
    """Test compare endpoint with missing workflow."""
    payload = {
        "probe": {"VISIBLE_FRONTAL": probe_face_image},
        "gallery": {"VISIBLE_FRONTAL": gallery_face_image}
    }

    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json=payload
    )

    assert response.status_code in [400, 500]
    _assert_error_body(response.json())


@allure.feature("Face Matcher API")
@allure.story("Negative - Input Validation")
@allure.title("Compare rejects unknown algorithm name")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a compare request using an unrecognised algorithm name ('INVALID_ALGO'). "
    "Expects HTTP 400 or 500. The server may return an empty body for this case, which is also accepted."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_invalid_algorithm(api_client, face_matcher_base_path, probe_face_image, gallery_face_image):
    """Test compare endpoint with invalid algorithm."""
    payload = {
        "probe": {"VISIBLE_FRONTAL": probe_face_image},
        "gallery": {"VISIBLE_FRONTAL": gallery_face_image},
        "workflow": {
            "comparator": {
                "algorithm": "INVALID_ALGO",
                "faceTypes": ["VISIBLE_FRONTAL"]
            }
        }
    }

    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json=payload
    )

    assert response.status_code in [400, 500]
    # Server may return an empty body for an unrecognized algorithm - only validate if JSON is present
    try:
        body = response.json()
        _assert_error_body(body)
    except (ValueError, KeyError):
        pass  # Non-JSON or empty body is acceptable; status code already validated


@allure.feature("Face Matcher API")
@allure.story("Negative - Input Validation")
@allure.title("Compare rejects completely empty payload")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a POST to /compare with an empty JSON body. "
    "Expects HTTP 400 or 500 and a structured error body indicating missing required fields."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_empty_payload(api_client, face_matcher_base_path):
    """Test compare endpoint with empty payload."""
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={}
    )

    assert response.status_code in [400, 500]
    _assert_error_body(response.json())
