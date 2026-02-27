"""
Tests for POST /onboarding/gallery/isRegistrationInGallery

Checks whether a registered user is currently enrolled in a given gallery.
Returns { "exist": true/false }.

Prerequisites (run once to populate .env):
    1. pytest tests/stateful_apis/gallery/test_register_user.py::test_register_multiple_users -v
       (Populates GALLERY_REGISTRATION_CODES)
    2. pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v
       (Populates GALLERY_NAMES — custom galleries only)
    3. pytest tests/stateful_apis/gallery/test_add_registrations_to_galleries.py -v
       (Ensures the users are already in the galleries before the exist=true check)
"""

import uuid
import allure
import pytest


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("isRegistrationInGallery returns true for enrolled user")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Reads the first registration code from GALLERY_REGISTRATION_CODES and the first "
    "gallery from GALLERY_NAMES in .env. Checks that the user is enrolled. "
    "Expects HTTP 200 and exist == true. "
    "Requires test_add_registrations_to_galleries to have been run first."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_is_registration_in_gallery_true(api_client, gallery_base_path, env_store):
    """isRegistrationInGallery returns exist=true for a user already enrolled (from .env)."""
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
    gallery_name = [g.strip() for g in raw_galleries.split(",") if g.strip()][0]

    print(f"\n[INFO] Checking enrollment: {reg_code} in '{gallery_name}'")

    response = api_client.http_client.post(
        f"{gallery_base_path}/isRegistrationInGallery",
        json={"galleryName": gallery_name, "registrationCode": reg_code},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    assert response.json().get("exist") is True, (
        f"Expected exist=true, got: {response.json()}"
    )

    print(f"\n[OK] isRegistrationInGallery=true for {reg_code} in '{gallery_name}'")


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("isRegistrationInGallery returns false for user not in gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Reads the first registration code from GALLERY_REGISTRATION_CODES in .env. "
    "Creates a fresh empty gallery and checks the user is not enrolled in it. "
    "Expects HTTP 200 and exist == false. The temporary gallery is deleted after the test."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_is_registration_in_gallery_false(api_client, gallery_base_path, env_store):
    """isRegistrationInGallery returns exist=false for a user not in a brand-new gallery."""
    raw_codes = env_store.get("GALLERY_REGISTRATION_CODES")
    if not raw_codes:
        pytest.skip(
            "GALLERY_REGISTRATION_CODES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_register_user.py"
            "::test_register_multiple_users -v"
        )

    reg_code = [c.strip() for c in raw_codes.split(",") if c.strip()][0]
    fresh_gallery = f"test_gallery_{uuid.uuid4().hex[:8]}"

    # Create a brand-new empty gallery — the user was never added to it
    create_resp = api_client.http_client.post(
        f"{gallery_base_path}/addGallery",
        json={"galleryName": fresh_gallery},
    )
    if create_resp.status_code != 200:
        pytest.skip(
            f"Could not create temporary gallery '{fresh_gallery}' "
            f"({create_resp.status_code}): {create_resp.text[:200]}"
        )

    print(f"\n[INFO] Checking enrollment: {reg_code} in fresh gallery '{fresh_gallery}'")

    try:
        response = api_client.http_client.post(
            f"{gallery_base_path}/isRegistrationInGallery",
            json={"galleryName": fresh_gallery, "registrationCode": reg_code},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        assert response.json().get("exist") is False, (
            f"Expected exist=false, got: {response.json()}"
        )

        print(f"\n[OK] isRegistrationInGallery=false for {reg_code} in '{fresh_gallery}'")
    finally:
        # Clean up the temporary gallery we created for this test
        api_client.http_client.post(
            f"{gallery_base_path}/deleteGallery",
            json={"galleryName": fresh_gallery},
        )
        print(f"[CLEANUP] Temporary gallery '{fresh_gallery}' deleted")
