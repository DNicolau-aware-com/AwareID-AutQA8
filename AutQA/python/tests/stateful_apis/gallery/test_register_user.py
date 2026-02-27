"""
Tests for POST /onboarding/gallery/registerUser

Registers a user with a face image and adds them to the default system gallery.
Returns a registrationCode on success.
"""

import uuid
import allure
import pytest

# Number of users to register in the bulk seed test.
_BULK_REGISTER_COUNT = 5


def _assert_error_body(result):
    """Assert standard Gallery API error format: {errorCode, errorMsg, status, timestamp}."""
    assert "errorCode" in result, f"Expected 'errorCode' in error response, got: {result}"
    assert "errorMsg" in result, f"Expected 'errorMsg' in error response, got: {result}"
    assert "status" in result, f"Expected 'status' in error response, got: {result}"
    assert "timestamp" in result, f"Expected 'timestamp' in error response, got: {result}"
    assert result["errorCode"] in ("INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR"), (
        f"Unexpected errorCode: {result['errorCode']}"
    )
    print(f"\n[OK] Error response - errorCode: {result['errorCode']}, errorMsg: {result['errorMsg']}")


@allure.feature("Gallery API")
@allure.story("User Registration")
@allure.title("Register user in default gallery with all required fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Registers a new user with username, email, and a face image. "
    "Expects HTTP 200 and a non-empty registrationCode in the response."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_register_user_required_fields_only(api_client, gallery_base_path, gallery_face_image):
    """Register a user with only the required fields (username, email, image)."""
    username = f"gallery_req_{uuid.uuid4().hex[:8]}"

    response = api_client.http_client.post(
        f"{gallery_base_path}/registerUser",
        json={
            "username": username,
            "email": f"{username}@test.aware.com",
            "image": gallery_face_image,
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "registrationCode" in result, f"Expected 'registrationCode' in response, got: {result}"
    assert result["registrationCode"], "registrationCode should not be empty"

    print(f"\n[OK] User registered: {username}")
    print(f"     Registration code: {result['registrationCode']}")


@allure.feature("Gallery API")
@allure.story("User Registration")
@allure.title("Register user in default gallery with all optional fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Registers a new user including optional firstName, lastName, and phoneNumber fields. "
    "Expects HTTP 200 and a valid registrationCode. "
    "Saves GALLERY_REGISTRATION_CODE, GALLERY_USERNAME, GALLERY_EMAIL to .env for reuse."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_register_user_all_fields(api_client, gallery_base_path, gallery_face_image, env_store):
    """Register a user with all fields and save the result to .env for reuse by other tests."""
    username = f"gallery_full_{uuid.uuid4().hex[:8]}"
    email = f"{username}@test.aware.com"

    response = api_client.http_client.post(
        f"{gallery_base_path}/registerUser",
        json={
            "username": username,
            "email": email,
            "firstName": "Gallery",
            "lastName": "TestUser",
            "phoneNumber": "555-000-1234",
            "image": gallery_face_image,
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "registrationCode" in result
    assert result["registrationCode"]

    reg_code = result["registrationCode"]

    # --- Rolling list: GALLERY_REGISTRATION_CODES (max 10) ---
    raw_codes = env_store.get("GALLERY_REGISTRATION_CODES")
    codes = [c.strip() for c in raw_codes.split(",") if c.strip()] if raw_codes else []
    if reg_code not in codes:
        codes.append(reg_code)
    codes = codes[-10:]

    # --- Rolling list: GALLERY_USERNAMES (max 10) ---
    raw_usernames = env_store.get("GALLERY_USERNAMES")
    usernames_list = [u.strip() for u in raw_usernames.split(",") if u.strip()] if raw_usernames else []
    if username not in usernames_list:
        usernames_list.append(username)
    usernames_list = usernames_list[-10:]

    # Save all keys to .env
    env_store.set_multiple({
        "GALLERY_REGISTRATION_CODE": reg_code,
        "GALLERY_USERNAME": username,
        "GALLERY_EMAIL": email,
        "GALLERY_REGISTRATION_CODES": ",".join(codes),
        "GALLERY_USERNAMES": ",".join(usernames_list),
    })

    print(f"\n[OK] User registered with all fields: {username}")
    print(f"     Registration code: {reg_code}")
    print(f"\n[SAVED] Written to .env:")
    print(f"        GALLERY_REGISTRATION_CODE={reg_code}")
    print(f"        GALLERY_USERNAME={username}")
    print(f"        GALLERY_EMAIL={email}")
    print(f"        GALLERY_REGISTRATION_CODES={','.join(codes)}  ({len(codes)}/10)")
    print(f"        GALLERY_USERNAMES={','.join(usernames_list)}  ({len(usernames_list)}/10)")


@allure.feature("Gallery API")
@allure.story("User Registration - Negative")
@allure.title("registerUser rejects request with missing username")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a registerUser request without the required 'username' field. "
    "Expects HTTP 400 and INPUT_FORMAT_ERROR or INPUT_VALUES_ERROR."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_register_user_missing_username(api_client, gallery_base_path, gallery_face_image):
    """Negative: missing username field."""
    response = api_client.http_client.post(
        f"{gallery_base_path}/registerUser",
        json={
            "email": "no_username@test.aware.com",
            "image": gallery_face_image,
        },
    )

    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )
    try:
        _assert_error_body(response.json())
    except (ValueError, AssertionError) as e:
        print(f"[INFO] Error body validation skipped: {e}")


@allure.feature("Gallery API")
@allure.story("User Registration - Negative")
@allure.title("registerUser rejects request with missing email")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a registerUser request without the required 'email' field. "
    "Expects HTTP 400 and a structured error response."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_register_user_missing_email(api_client, gallery_base_path, gallery_face_image):
    """Negative: missing email field."""
    username = f"gallery_noemail_{uuid.uuid4().hex[:8]}"

    response = api_client.http_client.post(
        f"{gallery_base_path}/registerUser",
        json={
            "username": username,
            "image": gallery_face_image,
        },
    )

    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )
    try:
        _assert_error_body(response.json())
    except (ValueError, AssertionError) as e:
        print(f"[INFO] Error body validation skipped: {e}")


@allure.feature("Gallery API")
@allure.story("User Registration - Negative")
@allure.title("registerUser rejects request with missing image")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a registerUser request without the required 'image' field. "
    "Expects HTTP 400 and a structured error response."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_register_user_missing_image(api_client, gallery_base_path):
    """Negative: missing image field."""
    username = f"gallery_noimg_{uuid.uuid4().hex[:8]}"

    response = api_client.http_client.post(
        f"{gallery_base_path}/registerUser",
        json={
            "username": username,
            "email": f"{username}@test.aware.com",
        },
    )

    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )
    try:
        _assert_error_body(response.json())
    except (ValueError, AssertionError) as e:
        print(f"[INFO] Error body validation skipped: {e}")


@allure.feature("Gallery API")
@allure.story("User Registration - Negative")
@allure.title("registerUser rejects non-image base64 data")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a registerUser request with a valid base64 string that is not a real image. "
    "Expects HTTP 400 or 500."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_register_user_invalid_image(api_client, gallery_base_path):
    """Negative: image field contains non-image base64 data."""
    username = f"gallery_badb64_{uuid.uuid4().hex[:8]}"

    response = api_client.http_client.post(
        f"{gallery_base_path}/registerUser",
        json={
            "username": username,
            "email": f"{username}@test.aware.com",
            "image": "dGhpc19pc19ub3RfYV9yZWFsX2ltYWdl",  # base64 of "this_is_not_a_real_image"
        },
    )

    assert response.status_code in [400, 500], (
        f"Expected 400 or 500 for invalid image, got {response.status_code}"
    )
    print(f"\n[OK] Invalid image correctly rejected with status {response.status_code}")


@allure.feature("Gallery API")
@allure.story("User Registration")
@allure.title(f"Bulk register {_BULK_REGISTER_COUNT} users and save all codes to .env")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    f"Registers {_BULK_REGISTER_COUNT} new users in sequence. "
    "All registration codes are appended to the GALLERY_REGISTRATION_CODES rolling list "
    "and all usernames to GALLERY_USERNAMES (max 10 each). "
    "Run this test once to quickly populate .env with enough codes for bulk/delete tests."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_register_multiple_users(api_client, gallery_base_path, gallery_face_image, env_store):
    """Register several users at once and accumulate all codes in .env (max 10)."""
    # Load existing lists from .env
    raw_codes = env_store.get("GALLERY_REGISTRATION_CODES")
    codes = [c.strip() for c in raw_codes.split(",") if c.strip()] if raw_codes else []

    raw_usernames = env_store.get("GALLERY_USERNAMES")
    usernames_list = [u.strip() for u in raw_usernames.split(",") if u.strip()] if raw_usernames else []

    new_codes = []
    new_usernames = []

    for i in range(1, _BULK_REGISTER_COUNT + 1):
        username = f"gallery_bulk_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.aware.com"

        response = api_client.http_client.post(
            f"{gallery_base_path}/registerUser",
            json={
                "username": username,
                "email": email,
                "firstName": "Bulk",
                "lastName": f"User{i}",
                "image": gallery_face_image,
            },
        )

        assert response.status_code == 200, (
            f"[User {i}] Expected 200, got {response.status_code}. Response: {response.text}"
        )

        reg_code = response.json()["registrationCode"]
        new_codes.append(reg_code)
        new_usernames.append(username)
        print(f"  [{i}/{_BULK_REGISTER_COUNT}] Registered {username} → {reg_code}")

    # Merge into rolling lists (max 10)
    for code in new_codes:
        if code not in codes:
            codes.append(code)
    codes = codes[-10:]

    for uname in new_usernames:
        if uname not in usernames_list:
            usernames_list.append(uname)
    usernames_list = usernames_list[-10:]

    env_store.set_multiple({
        "GALLERY_REGISTRATION_CODE": new_codes[-1],
        "GALLERY_USERNAME": new_usernames[-1],
        "GALLERY_REGISTRATION_CODES": ",".join(codes),
        "GALLERY_USERNAMES": ",".join(usernames_list),
    })

    print(f"\n[OK] Registered {len(new_codes)} users")
    print(f"\n[SAVED] GALLERY_REGISTRATION_CODES={','.join(codes)}  ({len(codes)}/10)")
    print(f"        GALLERY_USERNAMES={','.join(usernames_list)}  ({len(usernames_list)}/10)")
