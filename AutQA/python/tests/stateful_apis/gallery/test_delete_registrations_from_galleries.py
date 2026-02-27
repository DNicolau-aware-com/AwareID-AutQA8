"""
Tests for POST /onboarding/gallery/deleteRegistrationsFromGalleries

Bulk removes one or more registered users from one or more galleries in a single request.

Prerequisites (run once to populate .env):
    1. pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_all_fields -v
       (Run at least twice so GALLERY_REGISTRATION_CODES has >= 2 entries)
    2. pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v
       (Populates GALLERY_NAMES with >= 2 galleries)
    3. pytest tests/stateful_apis/gallery/test_add_multiple_users_to_galleries.py -v
       (To ensure all users are in all galleries before bulk-deleting)
"""

import allure
import pytest


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("Bulk delete multiple users from multiple galleries")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Reads GALLERY_REGISTRATION_CODES and GALLERY_NAMES from .env and removes all stored users "
    "from all stored galleries in a single API call. "
    "Expects HTTP 200. Requires at least 2 registration codes and 2 galleries in .env."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_delete_registrations_from_galleries_bulk(
    api_client, gallery_base_path, registration_codes, gallery_names
):
    """Bulk delete: remove all stored users from all stored galleries."""
    response = api_client.http_client.post(
        f"{gallery_base_path}/deleteRegistrationsFromGalleries",
        json={
            "galleryNames": gallery_names,
            "registrationCodes": registration_codes,
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    print(f"\n[OK] Bulk delete: {len(registration_codes)} users removed from {len(gallery_names)} galleries")
    print(f"     Galleries ({len(gallery_names)}):")
    for name in gallery_names:
        print(f"       - {name}")
    print(f"     Registration codes ({len(registration_codes)}):")
    for code in registration_codes:
        print(f"       - {code}")
