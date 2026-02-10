"""
Shared fixtures for Knomi Web (B2C SDK) tests.
"""

import pytest
from dotenv import dotenv_values


@pytest.fixture
def preface_base_path():
    """Base path for Preface SDK endpoints."""
    return "/b2c/sdk/preface"


@pytest.fixture
def knomi_web_base_path():
    """Base path for Knomi Web B2C SDK endpoints."""
    return "/b2c/sdk"


@pytest.fixture
def preface_profile_xml():
    """Get Preface profile XML from .env file."""
    # Load fresh from .env every time (don't use cached env_store)
    env = dotenv_values()
    xml = env.get("PREFACE_PROFILE_XML") or env.get("XML_PROFILE")
    
    if not xml or len(xml) < 50:
        pytest.skip("PREFACE_PROFILE_XML not configured in .env (need valid XML profile)")
    
    return xml


@pytest.fixture
def face_image_base64():
    """Get base64 encoded face image from .env."""
    env = dotenv_values()
    image = env.get("FACE") or env.get("DAN_FACE") or env.get("FACE_IMAGE")
    
    if not image:
        pytest.skip("Face image (FACE) not found in .env")
    
    # Remove data URI prefix if present
    if image.startswith("data:image"):
        image = image.split(",")[1]
    
    return image


@pytest.fixture
def document_verification_base_path():
    """Base path for Document Verification endpoints."""
    return "/b2c/sdk/documentVerification"


@pytest.fixture
def document_front_image():
    """Get front document image from .env."""
    env = dotenv_values()
    image = env.get("DAN_DOC_FRONT") or env.get("OCR_FRONT") or env.get("DOCUMENT_FRONT")
    
    if not image:
        pytest.skip("Document front image not found in .env")
    
    # Remove data URI prefix if present
    if image.startswith("data:image"):
        image = image.split(",")[1]
    
    return image


@pytest.fixture
def document_back_image():
    """Get back document image from .env."""
    env = dotenv_values()
    image = env.get("DAN_DOC_BACK") or env.get("OCR_BACK") or env.get("DOCUMENT_BACK")
    
    if not image:
        return None  # Back is optional
    
    # Remove data URI prefix if present
    if image.startswith("data:image"):
        image = image.split(",")[1]
    
    return image
