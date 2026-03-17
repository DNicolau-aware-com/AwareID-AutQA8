"""
Tests for DELETE /compliance/geofence/definitions/{geofenceName}

Deletes a geofence definition by name.

Response structure:
    200/204  Successful deletion
    404      Definition not found
    500      errorCode, errorMsg, status, timestamp
"""

import allure
import pytest


# ==============================================================================
# TESTS — POSITIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Delete Definition")
@allure.title("DELETE definition — returns 200/204 and is no longer retrievable")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Creates a definition then deletes it. Expects 200 or 204. "
    "Verifies a subsequent GET returns 404."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_delete_definition_success(
    api_client,
    geofence_base_path,
    geofence_test_name,
    admin_geofence_payload,
):
    """DELETE → 200/204, then GET confirms 404."""
    # Create
    create_response = api_client.http_client.post(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        json=admin_geofence_payload,
        with_apikey=False,
    )
    if create_response.status_code not in (200, 201):
        pytest.skip(
            f"Cannot create test geofence ({create_response.status_code}) — "
            "endpoint may not be available"
        )

    # Delete
    delete_response = api_client.http_client.delete(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        with_apikey=False,
    )

    assert delete_response.status_code in (200, 204), (
        f"Expected 200/204, got {delete_response.status_code}. "
        f"Response: {delete_response.text}"
    )

    print(f"\n[OK] DELETE definitions/{geofence_test_name} → {delete_response.status_code}")

    # Verify it is gone
    get_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        with_apikey=False,
    )

    assert get_response.status_code == 404, (
        f"Expected 404 after deletion, got {get_response.status_code}"
    )

    print(f"     GET after DELETE → 404 (confirmed)")

    allure.attach(
        f"deleted: {geofence_test_name}\ndelete status: {delete_response.status_code}\nverify GET: 404",
        name="Delete Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Geofence API")
@allure.story("Delete Definition")
@allure.title("DELETE definition — deleted entry no longer appears in list")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Deletes a definition and verifies it no longer appears in GET /definitions."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_delete_definition_removed_from_list(
    api_client,
    geofence_base_path,
    geofence_test_name,
    admin_geofence_payload,
):
    """Deleted definition no longer appears in the full list."""
    # Create
    create_response = api_client.http_client.post(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        json=admin_geofence_payload,
        with_apikey=False,
    )
    if create_response.status_code not in (200, 201):
        pytest.skip(f"Cannot create test geofence ({create_response.status_code})")

    # Delete
    delete_response = api_client.http_client.delete(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        with_apikey=False,
    )
    assert delete_response.status_code in (200, 204)

    # Check list
    list_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions",
        with_apikey=False,
    )
    assert list_response.status_code == 200

    definitions = list_response.json()
    names = [
        d.get("geofence", {}).get("name") or d.get("name")
        for d in definitions
    ]

    assert geofence_test_name not in names, (
        f"Deleted geofence '{geofence_test_name}' still appears in list: {names}"
    )

    print(f"\n[OK] '{geofence_test_name}' no longer in list after deletion")


# ==============================================================================
# TESTS — NEGATIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Delete Definition")
@allure.title("DELETE definition — non-existent name returns 404")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Calls DELETE with a name that does not exist. Expects 404."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_delete_definition_unknown_name_returns_404(
    api_client,
    geofence_base_path,
):
    """DELETE on a non-existent name → 404."""
    response = api_client.http_client.delete(
        f"{geofence_base_path}/definitions/this-does-not-exist-xyz",
        with_apikey=False,
    )

    assert response.status_code == 404, (
        f"Expected 404 for unknown name, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Unknown name → 404")


@allure.feature("Geofence API")
@allure.story("Delete Definition")
@allure.title("DELETE definition — double-delete returns 404 on second attempt")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Deletes a definition twice. The first call should succeed (200/204), "
    "the second should return 404."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_delete_definition_double_delete(
    api_client,
    geofence_base_path,
    geofence_test_name,
    admin_geofence_payload,
):
    """DELETE twice → first succeeds (200/204), second returns 404."""
    # Create
    create_response = api_client.http_client.post(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        json=admin_geofence_payload,
        with_apikey=False,
    )
    if create_response.status_code not in (200, 201):
        pytest.skip(f"Cannot create test geofence ({create_response.status_code})")

    # First delete — should succeed
    first_delete = api_client.http_client.delete(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        with_apikey=False,
    )
    assert first_delete.status_code in (200, 204), (
        f"First delete: expected 200/204, got {first_delete.status_code}"
    )
    print(f"\n[OK] First DELETE → {first_delete.status_code}")

    # Second delete — should fail
    second_delete = api_client.http_client.delete(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        with_apikey=False,
    )
    assert second_delete.status_code == 404, (
        f"Second delete: expected 404, got {second_delete.status_code}"
    )
    print(f"[OK] Second DELETE → 404 (correctly rejected)")
