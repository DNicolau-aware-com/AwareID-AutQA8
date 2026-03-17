"""
Tests for PUT /compliance/geofence/definitions/{geofenceName}/toggle-status

Enables or disables a geofence definition.

Response structure:
    200  Updated rule object (with toggled enabled/active status)
    404  Definition not found
    500  errorCode, errorMsg, status, timestamp

No request body required — the endpoint toggles the current state.
"""

import allure
import pytest


_STATUS_FIELDS = ("enabled", "active", "status", "isEnabled", "isActive")


def _extract_status(rule: dict) -> object:
    """Return the status/enabled field value from a rule object, or None."""
    geo = rule.get("geofence", {})
    for field in _STATUS_FIELDS:
        if field in rule:
            return rule[field]
        if field in geo:
            return geo[field]
    return None


# ==============================================================================
# TESTS — POSITIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Toggle Status")
@allure.title("PUT toggle-status — returns 200")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Creates a definition, then calls PUT toggle-status. Expects 200."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_toggle_status_returns_200(
    api_client,
    geofence_base_path,
    created_geofence,
):
    """PUT toggle-status → 200."""
    response = api_client.http_client.put(
        f"{geofence_base_path}/definitions/{created_geofence}/toggle-status",
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    print(f"\n[OK] PUT toggle-status/{created_geofence} → 200")

    allure.attach(
        f"name: {created_geofence}\nstatus: {response.status_code}\nbody: {response.text[:500]}",
        name="Toggle Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Geofence API")
@allure.story("Toggle Status")
@allure.title("PUT toggle-status — status field changes after toggle")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Calls toggle-status twice and verifies the status field alternates. "
    "Skips if the response does not contain a recognisable status field."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_toggle_status_alternates(
    api_client,
    geofence_base_path,
    created_geofence,
):
    """Two toggles: status flips then flips back."""
    # First toggle
    r1 = api_client.http_client.put(
        f"{geofence_base_path}/definitions/{created_geofence}/toggle-status",
        with_apikey=False,
    )
    assert r1.status_code == 200, f"First toggle failed: {r1.status_code}"

    try:
        body1 = r1.json()
    except Exception:
        pytest.skip("Toggle response is not JSON — cannot check status alternation")

    status_after_first = _extract_status(body1)
    if status_after_first is None:
        pytest.skip(
            f"No recognisable status field in response. Keys: {list(body1.keys())}"
        )

    # Second toggle
    r2 = api_client.http_client.put(
        f"{geofence_base_path}/definitions/{created_geofence}/toggle-status",
        with_apikey=False,
    )
    assert r2.status_code == 200, f"Second toggle failed: {r2.status_code}"

    status_after_second = _extract_status(r2.json())

    assert status_after_first != status_after_second, (
        f"Status did not change after second toggle: "
        f"first={status_after_first!r}, second={status_after_second!r}"
    )

    print(f"\n[OK] Status alternates: {status_after_first!r} → {status_after_second!r}")

    allure.attach(
        f"after toggle 1: {status_after_first}\nafter toggle 2: {status_after_second}",
        name="Toggle Alternation",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Geofence API")
@allure.story("Toggle Status")
@allure.title("PUT toggle-status — GET reflects new status")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Calls toggle-status and verifies the subsequent GET returns the updated status."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_toggle_status_persisted_in_get(
    api_client,
    geofence_base_path,
    created_geofence,
):
    """Status change from toggle is visible in GET by name."""
    # Toggle
    toggle_response = api_client.http_client.put(
        f"{geofence_base_path}/definitions/{created_geofence}/toggle-status",
        with_apikey=False,
    )
    assert toggle_response.status_code == 200

    try:
        toggle_body = toggle_response.json()
    except Exception:
        pytest.skip("Toggle response is not JSON")

    status_after_toggle = _extract_status(toggle_body)
    if status_after_toggle is None:
        pytest.skip("No recognisable status field in toggle response")

    # Verify via GET
    get_response = api_client.http_client.get(
        f"{geofence_base_path}/definitions/{created_geofence}",
        with_apikey=False,
    )
    assert get_response.status_code == 200

    stored_status = _extract_status(get_response.json())

    assert stored_status == status_after_toggle, (
        f"GET status {stored_status!r} does not match toggle response {status_after_toggle!r}"
    )

    print(f"\n[OK] Toggled status '{status_after_toggle}' persisted in GET")


# ==============================================================================
# TESTS — NEGATIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Toggle Status")
@allure.title("PUT toggle-status — non-existent name returns 404")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Calls toggle-status with a name that does not exist. Expects 404."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_toggle_status_unknown_name_returns_404(
    api_client,
    geofence_base_path,
):
    """PUT toggle-status on a non-existent name → 404."""
    response = api_client.http_client.put(
        f"{geofence_base_path}/definitions/this-does-not-exist-xyz/toggle-status",
        with_apikey=False,
    )

    assert response.status_code == 404, (
        f"Expected 404 for unknown name, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Unknown name → 404")
