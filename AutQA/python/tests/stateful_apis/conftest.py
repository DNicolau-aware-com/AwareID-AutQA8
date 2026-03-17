import copy
import pytest
import uuid
import time
from pathlib import Path
from dotenv import dotenv_values

ENROLLMENT_SETTINGS = {
    "add_face": True,
    "add_document": False,
    "add_voice": False,
    "add_pin": False,
    "check_device_security": False,
    "add_device": False,
    "enable_age_estimation": False,
    "prevent_duplicate_enrollments": True,
    "duplicate_face_match_threshold": 80,
    "rfid_portrait_selfie_threshold": 3,
    "ocr_portrait_selfie_threshold": 2.0,
    "document_rfid": "DISABLED",
    "max_device_ids": 3,
}

@pytest.fixture(scope="session")
def enrollment_settings():
    return ENROLLMENT_SETTINGS

@pytest.fixture(scope="session")
def env_vars():
    root = Path(__file__).resolve().parents[2]
    return dotenv_values(root / ".env")

@pytest.fixture
def unique_username():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    return f"dantest_{timestamp}_{unique_id}"[:50]

@pytest.fixture
def face_image(env_vars):
    image = (
        env_vars.get("FACE") or
        env_vars.get("DAN_FACE") or
        env_vars.get("FACE_IMAGE")
    )
    if not image:
        pytest.skip("Face image not found in .env (set FACE=<base64>)")
    if image.startswith("data:image"):
        image = image.split(",")[1]
    return image.strip()

@pytest.fixture
def face_frames(face_image):
    now_ms = int(time.time() * 1000)
    return [
        {"data": face_image, "timestamp": now_ms + (i * 30), "tags": []}
        for i in range(3)
    ]

@pytest.fixture
def workflow(env_vars):
    return env_vars.get("WORKFLOW", "charlie4")

@pytest.fixture
def enrolled_username(env_vars):
    return env_vars.get('userEnroll', 'TESTETSTETS')


# ==============================================================================
# SERVER CONFIG PRESETS
# Face settings use "reenrollment" (lowercase) — confirmed from admin tests.
# Enabling face requires 3 sequential requests (server dependency order).
# Disabling face requires all 3 flags in ONE request.
# ==============================================================================

# Preset extra settings applied ON TOP of the face-enabled baseline.
# Face enabling is always handled separately via _ensure_face_enabled().
#
# Top-level onboardingConfig fields (from API spec):
#   maxDeviceIds              — int
#   maxAuthenticationAttempts — int
#   saveToSubjectManager      — int (1 = enabled, 0 = disabled)
_CONFIG_PRESETS = {
    "enrollment_face_only": {
        "maxDeviceIds": 3,
        "maxAuthenticationAttempts": 4,
        "saveToSubjectManager": 1,
        "onboardingOptions": {
            "enrollment": {
                "addDocument": False,
                "addDevice": False,
                "ageEstimation": {
                    "enabled": False,
                    "minAge": 1,
                    "maxAge": 101,
                    "minTolerance": 0,
                    "maxTolerance": 0,
                },
            },
        },
    },
    "enrollment_with_document": {
        "maxDeviceIds": 3,
        "maxAuthenticationAttempts": 4,
        "saveToSubjectManager": 1,
        "onboardingOptions": {
            "enrollment": {
                "addDocument": True,
                "addDevice": True,
                "ageEstimation": {
                    "enabled": False,
                    "minAge": 1,
                    "maxAge": 101,
                    "minTolerance": 0,
                    "maxTolerance": 0,
                },
            },
            "document": {"rfid": "DISABLED"},
        },
    },
    "authentication_face": {
        "maxDeviceIds": 3,
        "maxAuthenticationAttempts": 4,
        "saveToSubjectManager": 1,
    },
    "re_enrollment_face": {
        "maxDeviceIds": 3,
        "maxAuthenticationAttempts": 4,
        "saveToSubjectManager": 1,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into a copy of base."""
    result = copy.deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


def _ensure_face_enabled(api_client) -> None:
    """
    Enable all face flags using the required 3-step dependency order
    (as documented in test_admin_config_dependencies.py):

      Step 1 — authentication.verifyFace = True  → POST → wait 2s
      Step 2 — reenrollment.verifyFace = True    → POST → wait 2s
      Step 3 — enrollment.addFace = True         → POST

    Note: "reenrollment" is lowercase in the API config (not camelCase).
    """
    # Step 1: authentication.verifyFace
    r = api_client.http_client.get("/onboarding/admin/customerConfig")
    c = copy.deepcopy(r.json().get("onboardingConfig", {}))
    c.setdefault("onboardingOptions", {}).setdefault("authentication", {})["verifyFace"] = True
    api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": c})
    time.sleep(2)

    # Step 2: reenrollment.verifyFace
    r = api_client.http_client.get("/onboarding/admin/customerConfig")
    c = copy.deepcopy(r.json().get("onboardingConfig", {}))
    c.setdefault("onboardingOptions", {}).setdefault("reenrollment", {})["verifyFace"] = True
    api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": c})
    time.sleep(2)

    # Step 3: enrollment.addFace
    r = api_client.http_client.get("/onboarding/admin/customerConfig")
    c = copy.deepcopy(r.json().get("onboardingConfig", {}))
    c.setdefault("onboardingOptions", {}).setdefault("enrollment", {})["addFace"] = True
    api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": c})
    time.sleep(1)


def _fix_face_constraint(api_client) -> None:
    """
    Read live config after setup. If any face flag is still False, fix it
    using the Admin API — following the pattern in test_update_config_no_restore.py.
    Never skips: always corrects before the test runs.
    """
    r = api_client.http_client.get("/onboarding/admin/customerConfig")
    opts = r.json().get("onboardingConfig", {}).get("onboardingOptions", {})

    checks = {
        "enrollment.addFace":        opts.get("enrollment", {}).get("addFace", False),
        "authentication.verifyFace": opts.get("authentication", {}).get("verifyFace", False),
        "reenrollment.verifyFace":   opts.get("reenrollment", {}).get("verifyFace", False),
    }
    violations = [k for k, v in checks.items() if not v]
    if violations:
        print(
            f"\n[CONFIG FIX] Face flags still incorrect after setup: {violations}. "
            "Re-applying 3-step enable sequence via Admin API..."
        )
        _ensure_face_enabled(api_client)


@pytest.fixture
def apply_server_config(api_client):
    """
    Fixture factory: ensures face is enabled via the 3-step admin sequence,
    then applies preset-specific extra settings, and restores original config after.

    Usage in a conftest autouse fixture:
        @pytest.fixture(autouse=True)
        def setup_config(apply_server_config):
            apply_server_config("enrollment_face_only")

    Or inline in a test to override the folder default:
        def test_something(apply_server_config):
            apply_server_config("enrollment_with_document")
    """
    original_config = None

    def _apply(preset):
        nonlocal original_config

        # Save current config for teardown restore
        resp = api_client.http_client.get("/onboarding/admin/customerConfig")
        original_config = resp.json().get("onboardingConfig", {})

        # Always enable face using the required 3-step dependency order
        _ensure_face_enabled(api_client)

        # Apply any preset-specific extra settings on top
        patch = _CONFIG_PRESETS.get(preset, {}) if isinstance(preset, str) else preset
        if patch:
            r = api_client.http_client.get("/onboarding/admin/customerConfig")
            current = r.json().get("onboardingConfig", {})
            new_config = _deep_merge(current, patch)
            api_client.http_client.post(
                "/onboarding/admin/customerConfig",
                json={"onboardingConfig": new_config},
            )
            time.sleep(0.5)

        # Verify and auto-fix face constraint — never skips, always corrects
        _fix_face_constraint(api_client)

        # Enforce: addDocument=True must always have document.rfid="DISABLED"
        r = api_client.http_client.get("/onboarding/admin/customerConfig")
        live = r.json().get("onboardingConfig", {})
        if live.get("onboardingOptions", {}).get("enrollment", {}).get("addDocument"):
            rfid = live.get("onboardingOptions", {}).get("document", {}).get("rfid")
            if rfid != "DISABLED":
                c = copy.deepcopy(live)
                c.setdefault("onboardingOptions", {}).setdefault("document", {})["rfid"] = "DISABLED"
                api_client.http_client.post(
                    "/onboarding/admin/customerConfig",
                    json={"onboardingConfig": c},
                )

    yield _apply

    # Teardown: restore original config.
    # Disable all face flags together in ONE request first (system rule),
    # then restore the full original config.
    if original_config is not None:
        r = api_client.http_client.get("/onboarding/admin/customerConfig")
        current = copy.deepcopy(r.json().get("onboardingConfig", {}))
        opts = current.setdefault("onboardingOptions", {})
        opts.setdefault("enrollment", {})["addFace"] = False
        opts.setdefault("reenrollment", {})["verifyFace"] = False
        opts.setdefault("authentication", {})["verifyFace"] = False
        api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": current},
        )
        time.sleep(1)
        api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": original_config},
        )
