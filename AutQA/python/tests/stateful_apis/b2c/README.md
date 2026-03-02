# B2C Test Suite

Automated test suite for the **AwareID B2C API** (`/onboarding/b2c`).
Covers triggering enrollment and authentication sessions via the B2C Authenticator,
and polling the status of those operations.

**Base path:** `/onboarding/b2c`

---

## How It Works

B2C operations allow an enrolled user to authenticate or re-enroll using the
**AwareID Authenticator** mobile app by scanning a QR code or receiving a link
via email or push notification.

Each positive test uses the `b2c_enrolled_user` fixture, which reads
`B2C_USERNAME` (or `RE_ENROLLMENT_USERNAME`) from `.env` — no fresh enrollment
is created per test.

The `b2c_session_token` fixture calls `POST /triggerAuthenticate` inline to
obtain a fresh `sessionToken` for `operationStatus` tests.

| `.env` Key | Required | Description |
|---|---|---|
| `B2C_USERNAME` | Yes (positive tests) | Already-enrolled username. Falls back to `RE_ENROLLMENT_USERNAME`. |
| `RE_ENROLLMENT_USERNAME` | Fallback | Used if `B2C_USERNAME` is not set. |
| `B2C_PHONE` | Optional | Phone number for `notifyByPush` tests. |

> The email `dnicolau.aware@gmail.com` is hardcoded in `conftest.py` as `B2C_EMAIL`
> and used in `triggerEnroll` payloads.

---

## Prerequisites

- Python 3.12+
- `pytest`, `allure-pytest`, `pytest-html` installed
- A valid `.env` file with at minimum:

| Key | Description |
|---|---|
| `BASEURL` | Base URL of the AwareID server (e.g. `https://qa8.awareid.com`) |
| `CLIENT_ID` | OAuth2 client ID |
| `CLIENT_SECRET` | OAuth2 client secret |
| `REALM_NAME` | Keycloak realm name (e.g. `snow`) |
| `APIKEY` | API key header value |
| `B2C_USERNAME` | Username of an **already-enrolled** user |

---

## Observed API Behaviour

| Endpoint | Invalid input | Response |
|---|---|---|
| `POST /triggerEnroll` | Missing/empty/unknown username | `200` with `status='FAILURE'`, null session fields, `errorSummary` |
| `POST /triggerAuthenticate` | Missing/empty/unknown username | `500` with `errorCode`, `errorMsg`, `status`, `timestamp` |
| `GET /operationStatus/{token}` | Random/malformed token | `400` or `500` with error structure |

---

## Run Commands

```bash
# All B2C tests
pytest -m b2c -v

# Individual test files
pytest tests/stateful_apis/b2c/test_trigger_enroll.py -v
pytest tests/stateful_apis/b2c/test_trigger_authenticate.py -v
pytest tests/stateful_apis/b2c/test_get_operation_status.py -v

# With Allure report
pytest -m b2c -v
allure serve allure-results
```

---

## Endpoints Covered

| Method | Path | Test File |
|---|---|---|
| POST | `/b2c/triggerEnroll` | `test_trigger_enroll.py` |
| POST | `/b2c/triggerAuthenticate` | `test_trigger_authenticate.py` |
| GET | `/b2c/operationStatus/{sessionToken}` | `test_get_operation_status.py` |

---

## Test Files

### `test_trigger_enroll.py` — POST triggerEnroll (7 tests)

Triggers an enrollment session via the B2C Authenticator. Always returns HTTP 200;
invalid inputs produce `status='FAILURE'` instead of 4xx/5xx.

#### Positive

| Test | Severity | Description |
|---|---|---|
| `test_trigger_enroll` | CRITICAL | Enrolled username only → 200 SUCCESS + sessionToken, sessionCallbackURL, qrcodeImage. |
| `test_trigger_enroll_with_email` | NORMAL | Username + `dnicolau.aware@gmail.com` → 200 SUCCESS. |
| `test_trigger_enroll_notify_by_email` | NORMAL | Username + email + `notifyByEmail=true` → 200 SUCCESS. Link delivered to `dnicolau.aware@gmail.com`. |
| `test_trigger_enroll_response_structure` | NORMAL | Validates `sessionCallbackURL` starts with `http`, `qrcodeImage` length > 100 chars. |

#### Negative

| Test | Severity | Description |
|---|---|---|
| `test_trigger_enroll_missing_username` | NORMAL | Empty body → 200 `status='FAILURE'`, null session fields, errorSummary present. |
| `test_trigger_enroll_empty_username` | NORMAL | `username=""` → 200 `status='FAILURE'`. |
| `test_trigger_enroll_unknown_username` | NORMAL | Non-existent generated username → 200 `status='FAILURE'`. |

---

### `test_trigger_authenticate.py` — POST triggerAuthenticate (7 tests)

Triggers an authentication session. Returns HTTP 500 (not 200 FAILURE) for
missing/empty/unknown usernames — different from `triggerEnroll`.

#### Positive

| Test | Severity | Description |
|---|---|---|
| `test_trigger_authenticate` | CRITICAL | Enrolled username only → 200 SUCCESS + sessionToken, sessionCallbackURL, qrcodeImage. |
| `test_trigger_authenticate_notify_by_email` | NORMAL | Username + `notifyByEmail=true` → 200 SUCCESS. Link sent to `dnicolau.aware@gmail.com`. |
| `test_trigger_authenticate_notify_by_push` | NORMAL | Username + `notifyByPush=true` → 200 SUCCESS. |
| `test_trigger_authenticate_response_structure` | NORMAL | Validates URL format and qrcodeImage length. |

#### Negative

| Test | Severity | Description |
|---|---|---|
| `test_trigger_authenticate_missing_username` | NORMAL | Empty body → 500 + errorCode, errorMsg, status, timestamp. |
| `test_trigger_authenticate_empty_username` | NORMAL | `username=""` → 500 + error structure. |
| `test_trigger_authenticate_unknown_username` | NORMAL | Non-existent generated username → 500 + error structure. |

---

### `test_get_operation_status.py` — GET operationStatus/{sessionToken} (5 tests)

Polls the completion status of a B2C operation. The `b2c_session_token` fixture
calls `POST /triggerAuthenticate` inline to obtain a fresh token.

#### Positive

| Test | Severity | Description |
|---|---|---|
| `test_get_operation_status` | CRITICAL | Valid sessionToken → 200, `completionStatus` in `{Pending, Success, Failed, Cancelled}`. |
| `test_get_operation_status_is_pending` | NORMAL | Fresh token polled immediately → `completionStatus == 'Pending'`. |
| `test_get_operation_status_response_structure` | NORMAL | Validates `completionStatus` is a string matching the spec enum. |

#### Negative

| Test | Severity | Description |
|---|---|---|
| `test_get_operation_status_invalid_token` | NORMAL | Random UUID token → 400 or 500 + error structure. |
| `test_get_operation_status_malformed_token` | MINOR | Plain string (non-UUID) token → 400 or 500. |

---

## Fixtures (conftest.py)

| Fixture | Scope | Description |
|---|---|---|
| `b2c_base_path` | function | Returns `"/onboarding/b2c"`. |
| `b2c_enrolled_user` | function | Reads `B2C_USERNAME` (or `RE_ENROLLMENT_USERNAME`) from `.env`. Returns `{"username": ..., "email": "dnicolau.aware@gmail.com"}`. Skips if absent. |
| `b2c_session_token` | function | Calls `POST /triggerAuthenticate` with the enrolled username → returns `sessionToken` string. Skips if SUCCESS not returned. |
| `b2c_phone` | function | Reads `B2C_PHONE` from `.env`. Skips if absent. |
| `log_api_responses` | function (autouse) | Patches HTTP client to log all requests/responses. Attaches JSON summaries to Allure. Writes artifact JSON files per test run. |

---

## Response Schemas

### triggerEnroll / triggerAuthenticate — 200 SUCCESS

```json
{
  "status": "SUCCESS",
  "sessionToken": "DGJHDIUEIHOEWUIEOO",
  "sessionCallbackURL": "https://awareid.com/GHDFHFYUEUET",
  "qrcodeImage": "iVGDHSGJKDH..."
}
```

### triggerEnroll — 200 FAILURE

```json
{
  "status": "FAILURE",
  "sessionToken": null,
  "sessionCallbackURL": null,
  "qrcodeImage": null,
  "errorSummary": "User information not found"
}
```

### operationStatus — 200

```json
{
  "completionStatus": "Pending"
}
```

| `completionStatus` | Meaning |
|---|---|
| `Pending` | Session created, awaiting authenticator action |
| `Success` | User completed the operation in the app |
| `Failed` | Operation failed (liveness / match rejected) |
| `Cancelled` | Session was cancelled |

### Error — 400 / 500

```json
{
  "errorCode": "INTERNAL_SERVER_ERROR",
  "errorMsg": "Internal server error while processing request",
  "status": 500,
  "timestamp": "2026-03-02 07:36:25"
}
```

---

## Allure Metadata

| Attribute | Values |
|---|---|
| `@allure.feature` | `B2C API` |
| `@allure.story` | `Trigger Enrollment`, `Trigger Authentication`, `Operation Status`, `Trigger Enrollment - Negative`, `Trigger Authentication - Negative`, `Operation Status - Negative` |
| `@pytest.mark` | `stateful`, `b2c` |
