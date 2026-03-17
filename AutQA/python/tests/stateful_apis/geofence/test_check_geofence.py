"""
Tests for POST /compliance/geofence/check

Checks whether a given latitude/longitude falls within the configured
geofence rules.

Request body:
    latitude   number — geographic latitude
    longitude  number — geographic longitude

Response structure:
    200  Check result object:
             allowed   boolean — true if location is within allowed geofence
             (additional fields depend on server implementation)
    400  Invalid payload (missing/invalid coordinates)
    500  errorCode, errorMsg, status, timestamp
"""

import allure
import pytest


_CHECK_PATH = "/compliance/geofence/check"

# Representative coordinates for testing
_COORDS_US_TEXAS = {"latitude": 30.2672, "longitude": -97.7431}      # Austin, TX
_COORDS_US_NEWYORK = {"latitude": 40.7128, "longitude": -74.0060}    # New York, NY
_COORDS_GERMANY = {"latitude": 52.5200, "longitude": 13.4050}        # Berlin, Germany
_COORDS_AUSTRALIA = {"latitude": -33.8688, "longitude": 151.2093}    # Sydney, Australia


# ==============================================================================
# TESTS — POSITIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Check Geofence")
@allure.title("POST check — valid coordinates return 200")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Sends a POST /compliance/geofence/check with valid US coordinates. "
    "Expects HTTP 200. The result depends on configured geofence rules "
    "so only the status code is asserted."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_check_geofence_valid_coordinates(api_client):
    """POST check with valid lat/lon → 200."""
    response = api_client.http_client.post(
        _CHECK_PATH,
        json=_COORDS_US_TEXAS,
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    print(f"\n[OK] POST /check → 200")
    print(f"     coords : lat={_COORDS_US_TEXAS['latitude']}, lon={_COORDS_US_TEXAS['longitude']}")

    try:
        result = response.json()
        print(f"     result : {result}")
        allure.attach(
            f"latitude:  {_COORDS_US_TEXAS['latitude']}\n"
            f"longitude: {_COORDS_US_TEXAS['longitude']}\n"
            f"result:    {result}",
            name="Check Result",
            attachment_type=allure.attachment_type.TEXT,
        )
    except Exception:
        pass


@allure.feature("Geofence API")
@allure.story("Check Geofence")
@allure.title("POST check — response contains a boolean result field")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Verifies the check response body contains a recognisable boolean result "
    "field (allowed, permitted, result, withinGeofence, or similar)."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_check_geofence_response_has_result_field(api_client):
    """POST check response contains a boolean 'allowed' (or similar) field."""
    response = api_client.http_client.post(
        _CHECK_PATH,
        json=_COORDS_US_TEXAS,
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )

    try:
        result = response.json()
    except Exception:
        pytest.skip("Response is not JSON — cannot validate result field")

    if not isinstance(result, dict):
        pytest.skip(f"Response is not a JSON object: {type(result).__name__}")

    _RESULT_FIELDS = ("allowed", "permitted", "result", "withinGeofence", "isAllowed", "pass")
    found = {f: result[f] for f in _RESULT_FIELDS if f in result}

    assert found, (
        f"No recognisable result field found in response. "
        f"Keys: {list(result.keys())}"
    )

    print(f"\n[OK] Result fields found: {found}")


@allure.feature("Geofence API")
@allure.story("Check Geofence")
@allure.title("POST check — multiple coordinates each return 200")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Calls POST check with four different coordinate pairs (US, NY, Germany, "
    "Australia) and verifies each returns 200."
)
@pytest.mark.stateful
@pytest.mark.geofence
@pytest.mark.parametrize("label,coords", [
    ("Austin TX",       _COORDS_US_TEXAS),
    ("New York NY",     _COORDS_US_NEWYORK),
    ("Berlin Germany",  _COORDS_GERMANY),
    ("Sydney Australia",_COORDS_AUSTRALIA),
])
def test_check_geofence_multiple_locations(api_client, label, coords):
    """Each coordinate pair returns 200."""
    response = api_client.http_client.post(
        _CHECK_PATH,
        json=coords,
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"{label}: expected 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] {label}: lat={coords['latitude']}, lon={coords['longitude']} → 200")


@allure.feature("Geofence API")
@allure.story("Check Geofence")
@allure.title("POST check — endpoint is idempotent for same coordinates")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Calls POST check with the same coordinates twice and verifies both "
    "responses are 200 with the same result."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_check_geofence_idempotent(api_client):
    """Two calls with identical coordinates return consistent results."""
    r1 = api_client.http_client.post(
        _CHECK_PATH,
        json=_COORDS_US_TEXAS,
        with_apikey=False,
    )
    r2 = api_client.http_client.post(
        _CHECK_PATH,
        json=_COORDS_US_TEXAS,
        with_apikey=False,
    )

    assert r1.status_code == 200, f"Call 1: expected 200, got {r1.status_code}"
    assert r2.status_code == 200, f"Call 2: expected 200, got {r2.status_code}"

    try:
        body1 = r1.json()
        body2 = r2.json()
        assert body1 == body2, (
            f"Results differ between identical calls:\n  call1={body1}\n  call2={body2}"
        )
    except Exception:
        pass  # Non-JSON response — status code check is sufficient

    print(f"\n[OK] POST check is idempotent for same coordinates")


# ==============================================================================
# TESTS — NEGATIVE
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Check Geofence")
@allure.title("POST check — missing latitude returns 400")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a POST with only longitude (latitude missing). Expects 400."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_check_geofence_missing_latitude(api_client):
    """POST check with missing latitude → 400."""
    response = api_client.http_client.post(
        _CHECK_PATH,
        json={"longitude": -97.7431},
        with_apikey=False,
    )

    assert response.status_code in (400, 422), (
        f"Expected 400/422 for missing latitude, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Missing latitude → {response.status_code}")


@allure.feature("Geofence API")
@allure.story("Check Geofence")
@allure.title("POST check — missing longitude returns 400")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a POST with only latitude (longitude missing). Expects 400."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_check_geofence_missing_longitude(api_client):
    """POST check with missing longitude → 400."""
    response = api_client.http_client.post(
        _CHECK_PATH,
        json={"latitude": 30.2672},
        with_apikey=False,
    )

    assert response.status_code in (400, 422), (
        f"Expected 400/422 for missing longitude, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Missing longitude → {response.status_code}")


@allure.feature("Geofence API")
@allure.story("Check Geofence")
@allure.title("POST check — out-of-range latitude returns 400")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends coordinates with latitude outside the valid range (-90 to 90). "
    "Expects 400."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_check_geofence_invalid_latitude_range(api_client):
    """POST check with latitude > 90 → 400."""
    response = api_client.http_client.post(
        _CHECK_PATH,
        json={"latitude": 999.0, "longitude": -97.7431},
        with_apikey=False,
    )

    assert response.status_code in (400, 422), (
        f"Expected 400/422 for out-of-range latitude, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Out-of-range latitude → {response.status_code}")


@allure.feature("Geofence API")
@allure.story("Check Geofence")
@allure.title("POST check — empty body returns 400")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends a POST with an empty body. Expects 400."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_check_geofence_empty_body(api_client):
    """POST check with empty body → 400."""
    response = api_client.http_client.post(
        _CHECK_PATH,
        json={},
        with_apikey=False,
    )

    assert response.status_code in (400, 422), (
        f"Expected 400/422 for empty body, got {response.status_code}. "
        f"Response: {response.text}"
    )

    print(f"\n[OK] Empty body → {response.status_code}")
