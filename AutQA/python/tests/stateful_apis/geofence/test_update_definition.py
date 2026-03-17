"""
Tests for PUT /compliance/geofence/definitions/{geofenceName}

Updates an existing geofence definition.

Request body: geofence rule object (same schema as create)

Response structure:
    200  Updated rule object (or confirmation)
    400  Invalid payload
    404  Definition not found
    500  errorCode, errorMsg, status, timestamp
"""

import allure
import pytest


# ==============================================================================
# TESTS — POSITIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Update Definition")
@allure.title("PUT update definition — returns 200 and change is persisted")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Creates a definition, then PUTs an updated payload with a different state. "
    "Verifies the response is 200 and the GET endpoint reflects the change."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_update_definition_success(
    api_client,
    geofence_base_path,
    created_geofence,
):
    """PUT update → 200, then GET confirms new value is stored."""
    updated_payload = {
        "type": "include",
        "geofence": {
            "type": "admin",
            "definitions": [
                {"country": "US", "states": ["CA", "NY"]}
            ],
        },
    }

    response = api_client.http_client.put(
        f"{geofence_base_path}/definitions/{created_geofence}",
        json=updated_payload,
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    print(f"\n[OK] PUT definitions/{created_geofence} → 200")

    # Verify the change was persisted
    get_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/{created_geofence}",
        with_apikey=False,
    )
    assert get_response.status_code == 200

    stored = get_response.json()
    geo_defs = stored.get("geofence", {}).get("definitions", [])
    countries = [d.get("country") for d in geo_defs]
    assert "US" in countries, f"Updated country not found in stored: {geo_defs}"

    stored_states = []
    for d in geo_defs:
        if d.get("country") == "US":
            stored_states = d.get("states", [])
            break

    assert "CA" in stored_states or "NY" in stored_states, (
        f"Expected updated states ['CA', 'NY'], got: {stored_states}"
    )

    print(f"     GET confirms update: states={stored_states}")

    allure.attach(
        f"name:      {created_geofence}\n"
        f"updated states: {stored_states}",
        name="Update Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Geofence API")
@allure.story("Update Definition")
@allure.title("PUT update definition — type field can be changed")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Changes the rule 'type' from 'include' to 'exclude' and verifies the "
    "updated value is persisted."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_update_definition_change_type(
    api_client,
    geofence_base_path,
    created_geofence,
):
    """Rule type can be changed from 'include' to 'exclude'."""
    payload = {
        "type": "exclude",
        "geofence": {
            "type": "admin",
            "definitions": [
                {"country": "US", "states": ["TX"]}
            ],
        },
    }

    response = api_client.http_client.put(
        f"{geofence_base_path}/definitions/{created_geofence}",
        json=payload,
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    get_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/{created_geofence}",
        with_apikey=False,
    )
    assert get_response.status_code == 200

    stored_type = get_response.json().get("type")
    assert stored_type == "exclude", (
        f"Expected type='exclude', got {stored_type!r}"
    )

    print(f"\n[OK] Rule type changed to 'exclude' and persisted")


@allure.feature("Geofence API")
@allure.story("Update Definition")
@allure.title("PUT update definition — idempotent: same payload returns 200 twice")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Calls PUT with the same payload twice. Both calls should return 200."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_update_definition_idempotent(
    api_client,
    geofence_base_path,
    created_geofence,
    admin_geofence_payload,
):
    """PUT with the same payload twice — both calls return 200."""
    for call_num in (1, 2):
        response = api_client.http_client.put(
            f"{geofence_base_path}/definitions/{created_geofence}",
            json=admin_geofence_payload,
            with_apikey=False,
        )
        assert response.status_code == 200, (
            f"Call {call_num}: expected 200, got {response.status_code}"
        )

    print(f"\n[OK] PUT is idempotent — both calls returned 200")


# ==============================================================================
# TESTS — NEGATIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Update Definition")
@allure.title("PUT update definition — non-existent name returns 404")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Calls PUT with a name that does not exist. Expects 404."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_update_definition_unknown_name_returns_404(
    api_client,
    geofence_base_path,
    admin_geofence_payload,
):
    """PUT on a non-existent definition → 404."""
    response = api_client.http_client.put(
        f"{geofence_base_path}/definitions/this-does-not-exist-xyz",
        json=admin_geofence_payload,
        with_apikey=False,
    )

    assert response.status_code == 404, (
        f"Expected 404 for unknown name, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Unknown name → 404")


@allure.feature("Geofence API")
@allure.story("Update Definition")
@allure.title("PUT update definition — empty body returns 400")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends a PUT with an empty body to an existing definition. Expects 400."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_update_definition_empty_body_rejected(
    api_client,
    geofence_base_path,
    created_geofence,
):
    """PUT with empty body → 400."""
    response = api_client.http_client.put(
        f"{geofence_base_path}/definitions/{created_geofence}",
        json={},
        with_apikey=False,
    )

    assert response.status_code in (400, 422), (
        f"Expected 400/422, got {response.status_code}. Response: {response.text}"
    )

    print(f"\n[OK] Empty body correctly rejected → {response.status_code}")
