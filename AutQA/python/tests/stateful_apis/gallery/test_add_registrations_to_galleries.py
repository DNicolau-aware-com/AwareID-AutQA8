"""
Tests for POST /onboarding/gallery/addRegistrationsToGalleries

Bulk adds one or more registered users to one or more galleries in a single request.

Prerequisites (run once to populate .env):
    1. pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_all_fields -v
    2. pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v
"""

import allure
import pytest


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("Bulk add a registered user to all galleries in the system")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Uses addRegistrationsToGalleries to add a user to all galleries returned by "
    "listGallery (stored in .env as GALLERY_NAMES). Expects HTTP 200. "
    "Requires at least 2 galleries to validate the bulk behaviour."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_add_registrations_to_galleries_bulk(api_client, gallery_base_path, registered_user, gallery_names):
    """Bulk add: one user to all galleries from .env (GALLERY_NAMES)."""
    reg_code = registered_user["registrationCode"]

    response = api_client.http_client.post(
        f"{gallery_base_path}/addRegistrationsToGalleries",
        json={
            "galleryNames": gallery_names,
            "registrationCodes": [reg_code],
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    print(f"\n[OK] Bulk add: user {reg_code} added to {len(gallery_names)} galleries:")
    for name in gallery_names:
        print(f"     - {name}")
