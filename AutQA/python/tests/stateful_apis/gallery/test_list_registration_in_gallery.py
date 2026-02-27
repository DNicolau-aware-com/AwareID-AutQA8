"""
Tests for POST /onboarding/gallery/listRegistrationInGallery

Lists users enrolled in a gallery, sorted by registrationCode. Supports pagination
via pageNumber and pageSize parameters.

Prerequisites (run once to populate .env):
    1. pytest tests/stateful_apis/gallery/test_register_user.py::test_register_multiple_users -v
       (Populates GALLERY_REGISTRATION_CODES)
    2. pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v
       (Populates GALLERY_NAMES — custom galleries only)
    3. pytest tests/stateful_apis/gallery/test_add_registrations_to_galleries.py -v
       (Ensures users are already enrolled in the galleries)
"""

import allure
import pytest


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("listRegistrationInGallery returns paginated users in a gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Reads the first registration code from GALLERY_REGISTRATION_CODES and the first "
    "gallery from GALLERY_NAMES in .env. Lists all registrations in that gallery and "
    "verifies the known user is present. "
    "Expects HTTP 200 with pagination fields (pageNumber, pageSize, totalRecords, totalPages, list)."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_list_registration_in_gallery(api_client, gallery_base_path, env_store):
    """listRegistrationInGallery returns pagination info and includes the known enrolled user."""
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

    print(f"\n[INFO] Listing registrations in '{gallery_name}', expecting {reg_code}")

    response = api_client.http_client.post(
        f"{gallery_base_path}/listRegistrationInGallery",
        json={"galleryName": gallery_name},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "pageNumber" in result, f"Expected 'pageNumber' in response, got: {result}"
    assert "pageSize" in result, f"Expected 'pageSize' in response, got: {result}"
    assert "totalRecords" in result, f"Expected 'totalRecords' in response, got: {result}"
    assert "totalPages" in result, f"Expected 'totalPages' in response, got: {result}"
    assert "list" in result, f"Expected 'list' in response, got: {result}"

    found = any(u.get("registrationCode") == reg_code for u in result["list"])
    assert found, f"Registered user {reg_code} not found in gallery listing for '{gallery_name}'"

    print(f"\n[OK] listRegistrationInGallery: {result['totalRecords']} total, page {result['pageNumber']}")


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("listRegistrationInGallery respects pageSize parameter")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Reads the first gallery from GALLERY_NAMES in .env and calls listRegistrationInGallery "
    "with pageSize=1. Expects the returned list to contain at most 1 entry."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_list_registration_in_gallery_paged(api_client, gallery_base_path, env_store):
    """Pagination: pageSize=1 returns at most 1 entry."""
    raw_galleries = env_store.get("GALLERY_NAMES")
    if not raw_galleries:
        pytest.skip(
            "GALLERY_NAMES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v"
        )

    gallery_name = [g.strip() for g in raw_galleries.split(",") if g.strip()][0]

    print(f"\n[INFO] Paged listing (pageSize=1) in '{gallery_name}'")

    response = api_client.http_client.post(
        f"{gallery_base_path}/listRegistrationInGallery",
        json={"galleryName": gallery_name, "pageNumber": 1, "pageSize": 1},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert len(result.get("list", [])) <= 1, (
        f"Expected at most 1 record with pageSize=1, got {len(result.get('list', []))}"
    )

    print(f"\n[OK] Paged list: {len(result['list'])} record(s) with pageSize=1")
