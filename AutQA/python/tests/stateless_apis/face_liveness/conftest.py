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
