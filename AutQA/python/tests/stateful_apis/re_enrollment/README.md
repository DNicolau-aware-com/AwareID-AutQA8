# Re-Enrollment Test Suite

Automated test suite for the **AwareID Re-Enrollment API** (`/onboarding/reEnrollment`).
Covers face liveness verification during the re-enrollment process, including positive,
structural, and negative test cases.

**Base path:** `/onboarding/reEnrollment`

---

## How It Works

Re-enrollment requires a session token (`reEnrollmentToken`) obtained from
`/onboarding/enrollment/enroll` for a user that is **already enrolled** in the system.

Unlike the Gallery suite (which stores tokens in `.env`), the `reEnrollmentToken` is
**short-lived** and obtained fresh inline for each test by the `re_enrollment_token`
fixture. The only persistent state stored in `.env` is the username.

| .env Key | Written by | Read by |
|---|---|---|
| `RE_ENROLLMENT_USERNAME` | Set manually once | `re_enrollment_token` fixture |
| `FACE` | Set manually once | `re_enrollment_face_image` fixture |
| `SPOOF` | Set manually once | `re_enrollment_spoof_image` fixture |
| `WORKFLOW` | Set manually once | `re_enrollment_workflow` fixture |

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
| `RE_ENROLLMENT_USERNAME` | Username of an **already-enrolled** user (verifyFace tests) |
| `GET_PUBLIC_KEY_USERNAME` | Username of an **already-enrolled** user (completeReEnroll tests) |
| `FACE` | Base64-encoded JPEG face photo — used for positive tests |
| `SPOOF` | *(optional)* Base64-encoded spoof image — used for `test_verify_face_spoof_image` |
| `WORKFLOW` | *(optional)* Liveness workflow name — defaults to `charlie4` |
| `RE_ENROLLMENT_EMAIL` | *(optional)* Email used during original enrollment — falls back to `EMAIL` then `<username>@example.com` |
| `FIRSTNAME` | *(optional)* First name — defaults to `Test` |
| `LASTNAME` | *(optional)* Last name — defaults to `User` |

> `TEST` (legacy key) is still accepted by `re_enrollment_face_image` as a fallback for `FACE`.

---

## Setup

### completeReEnroll tests — set RE_ENROLLMENT_USERNAME once

The `complete_re_enrollment_token` fixture reads `RE_ENROLLMENT_USERNAME` from `.env`
and calls `/enrollment/enroll` to get a fresh `reEnrollmentToken` each run.

**Requires:** `RE_ENROLLMENT_USERNAME` set to an already-enrolled username.

### verifyFace tests — set RE_ENROLLMENT_USERNAME once

Both `verifyFace` and `completeReEnroll` tests read `RE_ENROLLMENT_USERNAME` from `.env`. Set it manually:

```dotenv
RE_ENROLLMENT_USERNAME=your_enrolled_username
```

### Optional: pre-existing ECDSA public key

Device tests use `GET_PUBLIC_KEY_USERNAME` from `.env` as the raw base64 public key.
Multi-line PEM format is **not** supported — store as a single-line base64 value:

```dotenv
GET_PUBLIC_KEY_USERNAME=MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE...
```

If absent, a fresh ECDSA key is generated dynamically.

ECDSA key pairs for device tests are **generated dynamically** when no `.env` key is present — no configuration needed.

---

## Recommended Test Execution Order

### completeReEnroll tests — run after setting GET_PUBLIC_KEY_USERNAME

```bash
# Minimal call (token only)
pytest tests/stateful_apis/re_enrollment/test_complete_re_enroll.py::test_complete_re_enroll -v

# With device — addOrUpdate=0 (add) and =1 (replace)
pytest tests/stateful_apis/re_enrollment/test_complete_re_enroll.py::test_complete_re_enroll_add_device -v
pytest tests/stateful_apis/re_enrollment/test_complete_re_enroll.py::test_complete_re_enroll_replace_device -v

# Negative (no username needed)
pytest tests/stateful_apis/re_enrollment/test_complete_re_enroll.py::test_complete_re_enroll_invalid_token -v
pytest tests/stateful_apis/re_enrollment/test_complete_re_enroll.py::test_complete_re_enroll_missing_token -v
pytest tests/stateful_apis/re_enrollment/test_complete_re_enroll.py::test_complete_re_enroll_invalid_public_key -v
```

---

### verifyFace tests — run after setting RE_ENROLLMENT_USERNAME

```bash
# Full happy path — live face, response structure, authStatus validation
pytest tests/stateful_apis/re_enrollment/test_verify_face.py::test_verify_face -v

# Validate all spec-defined response fields including nested faceLivenessResults
pytest tests/stateful_apis/re_enrollment/test_verify_face.py::test_verify_face_response_structure -v

# Spoof image — logs liveness decision (SPOOF required in .env)
pytest tests/stateful_apis/re_enrollment/test_verify_face.py::test_verify_face_spoof_image -v
```

### Negative tests — run any time (no .env token state required)

```bash
# Invalid token (random UUID) → 400/500
pytest tests/stateful_apis/re_enrollment/test_verify_face.py::test_verify_face_invalid_token -v

# Missing reEnrollmentToken field → 400/500
pytest tests/stateful_apis/re_enrollment/test_verify_face.py::test_verify_face_missing_token -v

# Valid token, missing faceLivenessData → 400/500
pytest tests/stateful_apis/re_enrollment/test_verify_face.py::test_verify_face_missing_face_data -v

# Valid token, empty frames array → 400/500
pytest tests/stateful_apis/re_enrollment/test_verify_face.py::test_verify_face_empty_frames -v
```

### Run all Re-Enrollment tests at once

```bash
pytest -m re_enrollment -v
```

**With Allure report:**
```bash
pytest -m re_enrollment -v
allure serve allure-results
```

---

## Endpoints Covered

| Method | Path | Test File |
|---|---|---|
| POST | `/verifyFace` | `test_verify_face.py` |
| POST | `/completeReEnroll` | `test_complete_re_enroll.py` |
| POST | `/cancel` | `test_cancel_re_enroll.py` |

---

## Test Files

### `test_cancel_re_enroll.py` — POST cancel (3 tests)

#### Positive

| Test | Severity | Description |
|---|---|---|
| `test_cancel_re_enroll` | CRITICAL | Valid reEnrollmentToken → 200. Session is cancelled. |

#### Negative

| Test | Severity | Description |
|---|---|---|
| `test_cancel_re_enroll_invalid_token` | NORMAL | Random UUID token → 400/500 + error structure. |
| `test_cancel_re_enroll_missing_token` | NORMAL | Empty body (no token) → 400/500 + error structure. |

---

### `test_complete_re_enroll.py` — POST completeReEnroll (6 tests)

#### Positive

| Test | Severity | Description |
|---|---|---|
| `test_complete_re_enroll` | CRITICAL | Token only (no device) → 200 + registrationCode. Minimal valid call. |
| `test_complete_re_enroll_add_device` | NORMAL | Token + deviceId + generated ECDSA key + addOrUpdate=0 → 200 + registrationCode. |
| `test_complete_re_enroll_replace_device` | NORMAL | Token + deviceId + generated ECDSA key + addOrUpdate=1 (replace all existing) → 200 + registrationCode. |

#### Negative

| Test | Severity | Description |
|---|---|---|
| `test_complete_re_enroll_invalid_token` | NORMAL | Random UUID token → 400/500 + error structure. |
| `test_complete_re_enroll_missing_token` | NORMAL | Empty body (no token) → 400/500. |
| `test_complete_re_enroll_invalid_public_key` | MINOR | Valid token + non-ECDSA publicKey → 400/500. |

> **ECDSA key pairs** are generated dynamically per test using Python's `cryptography` library (secp256k1 curve). No keys need to be stored in `.env`.

---

### `test_verify_face.py` — POST verifyFace (7 tests)

#### Positive

| Test | Severity | Description |
|---|---|---|
| `test_verify_face` | CRITICAL | Full happy path: valid token + FACE frames → 200 + livenessResult, matchResult, matchScore, authStatus. |
| `test_verify_face_response_structure` | NORMAL | Validates all spec fields. When `faceLivenessResults` is present, checks nested `liveness_result` (feedback, score, decision, score_frr). |
| `test_verify_face_spoof_image` | NORMAL | Valid token + SPOOF frames → 200. Logs `livenessResult` (expected false) and `decision`. Skipped if `SPOOF` absent. |

#### Negative

| Test | Severity | Description |
|---|---|---|
| `test_verify_face_invalid_token` | NORMAL | Random UUID token → 400/500 + errorCode/errorMsg/status/timestamp. |
| `test_verify_face_missing_token` | NORMAL | No `reEnrollmentToken` field → 400/500. |
| `test_verify_face_missing_face_data` | NORMAL | Valid token, no `faceLivenessData` field → 400/500. |
| `test_verify_face_empty_frames` | MINOR | Valid token, empty `frames` array → 400/500. |

---

## Fixtures (conftest.py)

| Fixture | Scope | Description |
|---|---|---|
| `re_enrollment_base_path` | function | Returns `"/onboarding/reEnrollment"`. |
| `re_enrollment_face_image` | function | Reads `FACE` (or `TEST`) from .env; strips `data:` prefix. Skips if absent. |
| `re_enrollment_spoof_image` | function | Reads `SPOOF` from .env; strips `data:` prefix. Skips if absent. |
| `re_enrollment_workflow` | function | Reads `WORKFLOW` from .env. Defaults to `charlie4`. |
| `re_enrollment_token` | function | Calls `/onboarding/enrollment/enroll` with `RE_ENROLLMENT_USERNAME` to get a fresh `reEnrollmentToken`. Used by verifyFace tests. |
| `complete_re_enrollment_token` | function | Calls `/enrollment/enroll` with `RE_ENROLLMENT_USERNAME` → yields `reEnrollmentToken`. Used by completeReEnroll tests. |
| `log_api_responses` | function (autouse) | Patches HTTP client to log all requests/responses. Attaches JSON summaries to Allure. Writes artifact JSON files per test run. |

---

## Response Schema (200)

```json
{
  "livenessResult": true,
  "matchResult": true,
  "matchScore": 98.5,
  "authStatus": 2,
  "faceLivenessResults": {
    "video": {},
    "liveness_result": {
      "feedback": ["SCORES_READY"],
      "score": 100.0,
      "decision": "LIVE",
      "score_frr": 99.1
    }
  }
}
```

| Field | Type | Values |
|---|---|---|
| `livenessResult` | boolean | `true` = live person, `false` = not live |
| `matchResult` | boolean | `true` = matches enrolled data, `false` = no match |
| `matchScore` | float | Matching score |
| `authStatus` | integer | `0` = Failed, `1` = Pending, `2` = Complete |
| `liveness_result.score` | double | `-1.0` = Error, `0.0` = Not Live, `100.0` = Live |
| `liveness_result.decision` | string | `LIVE`, `SPOOF`, `TOO_BLURRY`, `UNABLE_TO_CALCULATE_LIVENESS` |

---

## Error Response Format

```json
{
  "errorCode": "INPUT_FORMAT_ERROR",
  "errorMsg": "Field is missing",
  "status": 400,
  "timestamp": "2021-10-12T01:06:24.000Z"
}
```

Valid `errorCode` values: `INPUT_FORMAT_ERROR`, `INPUT_VALUES_ERROR`, `INTERNAL_SERVER_ERROR`

---

## Allure Metadata

| Attribute | Values |
|---|---|
| `@allure.feature` | `Re-Enrollment API` |
| `@allure.story` | `Face Liveness — Re-Enrollment`, `Face Liveness — Re-Enrollment - Negative` |
| `@pytest.mark` | `stateful`, `re_enrollment` |
