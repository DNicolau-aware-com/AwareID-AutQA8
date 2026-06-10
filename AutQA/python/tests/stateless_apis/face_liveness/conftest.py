"""
Shared fixtures for Face Liveness tests.
"""

import pytest
import json


@pytest.fixture
def face_liveness_base_path():
    """Base path for face liveness endpoints."""
    return "/faceliveness"


@pytest.fixture
def b2c_sdk_base_path():
    """Base path for B2C SDK endpoints."""
    return "/b2c/sdk"


@pytest.fixture
def b2c_session_id(api_client):
    """
    Obtain a fresh server-issued session ID from GET /b2c/sdk/session-id.

    Skips the test if the endpoint returns 404 (feature not deployed on this server).
    Returns the session-id UUID string.
    """
    response = api_client.http_client.get("/b2c/sdk/getSessionId", retry=False)
    if response.status_code == 404:
        pytest.skip(
            "GET /b2c/sdk/getSessionId returned 404 — Session ID feature not deployed "
            "on this server. Set BASEURL to an environment where the feature is active."
        )
    if response.status_code != 200:
        pytest.fail(
            f"GET /b2c/sdk/getSessionId returned {response.status_code} "
            f"— endpoint is deployed but returned an error. Response: {response.text[:300]}"
        )
    data = response.json()
    session_id = data.get("session_id")
    if not session_id:
        pytest.skip(
            f"No 'session-id' key in response from /b2c/sdk/getSessionId. Got: {data}"
        )
    return session_id


@pytest.fixture
def face_image_base64(env_store):
    """Get face image from .env file."""
    face_b64 = env_store.get("TX_DL_FACE_B64")
    if not face_b64:
        pytest.skip("TX_DL_FACE_B64 not found in .env file")
    return face_b64


@pytest.fixture
def face_liveness_data(env_store):
    """
    Get face liveness encrypted data from .env file.
    
    FACELIVENESSDATA should be a JSON object with:
    {
      "key": "string",
      "iv": any,
      "p": any
    }
    """
    data_str = env_store.get("FACELIVENESSDATA")
    if not data_str:
        pytest.skip("FACELIVENESSDATA not found in .env file")
    
    try:
        data = json.loads(data_str)
        assert "key" in data, "FACELIVENESSDATA must contain 'key'"
        assert "iv" in data, "FACELIVENESSDATA must contain 'iv'"
        assert "p" in data, "FACELIVENESSDATA must contain 'p'"
        return data
    except json.JSONDecodeError as e:
        pytest.skip(f"FACELIVENESSDATA is not valid JSON: {e}")
    except AssertionError as e:
        pytest.skip(str(e))
