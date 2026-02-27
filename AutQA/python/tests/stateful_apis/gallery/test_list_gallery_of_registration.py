"""
Tests for POST /onboarding/gallery/listGalleryOfRegistration

Returns the list of galleries a registered user has been enrolled to.

Prerequisites (run once to populate .env):
    1. pytest tests/stateful_apis/gallery/test_register_user.py::test_register_multiple_users -v
       (Populates GALLERY_REGISTRATION_CODES)
    2. pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v
       (Populates GALLERY_NAMES — custom galleries only)
    3. pytest tests/stateful_apis/gallery/test_add_registrations_to_galleries.py -v
       (Ensures the users are already enrolled in the galleries)
"""

import allure
import pytest


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("listGalleryOfRegistration returns galleries the user belongs to")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Reads the first registration code from GALLERY_REGISTRATION_CODES and the first "
    "gallery from GALLERY_NAMES in .env. Calls listGalleryOfRegistration and asserts "
    "that the expected gallery appears in the response list. "
    "Expects HTTP 200 and a 'list' array containing the known gallery."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_list_gallery_of_registration(api_client, gallery_base_path, env_store):
    """listGalleryOfRegistration includes the gallery the user was enrolled in (from .env)."""
    raw_codes = env_store.get("GALLERY_REGISTRATION_CODES")
    if not raw_codes:
        pytest.skip(
            "GALLERY_REGISTRATION_CODES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_register_user.py"
            "::test_register_multiple_users -v"
        )
    raw_galleries = env_store.get("GALLERY_NAMES")
    if not raw_galleries:
        pytest.skip(
            "GALLERY_NAMES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v"
        )

    reg_code = [c.strip() for c in raw_codes.split(",") if c.strip()][0]
    expected_gallery = [g.strip() for g in raw_galleries.split(",") if g.strip()][0]

    print(f"\n[INFO] Listing galleries for {reg_code}, expecting '{expected_gallery}'")

    response = api_client.http_client.post(
        f"{gallery_base_path}/listGalleryOfRegistration",
        json={"registrationCode": reg_code},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "list" in result, f"Expected 'list' in response, got: {result}"
    assert expected_gallery in result["list"], (
        f"Expected '{expected_gallery}' in gallery list: {result['list']}"
    )

    print(f"\n[OK] User {reg_code} is in galleries: {result['list']}")
