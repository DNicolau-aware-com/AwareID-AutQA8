"""
Tests for GET /compliance/geofence/definitions

Returns all stored geocoding definitions configured in the AwareID portal.
Each entry in the response array defines a geofence rule with a type and
a geofence configuration object.

Response structure:
    200  Array of geofence rule objects (may be empty if none are configured)
         Each object:
             type      string — "include" (rule direction)
             geofence  object — one of AdminGeofence | CircularGeofence | CustomGeofence

         AdminGeofence:
             geofence.type         "admin"
             geofence.definitions  [{country: string, states: [string]}]

    500  errorCode, errorMsg, status, timestamp

No request parameters — authentication is handled by the framework (JWT / API Key).
"""

import allure
import pytest


# ==============================================================================
# CONSTANTS
# ==============================================================================

_VALID_RULE_TYPES = {"include", "exclude"}
_VALID_GEOFENCE_TYPES = {"admin", "circular", "custom"}


# ==============================================================================
# HELPERS
# ==============================================================================

def _assert_error_structure(result: dict) -> None:
    """Assert a 500 error response contains all required fields."""
    for field in ("errorCode", "errorMsg", "status", "timestamp"):
        assert field in result, f"Expected '{field}' in error response, got: {result}"


# ==============================================================================
# TESTS
# ==============================================================================

@allure.feature("Geofence API")
@allure.story("Get Definitions")
@allure.title("GET definitions returns 200 with an array")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Calls GET /compliance/geofence/definitions. "
    "Expects HTTP 200 with a JSON array — the array may be empty if no "
    "geofence rules are configured in the portal."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_get_definitions(
    api_client,
    geofence_base_path,
):
    """GET definitions → 200 with a JSON array."""
    response = api_client.http_client.get(
        f"{geofence_base_path}/definitions",
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert isinstance(result, list), (
        f"Response must be a JSON array, got: {type(result).__name__}. Body: {result}"
    )

    print(f"\n[OK] GET definitions → 200")
    print(f"     definitions count : {len(result)}")

    allure.attach(
        f"status:      200\n"
        f"definitions: {len(result)} rule(s) returned",
        name="Definitions Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Geofence API")
@allure.story("Get Definitions")
@allure.title("GET definitions — each rule has required type and geofence fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "When the definitions array is non-empty, validates that each entry contains "
    "a 'type' field (string) and a 'geofence' object with its own 'type' field. "
    "Skips if no definitions are configured."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_get_definitions_rule_structure(
    api_client,
    geofence_base_path,
):
    """Each rule object has 'type' (string) and 'geofence' (object) fields."""
    response = api_client.http_client.get(
        f"{geofence_base_path}/definitions",
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    definitions = response.json()
    assert isinstance(definitions, list), (
        f"Expected a list, got: {type(definitions).__name__}"
    )

    if not definitions:
        pytest.skip("No geofence definitions configured — skipping structure validation")

    for i, rule in enumerate(definitions):
        assert isinstance(rule, dict), (
            f"Rule[{i}] must be an object, got: {type(rule).__name__}"
        )
        assert "type" in rule, f"Rule[{i}] missing 'type' field. Keys: {list(rule.keys())}"
        assert isinstance(rule["type"], str), (
            f"Rule[{i}].type must be a string, got: {type(rule['type']).__name__}"
        )
        assert "geofence" in rule, (
            f"Rule[{i}] missing 'geofence' field. Keys: {list(rule.keys())}"
        )
        assert isinstance(rule["geofence"], dict), (
            f"Rule[{i}].geofence must be an object, got: {type(rule['geofence']).__name__}"
        )

    print(f"\n[OK] All {len(definitions)} rule(s) have required fields")
    for i, rule in enumerate(definitions):
        print(f"     [{i}] type={rule['type']!r}  geofence.type={rule['geofence'].get('type')!r}")

    allure.attach(
        "\n".join(
            f"[{i}] type={r['type']!r}  geofence.type={r['geofence'].get('type')!r}"
            for i, r in enumerate(definitions)
        ),
        name="Rule Structure Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("Geofence API")
@allure.story("Get Definitions")
@allure.title("GET definitions — geofence type values match spec enum")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Validates that geofence.type in each rule is one of the spec-defined values: "
    "admin, circular, or custom. Skips if no definitions are configured."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_get_definitions_geofence_type_values(
    api_client,
    geofence_base_path,
):
    """geofence.type in each rule is one of: admin | circular | custom."""
    response = api_client.http_client.get(
        f"{geofence_base_path}/definitions",
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    definitions = response.json()
    if not definitions:
        pytest.skip("No geofence definitions configured — skipping type value validation")

    for i, rule in enumerate(definitions):
        geofence = rule.get("geofence", {})
        geo_type = geofence.get("type")

        if geo_type is not None:
            assert geo_type in _VALID_GEOFENCE_TYPES, (
                f"Rule[{i}].geofence.type must be one of {_VALID_GEOFENCE_TYPES}, "
                f"got: '{geo_type}'"
            )

    print(f"\n[OK] All geofence types are valid")
    for i, rule in enumerate(definitions):
        print(f"     [{i}] geofence.type = {rule['geofence'].get('type')!r}")


@allure.feature("Geofence API")
@allure.story("Get Definitions")
@allure.title("GET definitions — admin geofence has definitions array with country and states")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "For any rule where geofence.type == 'admin', validates that geofence.definitions "
    "is an array of objects, each with a 'country' string and a 'states' array. "
    "Skips if no admin-type geofences are configured."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_get_definitions_admin_geofence_structure(
    api_client,
    geofence_base_path,
):
    """Admin-type geofences have definitions: [{country, states}]."""
    response = api_client.http_client.get(
        f"{geofence_base_path}/definitions",
        with_apikey=False,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    definitions = response.json()
    admin_rules = [
        (i, r) for i, r in enumerate(definitions)
        if isinstance(r.get("geofence"), dict) and r["geofence"].get("type") == "admin"
    ]

    if not admin_rules:
        pytest.skip("No admin-type geofence definitions found — skipping admin structure check")

    for i, rule in admin_rules:
        geo = rule["geofence"]
        defs = geo.get("definitions")

        assert defs is not None, (
            f"Rule[{i}] admin geofence missing 'definitions' field. "
            f"geofence keys: {list(geo.keys())}"
        )
        assert isinstance(defs, list), (
            f"Rule[{i}] geofence.definitions must be an array, got: {type(defs).__name__}"
        )

        for j, entry in enumerate(defs):
            assert isinstance(entry, dict), (
                f"Rule[{i}].definitions[{j}] must be an object, got: {type(entry).__name__}"
            )
            assert "country" in entry, (
                f"Rule[{i}].definitions[{j}] missing 'country'. Keys: {list(entry.keys())}"
            )
            assert isinstance(entry["country"], str), (
                f"Rule[{i}].definitions[{j}].country must be a string"
            )

            states = entry.get("states")
            if states is not None:
                assert isinstance(states, list), (
                    f"Rule[{i}].definitions[{j}].states must be an array"
                )
                for state in states:
                    assert isinstance(state, str), (
                        f"Each state in Rule[{i}].definitions[{j}].states must be a string"
                    )

        print(f"\n[OK] Rule[{i}] admin definitions valid ({len(defs)} entr{'y' if len(defs) == 1 else 'ies'})")
        for j, entry in enumerate(defs):
            print(f"     [{j}] country={entry['country']!r}  states={entry.get('states', [])}")

        allure.attach(
            "\n".join(
                f"country={e['country']!r}  states={e.get('states', [])}"
                for e in defs
            ),
            name=f"Admin Geofence Rule[{i}] Definitions",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.feature("Geofence API")
@allure.story("Get Definitions")
@allure.title("GET definitions — response can be called repeatedly and returns 200")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Calls GET /compliance/geofence/definitions twice and verifies both calls "
    "return HTTP 200. Confirms the endpoint is idempotent."
)
@pytest.mark.stateful
@pytest.mark.geofence
def test_get_definitions_is_idempotent(
    api_client,
    geofence_base_path,
):
    """Two consecutive GET calls both return 200 with consistent counts."""
    response1 = api_client.http_client.get(
        f"{geofence_base_path}/definitions", with_apikey=False
    )
    response2 = api_client.http_client.get(
        f"{geofence_base_path}/definitions", with_apikey=False
    )

    assert response1.status_code == 200, (
        f"First call: expected 200, got {response1.status_code}"
    )
    assert response2.status_code == 200, (
        f"Second call: expected 200, got {response2.status_code}"
    )

    count1 = len(response1.json()) if isinstance(response1.json(), list) else "N/A"
    count2 = len(response2.json()) if isinstance(response2.json(), list) else "N/A"

    assert count1 == count2, (
        f"Definition counts differ between calls: {count1} vs {count2}"
    )

    print(f"\n[OK] Endpoint is idempotent — both calls returned {count1} definition(s)")

    allure.attach(
        f"call1: 200, {count1} definition(s)\n"
        f"call2: 200, {count2} definition(s)",
        name="Idempotency Check",
        attachment_type=allure.attachment_type.TEXT,
    )
