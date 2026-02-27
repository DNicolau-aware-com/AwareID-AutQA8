# Gallery (1-N Match) Test Suite

Automated test suite for the **AwareID Gallery API** (`/onboarding/gallery`).
Covers user registration, 1-N face matching, custom gallery management, and gallery membership operations.

**Base path:** `/onboarding/gallery`

---

## How It Works — .env-Driven Data

All tests reuse **real data persisted in `.env`** rather than creating throwaway fixtures on every run.
Running a seed test once populates the keys; subsequent tests read those values automatically.

| .env Key | Written by | Read by |
|---|---|---|
| `GALLERY_REGISTRATION_CODE` | `test_register_user_all_fields`, `test_register_multiple_users` | `registered_user` fixture |
| `GALLERY_REGISTRATION_CODES` | `test_register_user_all_fields`, `test_register_multiple_users` | `registration_codes` fixture, match/delete/list tests |
| `GALLERY_USERNAME` | same as above | informational |
| `GALLERY_USERNAMES` | same as above | informational |
| `GALLERY_EMAIL` | `test_register_user_all_fields` | informational |
| `GALLERY_NAME` | `test_add_gallery` | `custom_gallery` fixture, `test_delete_gallery` |
| `GALLERY_NAMES` | `test_list_gallery` (custom galleries only, max 10) | `gallery_names` fixture, match/delete/list tests |

**Rolling lists** (`GALLERY_REGISTRATION_CODES`, `GALLERY_USERNAMES`, `GALLERY_NAMES`) keep a maximum of **10 entries** — oldest entries are dropped automatically when the limit is reached.

**`(default)` gallery** is excluded from `GALLERY_NAMES` because it does not support `deleteRegistrationFromGallery` or `deleteGallery`.

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
| `FACE` | Base64-encoded JPEG face photo — used for `registerUser` and `matchFace` |
| `SPOOF` | Base64-encoded spoof image — used for `matchFace` spoof tests |
| `TX_DL_FACE` | *(optional)* Face from a TX driver's licence — tests skip gracefully if absent |

> `TEST` (legacy key) is still accepted by the `gallery_face_image` fixture as a fallback.

---

## Recommended Test Execution Order

Run the phases **in order** to avoid skips or failures caused by missing `.env` data.
Delete-phase tests are intentionally placed last as they are destructive.

---

### Phase 0 — Seed `.env` once (run before everything else)

These tests **create real data** and save it to `.env` for all subsequent tests.

```bash
# Step 1 — Register 5 users at once (fills GALLERY_REGISTRATION_CODES up to 10)
pytest tests/stateful_apis/gallery/test_register_user.py::test_register_multiple_users -v

# Step 2 — Create a custom gallery (saves GALLERY_NAME)
pytest tests/stateful_apis/gallery/test_add_gallery.py::test_add_gallery -v

# Step 3 — Discover all custom galleries (saves GALLERY_NAMES, excludes "(default)")
pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v
```

> Re-run Step 1 a second time to accumulate ≥ 10 registration codes if needed.
> Re-run Steps 2 + 3 whenever you add new galleries via the admin portal.

---

### Phase 1 — Add / enroll users in galleries

Requires `GALLERY_REGISTRATION_CODES` and `GALLERY_NAMES` to be set in `.env`.

```bash
# Bulk add single user to all galleries
pytest tests/stateful_apis/gallery/test_add_registrations_to_galleries.py -v

# Bulk add ALL stored users to ALL stored galleries (requires ≥ 2 codes and ≥ 2 galleries)
pytest tests/stateful_apis/gallery/test_add_multiple_users_to_galleries.py -v

# Add single user to a single custom gallery (also runs a negative test)
pytest tests/stateful_apis/gallery/test_add_registration_to_gallery.py -v
```

---

### Phase 2 — Verify / read operations

Safe to run at any time after Phase 1. No data is modified.

```bash
# Check enrollment status (true + false variants)
pytest tests/stateful_apis/gallery/test_is_registration_in_gallery.py -v

# List galleries a user belongs to
pytest tests/stateful_apis/gallery/test_list_gallery_of_registration.py -v

# List users enrolled in a gallery (with pagination)
pytest tests/stateful_apis/gallery/test_list_registration_in_gallery.py -v

# Face matching — default gallery + custom gallery (FACE, SPOOF, TX_DL_FACE images)
pytest tests/stateful_apis/gallery/test_match_face.py -v

# List all galleries
pytest tests/stateful_apis/gallery/test_list_gallery.py -v
```

---

### Phase 3 — Delete operations ⚠️ destructive — run last

After these tests you will need to re-run Phase 0 → Phase 1 before running Phase 2 again.

```bash
# Remove first user from first gallery, verify absence via isRegistrationInGallery
pytest tests/stateful_apis/gallery/test_delete_registration_from_gallery.py::test_delete_registration_from_gallery -v

# Bulk remove ALL stored users from ALL stored galleries
pytest tests/stateful_apis/gallery/test_delete_registrations_from_galleries.py -v

# Delete the gallery stored in GALLERY_NAME; clears GALLERY_NAME from .env
pytest tests/stateful_apis/gallery/test_delete_gallery.py::test_delete_gallery -v
```

---

### Negative tests — run any time

These never modify data and do not depend on `.env` state.

```bash
pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_missing_username -v
pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_missing_email -v
pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_missing_image -v
pytest tests/stateful_apis/gallery/test_register_user.py::test_register_user_invalid_image -v
pytest tests/stateful_apis/gallery/test_add_gallery.py::test_add_gallery_missing_name -v
pytest tests/stateful_apis/gallery/test_delete_gallery.py::test_delete_gallery_missing_name -v
pytest tests/stateful_apis/gallery/test_add_registration_to_gallery.py::test_add_registration_to_gallery_missing_name -v
pytest tests/stateful_apis/gallery/test_match_face.py::test_match_face_missing_image -v
```

---

### Run all Gallery tests at once

```bash
pytest -m gallery -v
```

> **Note:** Running `-m gallery` without the phase ordering above may result in skipped tests
> if `.env` has not been seeded first. The seed phase must be completed at least once.

**With Allure report:**
```bash
pytest -m gallery -v
allure serve allure-results
```

---

## Endpoints Covered

| Method | Path | Test File |
|---|---|---|
| POST | `/registerUser` | `test_register_user.py` |
| POST | `/matchFace` | `test_match_face.py` |
| POST | `/addGallery` | `test_add_gallery.py` |
| POST | `/deleteGallery` | `test_delete_gallery.py` |
| GET | `/listGallery` | `test_list_gallery.py` |
| POST | `/addRegistrationToGallery` | `test_add_registration_to_gallery.py` |
| POST | `/addRegistrationsToGalleries` | `test_add_registrations_to_galleries.py` |
| POST | `/deleteRegistrationFromGallery` | `test_delete_registration_from_gallery.py` |
| POST | `/deleteRegistrationsFromGalleries` | `test_delete_registrations_from_galleries.py` |
| POST | `/isRegistrationInGallery` | `test_is_registration_in_gallery.py` |
| POST | `/listGalleryOfRegistration` | `test_list_gallery_of_registration.py` |
| POST | `/listRegistrationInGallery` | `test_list_registration_in_gallery.py` |
| POST | `/addRegistrationsToGalleries` (multi-user) | `test_add_multiple_users_to_galleries.py` |

---

## Test Files

### `test_register_user.py` — POST registerUser (7 tests)

| Test | Severity | Description |
|---|---|---|
| `test_register_user_required_fields_only` | CRITICAL | Register with username, email, image only. Expects 200 + valid registrationCode. |
| `test_register_user_all_fields` | NORMAL | Register with all optional fields. Saves `GALLERY_REGISTRATION_CODE`, `GALLERY_REGISTRATION_CODES`, `GALLERY_USERNAMES` to .env. |
| `test_register_multiple_users` | NORMAL | Registers 5 users in one run. Appends all codes to `GALLERY_REGISTRATION_CODES` (max 10). **Recommended seed test.** |
| `test_register_user_missing_username` | NORMAL | Missing username → 400/500. |
| `test_register_user_missing_email` | NORMAL | Missing email → 400/500. |
| `test_register_user_missing_image` | NORMAL | Missing image → 400/500. |
| `test_register_user_invalid_image` | NORMAL | Non-image base64 → 400/500. |

---

### `test_match_face.py` — POST matchFace (10 tests)

#### Default gallery `(default)`

| Test | Image | candidateList |
|---|---|---|
| `test_match_face_default_face_empty_candidate_list` | `FACE` | `[]` — match all enrolled users |
| `test_match_face_default_face_with_candidate` | `FACE` | `[reg_code]` from .env |
| `test_match_face_default_spoof_image` | `SPOOF` | none — logs score |
| `test_match_face_default_tx_dl_face` | `TX_DL_FACE` | none — skipped if key absent |

#### Custom gallery from `GALLERY_NAMES[0]`

| Test | Image | candidateList |
|---|---|---|
| `test_match_face_custom_gallery_face_empty_candidate_list` | `FACE` | `[]` |
| `test_match_face_custom_gallery_face_with_candidate` | `FACE` | `[reg_code]` from .env |
| `test_match_face_custom_gallery_spoof_image` | `SPOOF` | none |
| `test_match_face_custom_gallery_tx_dl_face` | `TX_DL_FACE` | none — skipped if key absent |

#### Structural / Negative

| Test | Severity | Description |
|---|---|---|
| `test_match_face_empty_custom_gallery` | MINOR | Fresh empty temp gallery → matchCount == 0. Temp gallery deleted in `finally`. |
| `test_match_face_missing_image` | NORMAL | Missing image → 400/500. |

---

### `test_add_gallery.py` — POST addGallery (2 tests)

| Test | Severity | Description |
|---|---|---|
| `test_add_gallery` | CRITICAL | Create a custom gallery. Saves `GALLERY_NAME` to .env. Gallery persists in admin portal. |
| `test_add_gallery_missing_name` | NORMAL | Missing galleryName → 400/500. |

---

### `test_delete_gallery.py` — POST deleteGallery (2 tests)

| Test | Severity | Description |
|---|---|---|
| `test_delete_gallery` | CRITICAL | Reads `GALLERY_NAME` from .env and deletes it. Verifies gone via listGallery. Clears `GALLERY_NAME` from .env. |
| `test_delete_gallery_missing_name` | NORMAL | Missing galleryName → 400/500. |

---

### `test_list_gallery.py` — GET listGallery (2 tests)

| Test | Severity | Description |
|---|---|---|
| `test_list_gallery` | NORMAL | Lists all galleries. Saves custom gallery names (excluding `(default)`, max 10) to `GALLERY_NAMES`. |
| `test_list_gallery_includes_custom_gallery` | NORMAL | Creates a gallery via `custom_gallery` fixture and verifies it appears in the list. |

---

### `test_add_registration_to_gallery.py` — POST addRegistrationToGallery (2 tests)

| Test | Severity | Description |
|---|---|---|
| `test_add_registration_to_gallery` | CRITICAL | Add user (from .env) to gallery (from .env). Verify via isRegistrationInGallery → exist == true. |
| `test_add_registration_to_gallery_missing_name` | NORMAL | Missing galleryName → 400/500. |

---

### `test_add_registrations_to_galleries.py` — POST addRegistrationsToGalleries (1 test)

| Test | Severity | Description |
|---|---|---|
| `test_add_registrations_to_galleries_bulk` | NORMAL | Bulk add `GALLERY_REGISTRATION_CODE` to all `GALLERY_NAMES`. Requires ≥ 2 galleries. |

---

### `test_add_multiple_users_to_galleries.py` — POST addRegistrationsToGalleries (1 test)

| Test | Severity | Description |
|---|---|---|
| `test_add_multiple_users_to_multiple_galleries` | NORMAL | Bulk add all `GALLERY_REGISTRATION_CODES` to all `GALLERY_NAMES` in one API call. Requires ≥ 2 codes and ≥ 2 galleries. |

---

### `test_delete_registration_from_gallery.py` — POST deleteRegistrationFromGallery (1 test)

| Test | Severity | Description |
|---|---|---|
| `test_delete_registration_from_gallery` | CRITICAL | Remove `GALLERY_REGISTRATION_CODES[0]` from `GALLERY_NAMES[0]`. Verify absence via isRegistrationInGallery. |

---

### `test_delete_registrations_from_galleries.py` — POST deleteRegistrationsFromGalleries (1 test)

| Test | Severity | Description |
|---|---|---|
| `test_delete_registrations_from_galleries_bulk` | NORMAL | Bulk remove all `GALLERY_REGISTRATION_CODES` from all `GALLERY_NAMES`. Requires ≥ 2 codes and ≥ 2 galleries. |

---

### `test_is_registration_in_gallery.py` — POST isRegistrationInGallery (2 tests)

| Test | Severity | Description |
|---|---|---|
| `test_is_registration_in_gallery_true` | NORMAL | Check `GALLERY_REGISTRATION_CODES[0]` in `GALLERY_NAMES[0]` → exist == true. |
| `test_is_registration_in_gallery_false` | NORMAL | Creates a fresh empty gallery inline; checks the user is not in it → exist == false. Temp gallery deleted in `finally`. |

---

### `test_list_gallery_of_registration.py` — POST listGalleryOfRegistration (1 test)

| Test | Severity | Description |
|---|---|---|
| `test_list_gallery_of_registration` | NORMAL | Calls listGalleryOfRegistration for `GALLERY_REGISTRATION_CODES[0]`. Expects `GALLERY_NAMES[0]` to appear in the result. |

---

### `test_list_registration_in_gallery.py` — POST listRegistrationInGallery (2 tests)

| Test | Severity | Description |
|---|---|---|
| `test_list_registration_in_gallery` | NORMAL | Lists users enrolled in `GALLERY_NAMES[0]`. Verifies `GALLERY_REGISTRATION_CODES[0]` appears in the result. |
| `test_list_registration_in_gallery_paged` | MINOR | pageSize=1 on `GALLERY_NAMES[0]` → result list has ≤ 1 entry. |

---

## Fixtures (conftest.py)

| Fixture | Scope | Description |
|---|---|---|
| `gallery_base_path` | function | Returns `"/onboarding/gallery"`. |
| `gallery_face_image` | function | Reads `FACE` (or `TEST`) from .env; strips `data:` prefix. Skips if absent. |
| `unique_gallery_name` | function | Generates `test_gallery_<8hex>`. |
| `registered_user` | function | Reads `GALLERY_REGISTRATION_CODE` from .env. Skips if absent. |
| `custom_gallery` | function | Reads `GALLERY_NAME` from .env (no teardown); creates a temp gallery + deletes in teardown if absent. |
| `registration_codes` | function | Reads `GALLERY_REGISTRATION_CODES` from .env. Skips if < 2 entries. |
| `gallery_names` | function | Reads `GALLERY_NAMES` from .env (custom galleries only). Skips if < 2 entries. |
| `log_api_responses` | function (autouse) | Patches HTTP client to log all requests/responses. Attaches JSON summaries to Allure. Writes artifact JSON files per test run. |

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
| `@allure.feature` | `Gallery API` |
| `@allure.story` | `User Registration`, `1-N Face Matching — Default Gallery`, `1-N Face Matching — Custom Gallery`, `1-N Face Matching`, `Gallery Management`, `Gallery Membership`, plus `- Negative` variants |
| `@pytest.mark` | `stateful`, `gallery` |
