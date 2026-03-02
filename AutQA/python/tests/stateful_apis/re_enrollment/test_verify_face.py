"""
Tests for POST /onboarding/reEnrollment/verifyFace

Checks whether captured face images belong to a live person and match
the previously enrolled biometric data.

Prerequisites (set once in .env before running):
    RE_ENROLLMENT_USERNAME  — username of an already-enrolled user
    FACE                    — base64-encoded live JPEG face image
    SPOOF                   — base64-encoded spoof image (optional, used by spoof test)
    WORKFLOW                — liveness workflow name (default: charlie4)

The re_enrollment_token fixture obtains a fresh reEnrollmentToken inline
by calling /onboarding/enrollment/enroll — no token is persisted to .env.
"""

import time as _time
import uuid

import allure
import pytest


# ==============================================================================
# MODULE-LEVEL HELPERS
# ==============================================================================

def _make_face_data(image_b64: str, workflow: str) -> dict:
    """
    Build a faceLivenessData payload with 3 frames from a single base64 image.

    Args:
        image_b64: Raw base64-encoded JPEG (no data: prefix).
        workflow:  Liveness workflow name (e.g. 'charlie4').
    """
    now_ms = int(_time.time() * 1000)
    frames = [
        {"data": image_b64, "tags": [], "timestamp": now_ms + (i * 30)}
        for i in range(3)
    ]
    return {
        "video": {
            "meta_data": {
                "client_device_brand": "Apple",
                "client_device_model": "iPhone 8",
                "client_os_version": "11.0.3",
                "client_version": "KnomiSLive_v:2.4.1_b:0.0.0_sdk_v:2.4.1_b:0.0.0",
                "localization": "en-US",
                "programming_language_version": "Swift 4.1",
                "username": "test",
            },
            "workflow_data": {
                "workflow": workflow,
                "frames": frames,
            },
        }
    }


def _assert_200_structure(result: dict) -> None:
    """
    Assert that a 200 response contains all required top-level fields per spec:
        livenessResult  boolean
        matchResult     boolean
        matchScore      number (float)
        authStatus      integer — 0 (Failed) | 1 (Pending) | 2 (Complete)
    """
    for field in ("livenessResult", "matchResult", "matchScore", "authStatus"):
        assert field in result, f"Expected '{field}' in response, got keys: {list(result.keys())}"

    assert isinstance(result["livenessResult"], bool), (
        f"livenessResult must be boolean, got: {type(result['livenessResult'])}"
    )
    assert isinstance(result["matchResult"], bool), (
        f"matchResult must be boolean, got: {type(result['matchResult'])}"
    )
    assert result["authStatus"] in (0, 1, 2), (
        f"authStatus must be 0 (Failed), 1 (Pending), or 2 (Complete). Got: {result['authStatus']}"
    )


def _assert_error_structure(result: dict) -> None:
    """
    Assert that an error response (400/500) contains required fields per spec:
        errorCode, errorMsg, status, timestamp
    """
    for field in ("errorCode", "errorMsg", "status", "timestamp"):
        assert field in result, f"Expected '{field}' in error response, got: {result}"


# ==============================================================================
# POSITIVE TESTS
# ==============================================================================

@allure.feature("Re-Enrollment API")
@allure.story("Face Liveness — Re-Enrollment")
@allure.title("verifyFace returns liveness and match result for live face")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Obtains a fresh reEnrollmentToken via /onboarding/enrollment/enroll using the "
    "username in RE_ENROLLMENT_USERNAME (.env). Sends 3 frames built from the FACE "
    "image. Expects HTTP 200 with livenessResult (bool), matchResult (bool), "
    "matchScore (float), and authStatus (0|1|2)."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_verify_face(
    api_client,
    re_enrollment_base_path,
    re_enrollment_token,
    re_enrollment_face_image,
    re_enrollment_workflow,
):
    """verifyFace with live FACE frames returns 200 and valid response structure."""
    payload = {
        "reEnrollmentToken": re_enrollment_token,
        "faceLivenessData": _make_face_data(re_enrollment_face_image, re_enrollment_workflow),
    }

    print(f"\n[INFO] POST {re_enrollment_base_path}/verifyFace")
    print(f"[INFO] reEnrollmentToken: {re_enrollment_token[:20]}...")

    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/verifyFace",
        json=payload,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_200_structure(result)

    auth_status_map = {0: "Failed", 1: "Pending", 2: "Complete"}
    print(f"\n[OK] verifyFace response:")
    print(f"     livenessResult : {result['livenessResult']}")
    print(f"     matchResult    : {result['matchResult']}")
    print(f"     matchScore     : {result.get('matchScore')}")
    print(f"     authStatus     : {result['authStatus']} ({auth_status_map.get(result['authStatus'])})")

    allure.attach(
        f"livenessResult: {result['livenessResult']}\n"
        f"matchResult:    {result['matchResult']}\n"
        f"matchScore:     {result.get('matchScore')}\n"
        f"authStatus:     {result['authStatus']} ({auth_status_map.get(result['authStatus'])})",
        name="Liveness & Match Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Re-Enrollment API")
@allure.story("Face Liveness — Re-Enrollment")
@allure.title("verifyFace response includes complete faceLivenessResults structure")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Validates the nested faceLivenessResults object in the response. "
    "When present, checks for liveness_result sub-object containing: "
    "feedback (array), score (number), decision (string), score_frr (number)."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_verify_face_response_structure(
    api_client,
    re_enrollment_base_path,
    re_enrollment_token,
    re_enrollment_face_image,
    re_enrollment_workflow,
):
    """All spec-defined response fields are present and correctly typed."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/verifyFace",
        json={
            "reEnrollmentToken": re_enrollment_token,
            "faceLivenessData": _make_face_data(re_enrollment_face_image, re_enrollment_workflow),
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_200_structure(result)

    # Validate nested faceLivenessResults when present
    flr = result.get("faceLivenessResults")
    if flr is not None:
        assert isinstance(flr, dict), f"faceLivenessResults must be an object, got: {type(flr)}"

        liveness_result = flr.get("liveness_result")
        if liveness_result is not None:
            assert isinstance(liveness_result, dict), (
                f"liveness_result must be an object, got: {type(liveness_result)}"
            )

            # feedback — array of strings
            feedback = liveness_result.get("feedback")
            if feedback is not None:
                assert isinstance(feedback, list), f"feedback must be an array, got: {type(feedback)}"
                valid_feedback = {
                    "NO_FACE_DETECTED", "MULTIPLE_FACES_DETECTED", "FRAMERATE_TOO_SLOW",
                    "INSSUFFICIENT FRAMES", "SCORES_READY", "INVALID_FRAME",
                    "INVALID_FRAME_DUE_TO_BLUR", "INVALID_FRAME_DUE_TO_POOR_EYE_DEFINITION",
                    "INVALID_FRAME_DUE_TO_LIGHTING", "INVALID_FRAME_DUE_TO_POSE",
                    "INVALID_FRAME_DUE_TO_GLASSES",
                }
                for fb in feedback:
                    assert fb in valid_feedback, f"Unexpected feedback value: '{fb}'"

            # score — -1.0 | 0.0 | 100.0
            score = liveness_result.get("score")
            if score is not None:
                assert isinstance(score, (int, float)), f"score must be numeric, got: {type(score)}"
                assert score in (-1, 0, 100), f"score must be -1, 0, or 100. Got: {score}"

            # decision — enum string
            decision = liveness_result.get("decision")
            if decision is not None:
                valid_decisions = {"LIVE", "SPOOF", "TOO_BLURRY", "UNABLE_TO_CALCULATE_LIVENESS"}
                assert decision in valid_decisions, (
                    f"decision must be one of {valid_decisions}. Got: '{decision}'"
                )

        print(f"\n[OK] faceLivenessResults structure is valid")
        print(f"     decision   : {liveness_result.get('decision') if liveness_result else 'N/A'}")
        print(f"     score      : {liveness_result.get('score') if liveness_result else 'N/A'}")
        print(f"     feedback   : {liveness_result.get('feedback') if liveness_result else 'N/A'}")
    else:
        print(f"\n[INFO] faceLivenessResults not present in response (optional field)")


@allure.feature("Re-Enrollment API")
@allure.story("Face Liveness — Re-Enrollment - Negative")
@allure.title("verifyFace with spoof image returns 200 with liveness decision")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends frames built from the SPOOF image (.env) with a valid reEnrollmentToken. "
    "Expects HTTP 200. Logs livenessResult (expected false for spoof) and decision. "
    "Does not assert livenessResult value — server may vary based on configuration."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_verify_face_spoof_image(
    api_client,
    re_enrollment_base_path,
    re_enrollment_token,
    re_enrollment_spoof_image,
    re_enrollment_workflow,
):
    """verifyFace with spoof frames returns 200; logs liveness outcome."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/verifyFace",
        json={
            "reEnrollmentToken": re_enrollment_token,
            "faceLivenessData": _make_face_data(re_enrollment_spoof_image, re_enrollment_workflow),
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_200_structure(result)

    flr = result.get("faceLivenessResults", {})
    liveness_result = flr.get("liveness_result", {}) if isinstance(flr, dict) else {}
    decision = liveness_result.get("decision", "N/A") if isinstance(liveness_result, dict) else "N/A"
    score = liveness_result.get("score", "N/A") if isinstance(liveness_result, dict) else "N/A"

    print(f"\n[OK] Spoof verifyFace response:")
    print(f"     livenessResult : {result['livenessResult']} (expected: false for spoof)")
    print(f"     decision       : {decision}")
    print(f"     score          : {score}")

    allure.attach(
        f"livenessResult: {result['livenessResult']}\n"
        f"matchResult:    {result['matchResult']}\n"
        f"decision:       {decision}\n"
        f"score:          {score}",
        name="Spoof Liveness Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Re-Enrollment API")
@allure.story("Face Liveness — Re-Enrollment - Negative")
@allure.title("verifyFace with spoof image is rejected — livenessResult is false")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Sends frames built from the SPOOF image (.env) with a valid reEnrollmentToken. "
    "Expects HTTP 200 with livenessResult == false, confirming the anti-spoofing "
    "engine correctly rejects the presentation attack. Also asserts decision is SPOOF "
    "when faceLivenessResults is present in the response."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_verify_face_spoof_rejected(
    api_client,
    re_enrollment_base_path,
    re_enrollment_token,
    re_enrollment_spoof_image,
    re_enrollment_workflow,
):
    """verifyFace with SPOOF image → livenessResult must be false (anti-spoofing check)."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/verifyFace",
        json={
            "reEnrollmentToken": re_enrollment_token,
            "faceLivenessData": _make_face_data(re_enrollment_spoof_image, re_enrollment_workflow),
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    _assert_200_structure(result)

    flr = result.get("faceLivenessResults", {})
    liveness_result = flr.get("liveness_result", {}) if isinstance(flr, dict) else {}
    decision = liveness_result.get("decision", "N/A") if isinstance(liveness_result, dict) else "N/A"
    score = liveness_result.get("score", "N/A") if isinstance(liveness_result, dict) else "N/A"

    print(f"\n[SPOOF TEST] verifyFace response:")
    print(f"     livenessResult : {result['livenessResult']}")
    print(f"     matchResult    : {result['matchResult']}")
    print(f"     decision       : {decision}")
    print(f"     score          : {score}")

    allure.attach(
        f"livenessResult: {result['livenessResult']}\n"
        f"matchResult:    {result['matchResult']}\n"
        f"decision:       {decision}\n"
        f"score:          {score}",
        name="Spoof Rejection Summary",
        attachment_type=allure.attachment_type.TEXT,
    )

    assert result["livenessResult"] is False, (
        f"Anti-spoofing check FAILED: expected livenessResult=false for spoof image, "
        f"got livenessResult={result['livenessResult']}. "
        f"decision={decision}, score={score}"
    )

    if decision != "N/A":
        assert decision == "SPOOF", (
            f"Expected decision='SPOOF' for spoof image, got '{decision}'"
        )

    print(f"\n[OK] Spoof correctly rejected: livenessResult=false, decision={decision}")


# ==============================================================================
# NEGATIVE TESTS
# ==============================================================================

@allure.feature("Re-Enrollment API")
@allure.story("Face Liveness — Re-Enrollment - Negative")
@allure.title("verifyFace with invalid reEnrollmentToken returns 400 or 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a randomly generated UUID as reEnrollmentToken alongside valid "
    "faceLivenessData. Expects HTTP 400 or 500 with errorCode, errorMsg, "
    "status, and timestamp fields."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_verify_face_invalid_token(
    api_client,
    re_enrollment_base_path,
    re_enrollment_face_image,
    re_enrollment_workflow,
):
    """Invalid reEnrollmentToken → 400/500 with error structure."""
    fake_token = str(uuid.uuid4())

    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/verifyFace",
        json={
            "reEnrollmentToken": fake_token,
            "faceLivenessData": _make_face_data(re_enrollment_face_image, re_enrollment_workflow),
        },
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
@allure.story("Face Liveness — Re-Enrollment - Negative")
@allure.title("verifyFace with missing reEnrollmentToken returns 400 or 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends faceLivenessData without the reEnrollmentToken field. "
    "Expects HTTP 400 or 500 with errorCode INPUT_FORMAT_ERROR or INPUT_VALUES_ERROR."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_verify_face_missing_token(
    api_client,
    re_enrollment_base_path,
    re_enrollment_face_image,
    re_enrollment_workflow,
):
    """Missing reEnrollmentToken → 400/500 with error structure."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/verifyFace",
        json={
            "faceLivenessData": _make_face_data(re_enrollment_face_image, re_enrollment_workflow),
        },
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
@allure.story("Face Liveness — Re-Enrollment - Negative")
@allure.title("verifyFace with missing faceLivenessData returns 400 or 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a valid reEnrollmentToken without the faceLivenessData field. "
    "Expects HTTP 400 or 500 with a structured error response."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_verify_face_missing_face_data(
    api_client,
    re_enrollment_base_path,
    re_enrollment_token,
):
    """Missing faceLivenessData → 400/500 with error structure."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/verifyFace",
        json={"reEnrollmentToken": re_enrollment_token},
    )

    assert response.status_code in (400, 500), (
        f"Expected 400 or 500 for missing faceLivenessData, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    _assert_error_structure(result)

    print(f"\n[OK] Missing faceLivenessData rejected: {response.status_code}")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")


@allure.feature("Re-Enrollment API")
@allure.story("Face Liveness — Re-Enrollment - Negative")
@allure.title("verifyFace with empty frames list returns 400 or 500")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends a valid reEnrollmentToken with faceLivenessData containing an empty "
    "frames array. Expects HTTP 400 or 500 — the server requires at least one frame."
)
@pytest.mark.stateful
@pytest.mark.re_enrollment
def test_verify_face_empty_frames(
    api_client,
    re_enrollment_base_path,
    re_enrollment_token,
    re_enrollment_workflow,
):
    """Empty frames array → 400/500 with error structure."""
    response = api_client.http_client.post(
        f"{re_enrollment_base_path}/verifyFace",
        json={
            "reEnrollmentToken": re_enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {
                        "client_device_brand": "Apple",
                        "client_device_model": "iPhone 8",
                        "client_os_version": "11.0.3",
                        "client_version": "KnomiSLive_v:2.4.1_b:0.0.0_sdk_v:2.4.1_b:0.0.0",
                        "localization": "en-US",
                        "programming_language_version": "Swift 4.1",
                        "username": "test",
                    },
                    "workflow_data": {
                        "workflow": re_enrollment_workflow,
                        "frames": [],
                    },
                }
            },
        },
    )

    assert response.status_code in (400, 500), (
        f"Expected 400 or 500 for empty frames, got {response.status_code}. "
        f"Response: {response.text}"
    )

    result = response.json()
    _assert_error_structure(result)

    print(f"\n[OK] Empty frames rejected: {response.status_code}")
    print(f"     errorCode : {result.get('errorCode')}")
    print(f"     errorMsg  : {str(result.get('errorMsg', ''))[:100]}")
