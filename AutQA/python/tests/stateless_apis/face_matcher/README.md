# Face Matcher (Nexaface) Test Suite

Automated test suite for the **AwareID Face Matcher API** (`/nexaface`).
Covers face comparison, face template export, error handling, and server health discovery.

---

## Overview

The Face Matcher API is a biometric service that performs 1-to-1 face matching and generates
face templates from images. It is accessed via the Aware NexaFace Library.

**Base path:** `/nexaface`
**Server version tested:** `Aware NexaFace Library, version 2.14 r173027`

---

## Endpoints Covered

| Method | Path               | Description                             |
|--------|--------------------|-----------------------------------------|
| GET    | `/nexaface/version` | Returns the server version string       |
| POST   | `/nexaface/compare` | 1-to-1 face comparison (probe vs gallery) |
| POST   | `/nexaface/export`  | Exports a biometric face template from a face image |

---

## Prerequisites

- Python 3.12+
- `pytest`, `allure-pytest`, `pytest-html` installed
- A valid `.env` file with the following keys:

| Key          | Description                                                      |
|--------------|------------------------------------------------------------------|
| `BASEURL`    | Base URL of the AwareID server (e.g. `https://qa8.awareid.com`) |
| `CLIENT_ID`  | OAuth2 client ID for token retrieval                             |
| `CLIENT_SECRET` | OAuth2 client secret                                          |
| `REALM_NAME` | Keycloak realm name (e.g. `snow`)                                |
| `APIKEY`     | API key header value                                             |
| `JWT`        | Auto-populated by the framework on each run                      |
| `TEST`       | Base64-encoded JPEG face image used for all face tests           |

> **Important:** The `TEST` image must be a real JPEG or PNG face photo (not a binary template).
> Use a clear, well-lit frontal face image. The framework auto-refreshes the JWT before each run.

---

## Setup

```bash
cd python/
pip install -r requirements.txt
```

Ensure your `.env` file is populated. To convert a face photo to base64:

```bash
python -c "import base64; print('TEST=' + base64.b64encode(open('face.jpg','rb').read()).decode())" >> .env
```

---

## Running the Tests

**Run all Face Matcher tests:**
```bash
pytest -m face_matcher -v -s
```

**Run with Allure report (recommended):**
```bash
pytest -m face_matcher -v -s
allure serve allure-results
```

**Run with HTML report:**
```bash
pytest -m face_matcher -v -s --html=report.html --self-contained-html
```

**Run a single test file:**
```bash
pytest tests/stateless_apis/face_matcher/test_compare.py -v -s
```

---

## Test Files

### `test_version.py` — Server Health (1 test)

| Test | Severity | Description |
|------|----------|-------------|
| `test_get_nexaface_version` | BLOCKER | Calls `GET /nexaface/version`. Expects HTTP 200 and a non-empty version string. Primary liveness check. |

---

### `test_compare.py` — Face Comparison (3 tests)

| Test | Severity | Description |
|------|----------|-------------|
| `test_compare_same_person_high_score` | CRITICAL | Sends the same face image as both probe and gallery with algorithm F500. Expects HTTP 200 and `scorePercent > 80`. |
| `test_compare_with_different_algorithms[F200]` | NORMAL | Tests comparison with F200 algorithm. Skipped automatically if the algorithm is disabled on the server (error code 113). |
| `test_compare_with_different_algorithms[F500]` | NORMAL | Tests comparison with F500 algorithm. Expects HTTP 200 and `scorePercent > 80`. |
| `test_compare_with_metadata` | MINOR | Includes optional client metadata fields (username, device info, OS version, etc.). Expects HTTP 200 and a valid score. |

**Request structure:**
```json
{
  "probe":   { "VISIBLE_FRONTAL": "<base64_jpeg>" },
  "gallery": { "VISIBLE_FRONTAL": "<base64_jpeg>" },
  "workflow": {
    "comparator": {
      "algorithm": "F500",
      "faceTypes": ["VISIBLE_FRONTAL"]
    }
  },
  "metadata": { "username": "...", "client_device_brand": "..." }
}
```

**Response structure:**
```json
{ "score": 43.71, "scorePercent": 100 }
```

---

### `test_export.py` — Face Template Export (2 tests)

| Test | Severity | Description |
|------|----------|-------------|
| `test_export_face_template` | CRITICAL | Sends a face image with an encounter ID. Expects HTTP 200 and a non-empty base64 template in the `export` field. |
| `test_export_without_encounter_id` | MINOR | Sends a face image without an encounter ID. The ID is optional; accepts HTTP 200, 400, or 500. |

**Request structure:**
```json
{
  "encounter": {
    "VISIBLE_FRONTAL": "<base64_jpeg>",
    "id": "encounter_test_001"
  }
}
```

**Response structure:**
```json
{ "export": "<base64_encoded_template>" }
```

---

### `test_compare_negative.py` — Input Validation for Compare (5 tests)

| Test | Severity | Description |
|------|----------|-------------|
| `test_compare_missing_probe` | NORMAL | No probe image. Expects 400/500 + structured error body. |
| `test_compare_missing_gallery` | NORMAL | No gallery image. Expects 400/500 + structured error body. |
| `test_compare_missing_workflow` | NORMAL | No workflow block. Expects 400/500 + structured error body. |
| `test_compare_invalid_algorithm` | NORMAL | Uses `"INVALID_ALGO"` as algorithm. Expects 400/500. Server may return empty body (also accepted). |
| `test_compare_empty_payload` | NORMAL | Completely empty JSON body `{}`. Expects 400/500 + structured error body. |

---

### `test_export_negative.py` — Input Validation for Export (3 tests)

| Test | Severity | Description |
|------|----------|-------------|
| `test_export_missing_encounter` | NORMAL | Empty payload `{}`. Expects 400/500 indicating missing `encounter` field. |
| `test_export_missing_visible_frontal` | NORMAL | Encounter with ID only, no image. Expects 400/500. |
| `test_export_invalid_base64` | NORMAL | Valid base64 of plain text (not a JPEG). Expects 400/500 indicating invalid image. |

---

### `test_error_responses.py` — Error Format Validation (2 tests)

| Test | Severity | Description |
|------|----------|-------------|
| `test_error_response_structure` | NORMAL | Triggers an error with empty payload. Validates that the response follows one of the two supported error formats (see below). |
| `test_endpoints_exist_and_reject_empty_payload[/compare]` | NORMAL | Confirms `/compare` is reachable and rejects empty input. |
| `test_endpoints_exist_and_reject_empty_payload[/export]` | NORMAL | Confirms `/export` is reachable and rejects empty input. |

**Supported error formats:**

Nested (actual server behavior):
```json
{ "error": { "code": -3, "description": "Required field \"probe\" is missing." } }
```

Standard (documented API spec):
```json
{ "errorCode": "INPUT_FORMAT_ERROR", "errorMsg": "...", "status": 400, "timestamp": "..." }
```

---

### `test_server_capabilities.py` — Server Discovery (4 tests)

| Test | Severity | Description |
|------|----------|-------------|
| `test_check_server_version` | BLOCKER | Verifies `GET /version` returns 200. Attaches version string to report. |
| `test_discover_enabled_algorithms` | MINOR | Tests all algorithms in `SUPPORTED_ALGORITHMS`. Logs enabled/disabled. Fails if none are enabled. |
| `test_check_available_endpoints` | NORMAL | Probes all 3 endpoints and logs availability. Fails if none respond. |
| `test_server_capabilities_summary` | MINOR | Comprehensive summary: version + algorithms + endpoints. Attaches a text summary to the Allure report. |

---

## Test Data

All face images are loaded from the `.env` file using the `TEST` key.
The same image is used for both probe and gallery (same-person comparisons).

The fixture chain:
```
TEST (.env key)
    └── face_image_base64 (fixture)
            ├── probe_face_image  (alias)
            └── gallery_face_image (alias)
```

---

## Report Attachments

Every HTTP transaction is automatically captured and attached to the Allure report:

- **Request body** (JSON) — base64 image strings are truncated for readability
- **Response body** (JSON or text) — template exports are also truncated
- **Response time** — shown in the attachment name as `[0.312s]`
- **Algorithm discovery summary** — text attachment on `test_discover_enabled_algorithms`
- **Server capabilities summary** — text attachment on `test_server_capabilities_summary`
- **Server version** — text attachment on `test_check_server_version`

---

## Known Server Configuration

Based on test runs against `qa8.awareid.com`:

| Item | Value |
|------|-------|
| F500 algorithm | **Enabled** |
| F200 algorithm | **Disabled** (error code 113) |
| Same-person score (F500) | ~43.7 raw / 100% normalized |

---

## Allure Metadata

All tests are tagged with:

| Attribute | Value |
|-----------|-------|
| `@allure.feature` | `Face Matcher API` |
| `@allure.story` | `Face Comparison`, `Face Template Export`, `Negative - Input Validation`, `Negative - Export Validation`, `Error Response Format`, `Server Health`, `Server Discovery` |
| `@pytest.mark` | `stateless`, `face_matcher` |
