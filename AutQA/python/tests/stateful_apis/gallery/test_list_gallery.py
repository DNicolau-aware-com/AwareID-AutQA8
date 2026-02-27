"""
Tests for GET /onboarding/gallery/listGallery

Lists all galleries configured in the system (default + any custom galleries).
"""

import allure
import pytest


@allure.feature("Gallery API")
@allure.story("Gallery Management")
@allure.title("List galleries returns a list with at least the default system gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Calls GET /onboarding/gallery/listGallery. "
    "Expects HTTP 200 and a 'list' array. The default system gallery should always be present."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_list_gallery(api_client, gallery_base_path, env_store):
    """listGallery returns HTTP 200 and a non-empty list. Saves all gallery names to .env."""
    response = api_client.http_client.get(f"{gallery_base_path}/listGallery")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "list" in result, f"Expected 'list' in response, got: {result}"
    assert isinstance(result["list"], list), "'list' should be an array"

    all_names = [g.get("galleryName", g) for g in result["list"]]
    print(f"\n[OK] Galleries found ({len(all_names)}): {all_names}")

    # Save only custom galleries to .env — exclude the default system gallery
    # which does not support deleteRegistrationFromGallery / deleteGallery.
    custom_names = [n for n in all_names if n != "(default)"]
    if custom_names:
        trimmed = custom_names[-10:]
        env_store.set("GALLERY_NAMES", ",".join(trimmed))
        print(f"\n[SAVED] GALLERY_NAMES={','.join(trimmed)}  ({len(trimmed)}/10)")

    allure.attach(
        "\n".join(all_names),
        name=f"Available Galleries ({len(all_names)})",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Gallery API")
@allure.story("Gallery Management")
@allure.title("New custom gallery appears in listGallery after creation")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Creates a custom gallery and verifies it appears in the listGallery response. "
    "Gallery is deleted in teardown via the custom_gallery fixture."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_list_gallery_includes_custom_gallery(api_client, gallery_base_path, custom_gallery):
    """Custom gallery appears in the list after creation."""
    response = api_client.http_client.get(f"{gallery_base_path}/listGallery")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    gallery_names = [g.get("galleryName", g) for g in result.get("list", [])]

    assert custom_gallery in gallery_names, (
        f"Expected '{custom_gallery}' in gallery list, got: {gallery_names}"
    )

    print(f"\n[OK] Custom gallery '{custom_gallery}' found in list")
