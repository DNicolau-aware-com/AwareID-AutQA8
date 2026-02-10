import pytest
import uuid
import time
from pathlib import Path
from dotenv import dotenv_values

ENROLLMENT_SETTINGS = {
    "add_face": True,
    "add_document": False,
    "add_voice": False,
    "add_pin": False,
    "check_device_security": False,
    "add_device": False,
    "enable_age_estimation": False,
    "prevent_duplicate_enrollments": True,
    "duplicate_face_match_threshold": 80,
    "rfid_portrait_selfie_threshold": 3,
    "ocr_portrait_selfie_threshold": 2.0,
    "document_rfid": "DISABLED",
    "max_device_ids": 3,
}

@pytest.fixture(scope="session")
def enrollment_settings():
    return ENROLLMENT_SETTINGS

@pytest.fixture(scope="session")
def env_vars():
    root = Path(__file__).resolve().parents[2]
    return dotenv_values(root / ".env")

@pytest.fixture
def unique_username():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    return f"dantest_{timestamp}_{unique_id}"[:50]

@pytest.fixture
def face_image(env_vars):
    image = (
        env_vars.get("FACE") or
        env_vars.get("DAN_FACE") or
        env_vars.get("FACE_IMAGE")
    )
    if not image:
        pytest.skip("Face image not found in .env (set FACE=<base64>)")
    if image.startswith("data:image"):
        image = image.split(",")[1]
    return image.strip()

@pytest.fixture
def face_frames(face_image):
    now_ms = int(time.time() * 1000)
    return [
        {"data": face_image, "timestamp": now_ms + (i * 30), "tags": []}
        for i in range(3)
    ]

@pytest.fixture
def workflow(env_vars):
    return env_vars.get("WORKFLOW", "charlie4")

@pytest.fixture
def enrolled_username(env_vars):
    return env_vars.get('userEnroll', 'TESTETSTETS')
