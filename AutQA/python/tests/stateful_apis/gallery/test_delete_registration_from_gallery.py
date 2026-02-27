"""
Tests for POST /onboarding/gallery/deleteRegistrationFromGallery

Removes a registered user from a custom gallery.
Note: the user remains in the default system gallery; only the custom gallery membership is removed.

Prerequisites (run once to populate .env):
    1. pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_all_fields -v
       (Populates GALLERY_REGISTRATION_CODES)
    2. pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v
       (Populates GALLERY_NAMES)
    3. pytest tests/stateful_apis/gallery/test_add_registration_to_gallery.py -v
       (Ensures the user is already in the gallery before deleting)
"""

import allure
import pytest


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("Remove a registered user from a custom gallery")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Reads the first entry from GALLERY_REGISTRATION_CODES and GALLERY_NAMES in .env "
    "and removes that user from that gallery. "
    "Expects HTTP 200. Verifies absence via isRegistrationInGallery."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_delete_registration_from_gallery(api_client, gallery_base_path, env_store):
    """Remove one user (first from .env list) from one gallery (first from .env list)."""
    raw_codes = env_store.get("GALLERY_REGISTRATION_CODES")
    if not raw_codes:
        pytest.skip(
            "GALLERY_REGISTRATION_CODES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_register_user.py"
            "::test_register_user_all_fields -v"
        )
    raw_galleries = env_store.get("GALLERY_NAMES")
    if not raw_galleries:
        pytest.skip(
            "GALLERY_NAMES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v"
        )

    reg_code = [c.strip() for c in raw_codes.split(",") if c.strip()][0]
    gallery_name = [g.strip() for g in raw_galleries.split(",") if g.strip()][0]

    print(f"\n[INFO] Deleting user {reg_code} from gallery '{gallery_name}'")

    # Delete
    del_resp = api_client.http_client.post(
        f"{gallery_base_path}/deleteRegistrationFromGallery",
        json={"galleryName": gallery_name, "registrationCode": reg_code},
    )
    assert del_resp.status_code == 200, (
        f"Expected 200 for deleteRegistrationFromGallery, got {del_resp.status_code}. "
        f"Response: {del_resp.text}"
    )

    # Verify absence
    check = api_client.http_client.post(
        f"{gallery_base_path}/isRegistrationInGallery",
        json={"galleryName": gallery_name, "registrationCode": reg_code},
    )
    if check.status_code == 200:
        assert check.json().get("exist") is False, "User should NOT be present after deletion"

    print(f"\n[OK] User {reg_code} removed from '{gallery_name}'")
