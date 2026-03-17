"""
Tests for GET /compliance/geofence/definitions/{geofenceName}

Returns a single geofence rule by name.

Response structure:
    200  Single geofence rule object:
             type      string — "include" | "exclude"
             geofence  object — AdminGeofence | CircularGeofence | CustomGeofence

    404  Definition not found (name does not exist)
    500  errorCode, errorMsg, status, timestamp
"""

import allure
import pytest


# ==============================================================================
# TESTS — POSITIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Get Definition By Name")
@allure.title("GET definition by name — returns 200 with rule object")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Fetches all definitions first, picks the first name, then calls "
    "GET /compliance/geofence/definitions/{name}. Expects 200 with a "
    "'type' and 'geofence' field matching what the list endpoint returned. "
    "Skips if no definitions are configured."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_get_definition_by_name_returns_200(api_client, geofence_base_path):
    """GET by name → 200 with a rule object."""
    # Get the list first so we have a real name to query
    list_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions",
        with_apikey=False,
    )
    assert list_response.status_code == 200, (
        f"Prerequisite list call failed: {list_response.status_code}"
    )

    definitions = list_response.json()
    if not isinstance(definitions, list) or not definitions:
        pytest.skip("No geofence definitions configured — cannot test GET by name")

    # Extract the name of the first definition
    first = definitions[0]
    geo_name = first.get("geofence", {}).get("name") or first.get("name")
    if not geo_name:
        pytest.skip(
            "First definition has no 'name' field — "
            f"available keys: {list(first.keys())}"
        )

    response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/{geo_name}",
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert isinstance(result, dict), (
        f"Expected an object, got: {type(result).__name__}"
    )
    assert "type" in result, f"Missing 'type' field. Keys: {list(result.keys())}"
    assert "geofence" in result, f"Missing 'geofence' field. Keys: {list(result.keys())}"

    print(f"\n[OK] GET definitions/{geo_name} → 200")
    print(f"     type    : {result['type']!r}")
    print(f"     geofence: {result['geofence']}")

    allure.attach(
        f"name:    {geo_name}\ntype:    {result['type']}\ngeofence: {result['geofence']}",
        name="Definition Detail",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Geofence API")
@allure.story("Get Definition By Name")
@allure.title("GET definition by name — response matches list endpoint entry")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Fetches a definition by name and verifies the returned object is consistent "
    "with what the list endpoint returned for the same entry."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_get_definition_by_name_matches_list(api_client, geofence_base_path):
    """GET by name returns the same rule that appears in the list."""
    list_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions",
        with_apikey=False,
    )
    assert list_response.status_code == 200

    definitions = list_response.json()
    if not isinstance(definitions, list) or not definitions:
        pytest.skip("No geofence definitions configured")

    first = definitions[0]
    geo_name = first.get("geofence", {}).get("name") or first.get("name")
    if not geo_name:
        pytest.skip("First definition has no 'name' field")

    single_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/{geo_name}",
        with_apikey=False,
    )
    assert single_response.status_code == 200

    single = single_response.json()

    # The rule type should match
    assert single.get("type") == first.get("type"), (
        f"type mismatch: list={first.get('type')!r} vs single={single.get('type')!r}"
    )

    # The geofence sub-type should match
    single_geo_type = single.get("geofence", {}).get("type")
    list_geo_type = first.get("geofence", {}).get("type")
    assert single_geo_type == list_geo_type, (
        f"geofence.type mismatch: list={list_geo_type!r} vs single={single_geo_type!r}"
    )

    print(f"\n[OK] GET by name is consistent with list endpoint")


# ==============================================================================
# TESTS — NEGATIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Get Definition By Name")
@allure.title("GET definition by name — unknown name returns 404")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Calls GET /compliance/geofence/definitions/{name} with a name that does "
    "not exist. Expects HTTP 404."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_get_definition_by_name_unknown_returns_404(api_client, geofence_base_path):
    """Non-existent geofence name → 404."""
    response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/this-name-does-not-exist-xyz123",
        with_apikey=False,
    )

    assert response.status_code == 404, (
        f"Expected 404 for unknown name, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Unknown geofence name → 404")


@allure.feature("Geofence API")
@allure.story("Get Definition By Name")
@allure.title("GET definition by name — created definition is retrievable by name")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Uses the created_geofence fixture to create a definition, then verifies "
    "it can be fetched by name. Skips if the create endpoint is unavailable."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_get_definition_by_name_after_create(
    api_client,
    geofence_base_path,
    created_geofence,
):
    """Newly created definition is retrievable by name."""
    response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/{created_geofence}",
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert isinstance(result, dict)
    assert "type" in result
    assert "geofence" in result

    print(f"\n[OK] Newly created definition '{created_geofence}' is retrievable")
    print(f"     type    : {result['type']!r}")
    print(f"     geofence: {result['geofence']}")
