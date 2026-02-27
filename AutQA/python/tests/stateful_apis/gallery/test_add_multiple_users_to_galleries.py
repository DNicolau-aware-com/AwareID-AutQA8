"""
Tests for POST /onboarding/gallery/addRegistrationsToGalleries — multi-user scenario

Bulk adds multiple registered users to multiple galleries in a single request.

Prerequisites (run once, or multiple times to accumulate data):
    1. pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_all_fields -v
       (Run at least twice so that GALLERY_REGISTRATION_CODES has >= 2 entries)
    2. pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v
       (Populates GALLERY_NAMES with all system galleries)
"""

import allure
import pytest


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("Bulk add multiple users to multiple galleries simultaneously")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Uses addRegistrationsToGalleries to add all accumulated users (GALLERY_REGISTRATION_CODES) "
    "to all galleries (GALLERY_NAMES) in a single API call. "
    "Expects HTTP 200. Requires at least 2 registration codes and 2 galleries in .env."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_add_multiple_users_to_multiple_galleries(
    api_client, gallery_base_path, registration_codes, gallery_names
):
    """Bulk add: all stored users to all stored galleries in one request."""
    response = api_client.http_client.post(
        f"{gallery_base_path}/addRegistrationsToGalleries",
        json={
            "galleryNames": gallery_names,
            "registrationCodes": registration_codes,
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    print(f"\n[OK] Bulk add: {len(registration_codes)} users → {len(gallery_names)} galleries")
    print(f"     Galleries ({len(gallery_names)}):")
    for name in gallery_names:
        print(f"       - {name}")
    print(f"     Registration codes ({len(registration_codes)}):")
    for code in registration_codes:
        print(f"       - {code}")
