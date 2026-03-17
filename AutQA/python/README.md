# AwareID Test Automation (AutQA8)

Automated test suite for the AwareID biometric identity verification platform. Covers enrollment, authentication, admin configuration, and stateless biometric APIs.

---

## Requirements

- Python 3.9+
- pip

Install dependencies:

```bash
pip install -r requirements.txt
pip install allure-pytest python-dotenv
```

---

## Setup

1. Copy `.env.example` to `.env` (or create `.env` manually):

```
BASEURL=https://your-aware-id-host.com
APIKEY=your-api-key
REALM_NAME=your-realm
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
ENROLLED_USERNAME=an-existing-enrolled-user
```

2. Optionally add base64-encoded test images:

```
FACE_FRAMES=<base64>
TX_DL_FRONT_b64=<base64>
TX_DL_BACK_b64=<base64>
```

> The JWT token is auto-refreshed before every test run — you do not need to set it manually.

---

## Running Tests

Run all tests:
```bash
pytest
```

Run a specific test group using markers:
```bash
pytest -m enrollment
pytest -m authentication
pytest -m admin
pytest -m stateless
pytest -m face_liveness
pytest -m face_matcher
pytest -m gallery
pytest -m document_verification
```

Run a specific file:
```bash
pytest tests/stateful_apis/enrollment/test_initiate_enrollment.py
```

---

## Test Reports

After a run, two reports are generated automatically:

| Report | Location | Notes |
|--------|----------|-------|
| HTML | `report.html` | Self-contained; opens in browser automatically |
| Allure | `allure-results/` | View with `allure serve allure-results` |

---

## Project Structure

```
python/
├── autqa/                  # Test framework (not tests)
│   ├── api/                # Thin API wrappers (enrollment, authentication)
│   ├── core/               # HTTP client, config, env store
│   ├── services/           # High-level operations (enrollment, auth, token)
│   └── utils/              # Logger, payload builders, CLI helpers
├── generated/              # Standalone helper scripts (token, enrollment steps)
├── samples/                # Static test data (public_key.pem, voice.b64)
├── tests/
│   ├── stateful_apis/
│   │   ├── enrollment/     # Enrollment API tests
│   │   ├── authentication/ # Authentication API tests
│   │   ├── admin/          # Admin portal config tests
│   │   ├── gallery/        # 1-to-N gallery tests
│   │   ├── re_enrollment/  # Re-enrollment tests
│   │   └── b2c/            # B2C authenticator tests
│   └── stateless_apis/
│       ├── face_liveness/  # Liveness detection tests
│       ├── face_matcher/   # 1-to-1 face comparison tests
│       └── document_verification/
├── client.py               # Standalone HTTP client (used by generated/ scripts)
├── conftest.py             # Root path setup
├── pytest.ini              # Pytest configuration and markers
└── requirements.txt
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `BASEURL` | Yes | API host (e.g. `https://qa8.awareid.com`) |
| `APIKEY` | Yes | API key sent in `apikey` header |
| `REALM_NAME` | OAuth | Keycloak realm name |
| `CLIENT_ID` | OAuth | OAuth client ID |
| `CLIENT_SECRET` | OAuth | OAuth client secret |
| `JWT` | Auto | JWT token — auto-refreshed before each run |
| `ENROLLED_USERNAME` | Some tests | Pre-enrolled user for auth tests |

> OAuth variables (`REALM_NAME`, `CLIENT_ID`, `CLIENT_SECRET`) must either all be set or all be absent. Partial configuration will cause a startup error.

---

## Known Backend Issues

These are tracked API-side bugs that block certain test groups:

- **GET `/onboarding/admin/customerConfig`** — returns duplicate JSON keys, causing a 500. Blocks ~80% of admin config tests.
- **POST `/onboarding/admin/customerConfig`** — crashes with NullPointerException. Blocks admin setting writes.

Expected pass rate once these are fixed: **95%+**.

---

## Architecture Notes

- **Token management**: `autqa/services/token_service.py` caches the OAuth JWT and refreshes it automatically on 401 responses. The `conftest.py` also proactively refreshes at session start.
- **Retry logic**: `autqa/core/http_client.py` retries 5xx errors up to 3 times with a 1s delay, and refreshes the token once on 401 before retrying.
- **Config**: All settings load from `.env` via `autqa/core/config.py`. Override the path with `ENV_FILE=/path/to/.env`.
