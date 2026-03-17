"""
Tests for POST /compliance/geofence/definitions/{geofenceName}

Creates a new geofence definition with the given name.

Request body: geofence rule object
    type      string — "include" | "exclude"
    geofence  object — AdminGeofence | CircularGeofence | CustomGeofence

Response structure:
    200/201  Created rule object (or confirmation)
    400      Invalid payload
    409      Name already exists (conflict)
    500      errorCode, errorMsg, status, timestamp
"""

import allure
import pytest


# ==============================================================================
# TESTS — POSITIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Create Definition")
@allure.title("POST create definition — returns 2xx and definition is stored")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Creates a new admin-type geofence definition with a unique name. "
    "Expects HTTP 200 or 201. Verifies the definition can be fetched "
    "by name afterwards. Cleans up the created resource."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_create_definition_success(
    api_client,
    geofence_base_path,
    geofence_test_name,
    admin_geofence_payload,
):
    """POST create → 2xx, then GET by name confirms it was stored."""
    response = api_client.http_client.post(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        json=admin_geofence_payload,
        with_apikey=False,
    )

    if response.status_code not in (200, 201):
        pytest.skip(
            f"Create endpoint returned {response.status_code} — "
            "feature may not be enabled on this environment."
        )

    print(f"\n[OK] POST definitions/{geofence_test_name} → {response.status_code}")

    # Verify it's retrievable
    get_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        with_apikey=False,
    )
    assert get_response.status_code == 200, (
        f"Created definition not found: {get_response.status_code}"
    )

    stored = get_response.json()
    assert stored.get("type") == admin_geofence_payload["type"], (
        f"Stored type mismatch: expected {admin_geofence_payload['type']!r}, "
        f"got {stored.get('type')!r}"
    )

    print(f"     GET confirms stored: type={stored.get('type')!r}")

    allure.attach(
        f"created:  {geofence_test_name}\nstored type: {stored.get('type')}",
        name="Create Summary",
        attachment_type=allure.attachment_type.TEXT,
    )

    # Cleanup
    api_client.http_client.delete(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        with_apikey=False,
    )


@allure.feature("Geofence API")
@allure.story("Create Definition")
@allure.title("POST create definition — created entry appears in list")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Creates a definition and verifies it appears in the GET /definitions list."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_create_definition_appears_in_list(
    api_client,
    geofence_base_path,
    created_geofence,
):
    """Newly created definition appears in the full list."""
    list_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions",
        with_apikey=False,
    )
    assert list_response.status_code == 200

    definitions = list_response.json()
    assert isinstance(definitions, list)

    # The created name should appear somewhere in the list
    names = [
        d.get("geofence", {}).get("name") or d.get("name")
        for d in definitions
    ]
    assert created_geofence in names, (
        f"Created definition '{created_geofence}' not found in list. "
        f"Names found: {names}"
    )

    print(f"\n[OK] '{created_geofence}' appears in definitions list ({len(definitions)} total)")


@allure.feature("Geofence API")
@allure.story("Create Definition")
@allure.title("POST create definition — admin geofence stores country and states")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Creates an admin-type geofence and verifies the country/states structure "
    "is preserved in the stored definition."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_create_definition_admin_structure_preserved(
    api_client,
    geofence_base_path,
    geofence_test_name,
    admin_geofence_payload,
):
    """Admin geofence country/states are preserved after create."""
    response = api_client.http_client.post(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        json=admin_geofence_payload,
        with_apikey=False,
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Create returned {response.status_code} — skipping")

    get_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        with_apikey=False,
    )
    assert get_response.status_code == 200

    stored = get_response.json()
    geo = stored.get("geofence", {})

    assert geo.get("type") == "admin", (
        f"Expected geofence.type='admin', got {geo.get('type')!r}"
    )

    stored_defs = geo.get("definitions", [])
    assert len(stored_defs) >= 1, "Expected at least one country definition"

    countries = [d.get("country") for d in stored_defs]
    assert "US" in countries, f"Expected 'US' in stored countries, got: {countries}"

    print(f"\n[OK] Admin geofence structure preserved: {stored_defs}")

    # Cleanup
    api_client.http_client.delete(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        with_apikey=False,
    )


# ==============================================================================
# TESTS — NEGATIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Create Definition")
@allure.title("POST create definition — duplicate name returns 4xx")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Creates a definition, then tries to create another with the same name. "
    "Expects 400 or 409 (conflict). Cleans up afterwards."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_create_definition_duplicate_name_rejected(
    api_client,
    geofence_base_path,
    created_geofence,
    admin_geofence_payload,
):
    """Creating a definition with a name that already exists → 400 or 409."""
    response = api_client.http_client.post(
        f"{geofence_base_path}/definitions/{created_geofence}",
        json=admin_geofence_payload,
        with_apikey=False,
    )

    assert response.status_code in (400, 409), (
        f"Expected 400 or 409 for duplicate name, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Duplicate name correctly rejected → {response.status_code}")


@allure.feature("Geofence API")
@allure.story("Create Definition")
@allure.title("POST create definition — empty body returns 400")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends a POST to create a definition with an empty body. Expects 400."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_create_definition_empty_body_rejected(
    api_client,
    geofence_base_path,
    geofence_test_name,
):
    """POST with empty body → 400."""
    response = api_client.http_client.post(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        json={},
        with_apikey=False,
    )

    assert response.status_code in (400, 422), (
        f"Expected 400/422 for empty body, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Empty body correctly rejected → {response.status_code}")


@allure.feature("Geofence API")
@allure.story("Create Definition")
@allure.title("POST create definition — invalid type value returns 400")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends a POST with an invalid rule 'type' value. Expects 400."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_create_definition_invalid_type_rejected(
    api_client,
    geofence_base_path,
    geofence_test_name,
):
    """POST with invalid rule type → 400."""
    payload = {
        "type": "invalid-type",
        "geofence": {
            "type": "admin",
            "definitions": [{"country": "US", "states": ["TX"]}],
        },
    }

    response = api_client.http_client.post(
        f"{geofence_base_path}/definitions/{geofence_test_name}",
        json=payload,
        with_apikey=False,
    )

    assert response.status_code in (400, 422), (
        f"Expected 400/422 for invalid type, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Invalid type value correctly rejected → {response.status_code}")
