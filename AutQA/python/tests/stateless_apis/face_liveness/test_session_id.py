"""
GUID-Based Replay Defense — Test Suite
Ticket: AwareID - GUID-Based Replay Defense (AWAREX-5607/5608/5609)

Endpoints:
    GET  /b2c/sdk/session-id            — obtain a single-use server-issued GUID
    POST /b2c/sdk/faceliveness/analyze  — faceliveness; session_id in meta_data

Server config key: DETECT_REPLAY_ATTACH  (none | optional | mandatory)
    none      — no GUID validation, behaves as v12.14 (default)
    optional  — validates session_id when present; passthrough when absent
    mandatory — session_id required; rejects absent, expired, or reused GUIDs

Session-id expiry: 5 minutes (300 s) by default; configurable via REPLAY_UUID_TIMEOUT.

Prerequisites (.env):
    TX_DL_FACE_B64          — base64 face image for analyze-endpoint tests
    DETECT_REPLAY_ATTACH    — (optional) mirrors server config so mode-specific tests
                              can assert the correct expected behaviour.
                              If not set, mode-sensitive tests run with permissive
                              assertions and print a warning.

All tests that require GET /b2c/sdk/session-id skip automatically when the
endpoint returns 404 (feature not yet deployed on this server).
"""

import re
import time
import pytest
import allure


# Override the conftest fixture — parametrize over FACE and SPOOF for this file only
@pytest.fixture(params=["FACE", "SPOOF"])
def face_image_base64(env_store, request):
    key = request.param
    img = env_store.get(key)
    if not img:
        pytest.skip(f"{key} not found in .env")
    return img

# ---------------------------------------------------------------------------
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

SESSION_ID_PATH = "/b2c/sdk/getSessionId"
ANALYZE_PATH    = "/b2c/sdk/faceliveness/analyze"

VALID_MODES = {"none", "optional", "mandatory"}


# ==============================================================================
# SHARED HELPERS
# ==============================================================================

def _is_uuid(value: str) -> bool:
    return isinstance(value, str) and bool(_UUID_RE.match(value))


def _log(label: str, response) -> None:
    """Print request label, status code, and (truncated) response body."""
    try:
        import json as _json
        body = _json.dumps(response.json(), indent=2)
    except Exception:
        body = response.text or "(empty)"
    if len(body) > 600:
        body = body[:600] + f"\n  ... [truncated, total {len(body)} chars]"
    print(f"\n{'-'*60}")
    print(f"  {label}")
    print(f"  Status : {response.status_code}")
    print(f"  Body   :\n{body}")
    print(f"{'-'*60}")


def _require_session_id_endpoint(api_client):
    """
    Guard: call the session-id endpoint; skip only if it returns 404 (not deployed).
    Returns the raw response so callers can inspect it.
    """
    response = api_client.http_client.get(SESSION_ID_PATH, retry=False)
    if response.status_code == 404:
        pytest.skip(
            f"GET {SESSION_ID_PATH} returned 404 — Session ID feature not yet deployed "
            "on this server. Set BASEURL to an environment where the feature is active "
            "(e.g. dev24.awareid.com) and ensure DETECT_REPLAY_ATTACH is configured."
        )
    return response


def _fetch_session_id(api_client) -> str:
    """Obtain a fresh server-issued session ID; skip if endpoint is unavailable."""
    response = _require_session_id_endpoint(api_client)
    assert response.status_code == 200, (
        f"GET {SESSION_ID_PATH} returned {response.status_code}: {response.text[:300]}"
    )
    data = response.json()
    sid = data.get("session_id")
    assert sid, f"'session-id' missing from response: {data}"
    return sid


def _fetch_session_id(api_client) -> str:
    """Obtain a fresh server-issued session ID; skip if endpoint is unavailable."""
    response = _require_session_id_endpoint(api_client)
    assert response.status_code == 200, (
        f"GET {SESSION_ID_PATH} returned {response.status_code}: {response.text[:300]}"
    )
    data = response.json()
    sid = data.get("session_id")
    assert sid, f"'session-id' missing from response: {data}"
    return sid


def _analyze_payload(face_b64: str, session_id: str = None) -> dict:
    """
    Build a /b2c/sdk/faceliveness/analyze payload matching the Postman collection
    structure (b2c faceliveness checkLiveness replay attack fix).
    """
    now_s  = int(time.time())
    now_ms = now_s * 1000

    meta = {
        "client_device_brand": "samsung",
        "client_device_model": "SM-S901U",
        "client_os_version":   "14",
        "username":            "autqa_session_id_test",
    }
    if session_id is not None:
        meta["session_id"] = session_id   # underscore per AWID-7

    return {
        "transaction-timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "video": {
            "client_version": "Aware FaceCapture Library, version 1.3 r174597",
            "meta_data": meta,
            "workflow_data": {
                "workflow":  "Charlie2",
                "rotation":  0,
                "timestamp": now_s,
                "frames": [
                    {"data": face_b64, "tags": [], "timestamp": now_ms},
                    {"data": face_b64, "tags": [], "timestamp": now_ms + 33},
                    {"data": face_b64, "tags": [], "timestamp": now_ms + 66},
                ],
            },
        },
    }


# ==============================================================================
# SECTION 1 — GET /b2c/sdk/session-id  (issuance endpoint)
# ==============================================================================

@allure.feature("GUID Replay Defense")
@allure.story("Session ID Issuance")
@allure.title("GET /b2c/sdk/session-id returns HTTP 200")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.stateless
@pytest.mark.b2c
def test_get_session_id_returns_200(api_client):
    """Server issues a session ID and responds with HTTP 200."""
    response = _require_session_id_endpoint(api_client)

    _log(f"GET {SESSION_ID_PATH}", response)
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )
    allure.attach(response.text, name="Response body", attachment_type=allure.attachment_type.JSON)


@allure.feature("GUID Replay Defense")
@allure.story("Session ID Issuance")
@allure.title("Response contains 'session-id' key")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.stateless
@pytest.mark.b2c
def test_get_session_id_response_has_session_id_key(api_client):
    """Response JSON must contain the 'session-id' key with a non-empty value."""
    response = _require_session_id_endpoint(api_client)

    _log(f"GET {SESSION_ID_PATH}", response)
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )
    data = response.json()
    assert "session_id" in data, (
        f"Response must contain 'session-id' key. Got keys: {list(data.keys())}"
    )
    assert data["session_id"], "session-id value must be non-empty"
    allure.attach(str(data), name="Response", attachment_type=allure.attachment_type.TEXT)


@allure.feature("GUID Replay Defense")
@allure.story("Session ID Issuance")
@allure.title("session-id value is a valid RFC 4122 UUID")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.stateless
@pytest.mark.b2c
def test_get_session_id_value_is_uuid(api_client):
    """Issued session-id must be a valid UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)."""
    response = _require_session_id_endpoint(api_client)
    _log(f"GET {SESSION_ID_PATH}", response)
    assert response.status_code == 200, (
        f"GET {SESSION_ID_PATH} returned {response.status_code}: {response.text[:300]}"
    )
    sid = response.json().get("session_id")
    assert sid, f"'session_id' missing from response: {response.json()}"

    assert _is_uuid(sid), (
        f"session-id must be UUID format. Got: '{sid}'"
    )
    allure.attach(sid, name="session_id", attachment_type=allure.attachment_type.TEXT)


@allure.feature("GUID Replay Defense")
@allure.story("Session ID Issuance")
@allure.title("Response Content-Type is application/json")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.b2c
def test_get_session_id_content_type_is_json(api_client):
    """Session-id endpoint must return Content-Type: application/json."""
    response = _require_session_id_endpoint(api_client)
    _log(f"GET {SESSION_ID_PATH}", response)
    assert response.status_code == 200
    ct = response.headers.get("Content-Type", "")
    assert "application/json" in ct, (
        f"Expected application/json Content-Type, got: '{ct}'"
    )
    print(f"  Content-Type: {ct}")


@allure.feature("GUID Replay Defense")
@allure.story("Session ID Issuance")
@allure.title("Consecutive calls return different session IDs (uniqueness)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Each call to GET /b2c/sdk/session-id must return a distinct GUID. "
    "Re-using the same GUID server-side would defeat replay protection."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_consecutive_session_ids_are_unique(api_client):
    """Two back-to-back calls must issue different session IDs."""
    r1 = _require_session_id_endpoint(api_client)
    _log(f"GET {SESSION_ID_PATH} (call 1)", r1)
    r2 = _require_session_id_endpoint(api_client)
    _log(f"GET {SESSION_ID_PATH} (call 2)", r2)
    sid1 = r1.json().get("session_id")
    sid2 = r2.json().get("session_id")

    assert sid1 != sid2, (
        f"Server must issue a unique GUID per request. Both calls returned: '{sid1}'"
    )
    allure.attach(
        f"First:  {sid1}\nSecond: {sid2}",
        name="Uniqueness Check",
        attachment_type=allure.attachment_type.TEXT,
    )


# ==============================================================================
# SECTION 2 — GET /b2c/sdk/session-id  (auth / negative)
# ==============================================================================

@allure.feature("GUID Replay Defense")
@allure.story("Session ID Issuance - Auth")
@allure.title("No Authorization header → 401 or 403")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.b2c
def test_get_session_id_no_auth_rejected(api_client):
    """Session-id endpoint must reject requests without a Bearer token."""
    _require_session_id_endpoint(api_client)   # skip if not deployed

    original = api_client.http_client.jwt_token
    try:
        api_client.http_client.jwt_token = None
        response = api_client.http_client.get(SESSION_ID_PATH, retry=False)
    finally:
        api_client.http_client.jwt_token = original

    _log(f"GET {SESSION_ID_PATH} (no auth)", response)
    assert response.status_code in (401, 403), (
        f"Expected 401/403 without auth, got {response.status_code}: {response.text[:200]}"
    )


@allure.feature("GUID Replay Defense")
@allure.story("Session ID Issuance - Auth")
@allure.title("Invalid/malformed JWT → 401 or 403")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.b2c
def test_get_session_id_invalid_token_rejected(api_client):
    """A nonsense JWT string must be rejected."""
    _require_session_id_endpoint(api_client)

    original = api_client.http_client.jwt_token
    try:
        api_client.http_client.jwt_token = "not-a-real-jwt"
        response = api_client.http_client.get(SESSION_ID_PATH, retry=False)
    finally:
        api_client.http_client.jwt_token = original

    _log(f"GET {SESSION_ID_PATH} (invalid token)", response)
    assert response.status_code in (401, 403), (
        f"Expected 401/403 with invalid token, got {response.status_code}: {response.text[:200]}"
    )


@allure.feature("GUID Replay Defense")
@allure.story("Session ID Issuance - Auth")
@allure.title("Missing apikey → 400, 401, or 403")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.b2c
def test_get_session_id_no_apikey_rejected(api_client):
    """Request without apikey header must be rejected."""
    _require_session_id_endpoint(api_client)

    response = api_client.http_client.get(SESSION_ID_PATH, with_apikey=False, retry=False)
    _log(f"GET {SESSION_ID_PATH} (no apikey)", response)
    # Without apikey the gateway may return 404 (route not matched) or 401/403
    assert response.status_code in (400, 401, 403, 404), (
        f"Expected 400/401/403/404 without apikey, got {response.status_code}: {response.text[:200]}"
    )


# ==============================================================================
# SECTION 3 — /b2c/sdk/faceliveness/analyze  (endpoint availability)
# ==============================================================================

@allure.feature("GUID Replay Defense")
@allure.story("Faceliveness Analyze - Availability")
@allure.title("POST /b2c/sdk/faceliveness/analyze endpoint exists (not 404)")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.stateless
@pytest.mark.b2c
def test_b2c_analyze_endpoint_exists(api_client):
    """The B2C SDK faceliveness analyze endpoint must be reachable."""
    response = api_client.http_client.post(ANALYZE_PATH, json={}, retry=False)
    _log(f"POST {ANALYZE_PATH} (empty payload)", response)
    assert response.status_code != 404, (
        f"POST {ANALYZE_PATH} returned 404 — endpoint not deployed on this server."
    )
    allure.attach(response.text[:500], name="Response", attachment_type=allure.attachment_type.TEXT)


@allure.feature("GUID Replay Defense")
@allure.story("Faceliveness Analyze - Availability")
@allure.title("Empty payload returns a structured error (not 2xx)")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "This server wraps validation failures in HTTP 500 with errorCode/errorMsg. "
    "Both 4xx and 500 are accepted here."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_b2c_analyze_empty_payload_returns_error(api_client):
    """Empty body must produce an error response (any 4xx or 5xx)."""
    response = api_client.http_client.post(ANALYZE_PATH, json={}, retry=False)
    _log(f"POST {ANALYZE_PATH} (empty payload)", response)
    assert response.status_code >= 400, (
        f"Expected an error for empty payload, got {response.status_code}: {response.text[:300]}"
    )
    allure.attach(response.text[:500], name="Error response", attachment_type=allure.attachment_type.TEXT)


# ==============================================================================
# SECTION 4 — DETECT_REPLAY_ATTACH = optional
#   - session_id absent  → passthrough (behaves as v12.14)
#   - session_id present → validate (accept first use, reject replay)
# ==============================================================================

@allure.feature("GUID Replay Defense")
@allure.story("DETECT_REPLAY_ATTACH = optional")
@allure.title("Without session_id: analyze proceeds normally (passthrough)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "In optional mode, omitting session_id from meta_data must NOT cause a rejection. "
    "The request is processed exactly as it was in v12.14."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_optional_mode_analyze_without_session_id_passes(api_client, face_image_base64):
    """
    DETECT_REPLAY_ATTACH = optional: no session_id in metadata → request accepted.
    This covers AC: 'Timestamp-only replay validation no longer causes failures
    when end-user device clock is misconfigured' for users not yet sending GUIDs.
    """
    payload = _analyze_payload(face_image_base64, session_id=None)
    response = api_client.http_client.post(ANALYZE_PATH, json=payload, retry=False)
    _log(f"POST {ANALYZE_PATH} (no session_id)", response)
    assert response.status_code == 200, (
        f"Expected 200 when session_id is absent (optional mode passthrough), "
        f"got {response.status_code}: {response.text[:400]}"
    )
    result = response.json()
    assert "video" in result, f"Expected 'video' in response. Got: {list(result.keys())}"
    allure.attach(
        response.text[:1000],
        name="Analyze response (no session_id)",
        attachment_type=allure.attachment_type.JSON,
    )


@allure.feature("GUID Replay Defense")
@allure.story("DETECT_REPLAY_ATTACH = optional")
@allure.title("With valid server-issued session_id: analyze succeeds (first use)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "When a session_id issued by GET /b2c/sdk/session-id is included in the payload "
    "for the first time, the request must succeed."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_optional_mode_analyze_with_valid_session_id_passes(
    api_client, b2c_session_id, face_image_base64
):
    """
    DETECT_REPLAY_ATTACH = optional: valid server-issued session_id → first use accepted.
    """
    payload = _analyze_payload(face_image_base64, session_id=b2c_session_id)
    response = api_client.http_client.post(ANALYZE_PATH, json=payload)
    _log(f"POST {ANALYZE_PATH} (valid session_id={b2c_session_id})", response)
    assert response.status_code == 200, (
        f"Expected 200 for first use of session_id='{b2c_session_id}', "
        f"got {response.status_code}: {response.text[:400]}"
    )
    result = response.json()
    assert "video" in result, f"Expected 'video' in response. Got: {list(result.keys())}"
    allure.attach(
        f"session_id: {b2c_session_id}\nstatus: {response.status_code}",
        name="First Use",
        attachment_type=allure.attachment_type.TEXT,
    )


# ==============================================================================
# SECTION 5 — REPLAY ATTACK DEFENSE  (core acceptance criteria)
#   AC: "Replay protection remains enabled and rejects duplicate/replayed
#       transaction attempts."
# ==============================================================================

@allure.feature("GUID Replay Defense")
@allure.story("Replay Attack Defense")
@allure.title("Reusing the same session_id is rejected (replay blocked)")
@allure.severity(allure.severity_level.BLOCKER)
@allure.description(
    "Core AC: after a session_id has been consumed in a successful analyze call, "
    "a second request carrying the same session_id must be rejected by the server. "
    "This test requires DETECT_REPLAY_ATTACH = optional or mandatory on the server "
    "AND the GET /b2c/sdk/session-id endpoint to be deployed."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_replay_attack_same_session_id_rejected_on_second_use(
    api_client, b2c_session_id, face_image_base64
):
    """
    Single-use guarantee: once a session_id is consumed, the server must reject
    any subsequent request carrying the same GUID.

    Flow:
        1. GET /b2c/sdk/session-id              → fresh GUID
        2. POST /b2c/sdk/faceliveness/analyze   → first use  → expect 200
        3. POST /b2c/sdk/faceliveness/analyze   → second use → expect 4xx / 5xx
    """
    payload = _analyze_payload(face_image_base64, session_id=b2c_session_id)

    # ── First use: must succeed ────────────────────────────────────────────────
    r1 = api_client.http_client.post(ANALYZE_PATH, json=payload)
    _log(f"POST {ANALYZE_PATH} (first use, session_id={b2c_session_id})", r1)
    assert r1.status_code == 200, (
        f"First analyze with session_id='{b2c_session_id}' must succeed (200). "
        f"Got {r1.status_code}: {r1.text[:400]}"
    )

    # ── Second use (replay): must be rejected ──────────────────────────────────
    r2 = api_client.http_client.post(ANALYZE_PATH, json=payload, retry=False)
    _log(f"POST {ANALYZE_PATH} (replay attempt, same session_id)", r2)
    assert r2.status_code != 200, (
        f"Second use of session_id='{b2c_session_id}' must be REJECTED (replay defense). "
        f"Server accepted it again with {r2.status_code}. "
        f"Check that DETECT_REPLAY_ATTACH is set to 'optional' or 'mandatory' on this server."
    )

    allure.attach(
        f"session_id:    {b2c_session_id}\n"
        f"First use:     {r1.status_code}\n"
        f"Replay attempt:{r2.status_code}\n"
        f"Replay body:   {r2.text[:300]}",
        name="Replay Defense Summary",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("GUID Replay Defense")
@allure.story("Replay Attack Defense")
@allure.title("A session_id not issued by this server is rejected (optional/mandatory mode)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "A randomly generated UUID that was never issued by GET /b2c/sdk/session-id "
    "should be treated as invalid. In optional mode the server may or may not "
    "reject it depending on whether validation is enforced when the GUID is unknown. "
    "This test records the actual behaviour without a hard assertion on mode."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_arbitrary_uuid_not_issued_by_server(api_client, face_image_base64):
    """
    Submit a well-formed UUID that was never issued by the server.
    Skip if the session-id endpoint is not deployed (feature not available).
    Records whether the server accepts or rejects it.
    """
    _require_session_id_endpoint(api_client)   # skip if not deployed

    fake_uuid = "cafebabe-dead-beef-1234-000000000001"
    payload = _analyze_payload(face_image_base64, session_id=fake_uuid)
    response = api_client.http_client.post(ANALYZE_PATH, json=payload, retry=False)
    _log(f"POST {ANALYZE_PATH} (unissued UUID={fake_uuid})", response)

    status = response.status_code
    if status == 200:
        print(
            f"  [WARN] Server accepted an unissued UUID. "
            f"Expected in none/optional mode; should be rejected in mandatory mode."
        )
    else:
        print(f"  [OK] Unissued UUID rejected -> {status}")

    allure.attach(
        f"fake_uuid: {fake_uuid}\nstatus:    {status}\nbody:      {response.text[:300]}",
        name="Unissued UUID Behaviour",
        attachment_type=allure.attachment_type.TEXT,
    )
    # No hard assertion: we want to observe and log, not gate on server config.


# ==============================================================================
# SECTION 6 — DETECT_REPLAY_ATTACH = mandatory
#   - session_id absent  → error (required)
#   - session_id reused  → error
# ==============================================================================

@allure.feature("GUID Replay Defense")
@allure.story("DETECT_REPLAY_ATTACH = mandatory")
@allure.title("Mandatory mode: missing session_id is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "When DETECT_REPLAY_ATTACH = mandatory, the server MUST reject any analyze "
    "request that does not include session_id in meta_data. "
    "This test is skipped if the session-id endpoint is not deployed."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_mandatory_mode_analyze_without_session_id_rejected(
    api_client, face_image_base64, env_store
):
    """
    DETECT_REPLAY_ATTACH = mandatory: no session_id → 4xx/5xx.

    Only asserts if DETECT_REPLAY_ATTACH=mandatory is confirmed in .env.
    Otherwise records the actual behaviour for informational purposes.
    """
    _require_session_id_endpoint(api_client)

    configured_mode = (env_store.get("DETECT_REPLAY_ATTACH") or "").lower().strip()

    payload = _analyze_payload(face_image_base64, session_id=None)
    response = api_client.http_client.post(ANALYZE_PATH, json=payload, retry=False)
    _log(f"POST {ANALYZE_PATH} (no session_id, mode={configured_mode or 'not set'})", response)
    status = response.status_code

    if configured_mode == "mandatory":
        assert status != 200, (
            f"DETECT_REPLAY_ATTACH=mandatory: missing session_id must be rejected. "
            f"Server returned {status} (accepted the request). "
            f"Body: {response.text[:400]}"
        )
        print(f"\n[OK] Mandatory mode — missing session_id rejected → {status}")
    else:
        print(
            f"\n[INFO] DETECT_REPLAY_ATTACH not set to 'mandatory' in .env "
            f"(configured_mode='{configured_mode or 'not set'}').\n"
            f"       Server returned {status} for missing session_id. "
            f"Set DETECT_REPLAY_ATTACH=mandatory in .env to enforce this assertion."
        )

    allure.attach(
        f"DETECT_REPLAY_ATTACH (env): {configured_mode or 'not set'}\n"
        f"status: {status}\n"
        f"body:   {response.text[:400]}",
        name="Mandatory Mode — Missing session_id",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("GUID Replay Defense")
@allure.story("DETECT_REPLAY_ATTACH = mandatory")
@allure.title("Mandatory mode: replayed session_id is rejected")
@allure.severity(allure.severity_level.BLOCKER)
@allure.description(
    "In mandatory mode, using a session_id that has already been consumed must "
    "return an error regardless of how well-formed the GUID is."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_mandatory_mode_replay_rejected(
    api_client, b2c_session_id, face_image_base64, env_store
):
    """
    DETECT_REPLAY_ATTACH = mandatory: second use of session_id → rejected.
    Hard-asserts only when DETECT_REPLAY_ATTACH=mandatory confirmed in .env.
    """
    configured_mode = (env_store.get("DETECT_REPLAY_ATTACH") or "").lower().strip()

    payload = _analyze_payload(face_image_base64, session_id=b2c_session_id)

    r1 = api_client.http_client.post(ANALYZE_PATH, json=payload)
    _log(f"POST {ANALYZE_PATH} (first use, session_id={b2c_session_id})", r1)
    r2 = api_client.http_client.post(ANALYZE_PATH, json=payload, retry=False)
    _log(f"POST {ANALYZE_PATH} (replay, same session_id)", r2)

    if configured_mode == "mandatory":
        assert r1.status_code == 200, (
            f"First use must succeed in mandatory mode. Got {r1.status_code}: {r1.text[:300]}"
        )
        assert r2.status_code != 200, (
            f"Mandatory mode: replay must be rejected. "
            f"Server accepted the second request with {r2.status_code}."
        )
        print("\n[OK] Mandatory mode — replay rejected")
    else:
        print(
            f"\n[INFO] DETECT_REPLAY_ATTACH not confirmed as 'mandatory' in .env "
            f"(value='{configured_mode or 'not set'}'). Set it to enforce hard assertions."
        )

    allure.attach(
        f"DETECT_REPLAY_ATTACH (env): {configured_mode or 'not set'}\n"
        f"session_id:  {b2c_session_id}\n"
        f"First use:   {r1.status_code}\n"
        f"Replay:      {r2.status_code}\n"
        f"Replay body: {r2.text[:300]}",
        name="Mandatory Mode — Replay Attempt",
        attachment_type=allure.attachment_type.TEXT,
    )


# ==============================================================================
# SECTION 7 — Observability / response shape
# ==============================================================================

@allure.feature("GUID Replay Defense")
@allure.story("Error Response Shape")
@allure.title("Replay rejection returns a structured error body")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "When the server rejects a replay attempt it must return a JSON body with "
    "errorCode and errorMsg so callers can distinguish replay errors from other failures."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_replay_rejection_has_structured_error_body(
    api_client, b2c_session_id, face_image_base64
):
    """
    After consuming a session_id, the server's rejection of the replay must
    include a JSON body with at minimum errorCode and errorMsg fields.
    """
    payload = _analyze_payload(face_image_base64, session_id=b2c_session_id)

    r1 = api_client.http_client.post(ANALYZE_PATH, json=payload)
    _log(f"POST {ANALYZE_PATH} (first use, session_id={b2c_session_id})", r1)
    if r1.status_code != 200:
        pytest.skip(
            f"First use failed ({r1.status_code}) — cannot test replay rejection shape. "
            f"Body: {r1.text[:300]}"
        )

    r2 = api_client.http_client.post(ANALYZE_PATH, json=payload, retry=False)
    _log(f"POST {ANALYZE_PATH} (replay attempt, same session_id)", r2)
    if r2.status_code == 200:
        pytest.skip(
            f"Replay was accepted (server may be configured as DETECT_REPLAY_ATTACH=none). "
            f"Cannot verify error shape when no error is returned."
        )

    try:
        body = r2.json()
    except Exception:
        pytest.fail(
            f"Replay rejection (HTTP {r2.status_code}) must return JSON. "
            f"Got non-JSON body: {r2.text[:300]}"
        )

    assert "errorCode" in body or "error" in body or "message" in body, (
        f"Replay rejection body must contain an error indicator. "
        f"Got keys: {list(body.keys())}"
    )

    print(f"\n[OK] Replay rejection body has error keys: {list(body.keys())}")
    allure.attach(
        r2.text[:800],
        name="Replay Rejection Error Body",
        attachment_type=allure.attachment_type.JSON,
    )


# ==============================================================================
# SECTION 8 — Input validation (session_id field values)
# ==============================================================================

@allure.feature("GUID Replay Defense")
@allure.story("Input Validation")
@allure.title("Empty string session_id is rejected")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.b2c
@pytest.mark.parametrize("bad_value,label", [
    ("",          "empty string"),
    ("   ",       "whitespace"),
    ("not-a-uuid","non-UUID string"),
    ("12345",     "numeric string"),
    ("00000000-0000-0000-0000-000000000000", "nil UUID"),
])
def test_invalid_session_id_value_rejected(api_client, face_image_base64, bad_value, label):
    """
    session_id present but with a malformed/invalid value must be rejected.
    Covers: empty string, whitespace, non-UUID, numeric, nil UUID.
    """
    _require_session_id_endpoint(api_client)

    payload = _analyze_payload(face_image_base64, session_id=bad_value)
    response = api_client.http_client.post(ANALYZE_PATH, json=payload, retry=False)
    _log(f"POST {ANALYZE_PATH} (session_id={label!r})", response)

    assert response.status_code != 200, (
        f"session_id with {label} value ({bad_value!r}) should be rejected. "
        f"Server returned {response.status_code}: {response.text[:300]}"
    )
    print(f"\n[OK] session_id={label!r} rejected -> {response.status_code}")
    allure.attach(
        f"bad_value: {bad_value!r}\nstatus:    {response.status_code}\nbody:      {response.text[:300]}",
        name=f"Invalid session_id ({label})",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.feature("GUID Replay Defense")
@allure.story("Input Validation")
@allure.title("Null session_id is treated as absent (not a crash)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.b2c
def test_null_session_id_does_not_crash(api_client, face_image_base64):
    """
    Explicitly setting session_id to JSON null should not cause a 500.
    The server should treat it as absent (optional-mode passthrough) or
    reject it cleanly (mandatory mode) — never crash.
    """
    _require_session_id_endpoint(api_client)

    payload = _analyze_payload(face_image_base64, session_id=None)
    # Force null into the payload (None is omitted by _analyze_payload; inject directly)
    payload["video"]["meta_data"]["session_id"] = None

    response = api_client.http_client.post(ANALYZE_PATH, json=payload, retry=False)
    _log(f"POST {ANALYZE_PATH} (session_id=null)", response)

    assert response.status_code != 500, (
        f"Null session_id caused a server crash (500): {response.text[:300]}"
    )
    print(f"\n[OK] null session_id -> {response.status_code} (no crash)")
    allure.attach(
        f"status: {response.status_code}\nbody:   {response.text[:400]}",
        name="Null session_id behaviour",
        attachment_type=allure.attachment_type.TEXT,
    )


# ==============================================================================
# SECTION 9 — Concurrent replay (race condition / double-spend)
# ==============================================================================

@allure.feature("GUID Replay Defense")
@allure.story("Concurrent Replay")
@allure.title("Simultaneous requests with the same session_id: only one succeeds")
@allure.severity(allure.severity_level.BLOCKER)
@allure.description(
    "Two requests carrying the same session_id fired concurrently must not both succeed. "
    "The server's session store must honour single-use under concurrent load — "
    "at most one 200 is acceptable; the other must be rejected."
)
@pytest.mark.stateless
@pytest.mark.b2c
def test_concurrent_replay_only_one_succeeds(api_client, b2c_session_id, face_image_base64):
    """
    Fire two analyze requests with the same session_id at the same time using
    threads. Assert that at most one of them receives HTTP 200.
    """
    import threading

    payload = _analyze_payload(face_image_base64, session_id=b2c_session_id)
    results = [None, None]

    def send(index):
        results[index] = api_client.http_client.post(ANALYZE_PATH, json=payload, retry=False)

    t1 = threading.Thread(target=send, args=(0,))
    t2 = threading.Thread(target=send, args=(1,))
    t1.start(); t2.start()
    t1.join();  t2.join()

    r1, r2 = results
    _log(f"POST {ANALYZE_PATH} (thread 1, session_id={b2c_session_id})", r1)
    _log(f"POST {ANALYZE_PATH} (thread 2, same session_id)", r2)

    statuses = (r1.status_code, r2.status_code)
    successes = statuses.count(200)

    assert successes <= 1, (
        f"Both concurrent requests with the same session_id returned 200. "
        f"Single-use guarantee is broken under concurrent load. "
        f"session_id={b2c_session_id}, statuses={statuses}"
    )
    print(f"\n[OK] Concurrent replay: statuses={statuses}, successes={successes}/2")
    allure.attach(
        f"session_id: {b2c_session_id}\n"
        f"Thread 1:   {r1.status_code} — {r1.text[:200]}\n"
        f"Thread 2:   {r2.status_code} — {r2.text[:200]}",
        name="Concurrent Replay Result",
        attachment_type=allure.attachment_type.TEXT,
    )
