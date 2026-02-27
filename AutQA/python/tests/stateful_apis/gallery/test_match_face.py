"""
Tests for POST /onboarding/gallery/matchFace

Performs 1-N face matching against the default or a custom gallery.
Returns a list of matched candidates with scores.

Images read from .env:
    FACE       — real face photo (positive match)
    SPOOF      — spoof/fake face (anti-spoofing probe)
    TX_DL_FACE — face cropped from a TX driver's licence (skipped if absent)

Prerequisites (run once to populate .env):
    1. pytest tests/stateful_apis/gallery/test_register_user.py::test_register_multiple_users -v
       (Populates GALLERY_REGISTRATION_CODES — required for candidateList tests)
    2. pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v
       (Populates GALLERY_NAMES — required for custom-gallery tests)
    3. pytest tests/stateful_apis/gallery/test_add_registrations_to_galleries.py -v
       (Ensures users are enrolled in the custom galleries)
"""

import uuid
import allure
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _img(env_store, key: str):
    """Read and normalise a base64 image from .env. Returns None if absent."""
    val = env_store.get(key)
    if not val:
        return None
    return val.split(",", 1)[1] if val.startswith("data:") else val


def _assert_match_structure(result):
    """Assert the standard matchFace response shape."""
    assert "matchCount" in result, f"Expected 'matchCount' in response, got: {result}"
    assert "list" in result, f"Expected 'list' in response, got: {result}"
    assert isinstance(result["matchCount"], int), "matchCount must be an integer"
    assert isinstance(result["list"], list), "list must be an array"


def _first_code(env_store):
    """Return the first registration code from .env, or None."""
    raw = env_store.get("GALLERY_REGISTRATION_CODES")
    if not raw:
        return None
    codes = [c.strip() for c in raw.split(",") if c.strip()]
    return codes[0] if codes else None


def _first_gallery(env_store):
    """Return the first custom gallery name from .env, or None."""
    raw = env_store.get("GALLERY_NAMES")
    if not raw:
        return None
    names = [n.strip() for n in raw.split(",") if n.strip()]
    return names[0] if names else None


# ---------------------------------------------------------------------------
# Group 1 — default gallery  "(default)"
# ---------------------------------------------------------------------------

@allure.feature("Gallery API")
@allure.story("1-N Face Matching — Default Gallery")
@allure.title("matchFace FACE image — default gallery, empty candidateList")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Matches the FACE image against the full default gallery (empty candidateList = no restriction). "
    "Expects HTTP 200 and a valid response structure."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_default_face_empty_candidate_list(api_client, gallery_base_path, env_store):
    """FACE image, default gallery, candidateList=[] (match all)."""
    image = _img(env_store, "FACE")
    if not image:
        pytest.skip("FACE not found in .env")

    response = api_client.http_client.post(
        f"{gallery_base_path}/matchFace",
        json={"image": image, "candidateList": []},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    _assert_match_structure(response.json())
    print(f"\n[OK] Default gallery / FACE / empty candidateList → {response.json()['matchCount']} match(es)")


@allure.feature("Gallery API")
@allure.story("1-N Face Matching — Default Gallery")
@allure.title("matchFace FACE image — default gallery, candidateList from .env")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Matches the FACE image against a single registration code from GALLERY_REGISTRATION_CODES. "
    "Expects HTTP 200 and all returned candidates to match the provided code."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_default_face_with_candidate(api_client, gallery_base_path, env_store):
    """FACE image, default gallery, candidateList=[reg_code from .env]."""
    image = _img(env_store, "FACE")
    if not image:
        pytest.skip("FACE not found in .env")

    reg_code = _first_code(env_store)
    if not reg_code:
        pytest.skip(
            "GALLERY_REGISTRATION_CODES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_register_user.py"
            "::test_register_multiple_users -v"
        )

    response = api_client.http_client.post(
        f"{gallery_base_path}/matchFace",
        json={"image": image, "candidateList": [reg_code]},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    result = response.json()
    _assert_match_structure(result)

    for candidate in result["list"]:
        assert candidate.get("registrationCode") == reg_code, (
            f"Expected only {reg_code} in result, got {candidate.get('registrationCode')}"
        )

    print(f"\n[OK] Default gallery / FACE / candidateList=[{reg_code}] → {result['matchCount']} match(es)")


@allure.feature("Gallery API")
@allure.story("1-N Face Matching — Default Gallery")
@allure.title("matchFace SPOOF image — default gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Matches the SPOOF image against the default gallery. "
    "Expects HTTP 200 and a valid response structure. "
    "Score results are logged but not strictly asserted (server threshold may vary)."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_default_spoof_image(api_client, gallery_base_path, env_store):
    """SPOOF image, default gallery."""
    image = _img(env_store, "SPOOF")
    if not image:
        pytest.skip("SPOOF not found in .env")

    response = api_client.http_client.post(
        f"{gallery_base_path}/matchFace",
        json={"image": image},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    result = response.json()
    _assert_match_structure(result)
    print(f"\n[OK] Default gallery / SPOOF → {result['matchCount']} match(es)")
    if result["list"]:
        top = result["list"][0]
        print(f"     Top candidate score: {top.get('scorePercent', top.get('score', 'N/A'))}%")


@allure.feature("Gallery API")
@allure.story("1-N Face Matching — Default Gallery")
@allure.title("matchFace TX_DL_FACE image — default gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Matches the TX_DL_FACE (face cropped from a TX driver's licence) against the default gallery. "
    "Skipped if TX_DL_FACE is not present in .env. "
    "Expects HTTP 200 and a valid response structure."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_default_tx_dl_face(api_client, gallery_base_path, env_store):
    """TX_DL_FACE image, default gallery (skipped if key absent in .env)."""
    image = _img(env_store, "TX_DL_FACE")
    if not image:
        pytest.skip("TX_DL_FACE not found in .env — add it to run this test")

    response = api_client.http_client.post(
        f"{gallery_base_path}/matchFace",
        json={"image": image},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    result = response.json()
    _assert_match_structure(result)
    print(f"\n[OK] Default gallery / TX_DL_FACE → {result['matchCount']} match(es)")


# ---------------------------------------------------------------------------
# Group 2 — custom gallery from .env  (GALLERY_NAMES[0])
# ---------------------------------------------------------------------------

@allure.feature("Gallery API")
@allure.story("1-N Face Matching — Custom Gallery")
@allure.title("matchFace FACE image — custom gallery, empty candidateList")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Matches the FACE image against the first custom gallery in GALLERY_NAMES "
    "with an empty candidateList (match all enrolled users). "
    "Expects HTTP 200 and a valid response structure."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_custom_gallery_face_empty_candidate_list(api_client, gallery_base_path, env_store):
    """FACE image, custom gallery from .env, candidateList=[]."""
    image = _img(env_store, "FACE")
    if not image:
        pytest.skip("FACE not found in .env")

    gallery_name = _first_gallery(env_store)
    if not gallery_name:
        pytest.skip(
            "GALLERY_NAMES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v"
        )

    response = api_client.http_client.post(
        f"{gallery_base_path}/matchFace",
        json={"image": image, "galleryName": gallery_name, "candidateList": []},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    _assert_match_structure(response.json())
    print(f"\n[OK] Custom '{gallery_name}' / FACE / empty candidateList → {response.json()['matchCount']} match(es)")


@allure.feature("Gallery API")
@allure.story("1-N Face Matching — Custom Gallery")
@allure.title("matchFace FACE image — custom gallery, candidateList from .env")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Matches the FACE image against a specific registration code within the first custom gallery. "
    "Expects HTTP 200 and all returned candidates to match the provided code."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_custom_gallery_face_with_candidate(api_client, gallery_base_path, env_store):
    """FACE image, custom gallery from .env, candidateList=[reg_code from .env]."""
    image = _img(env_store, "FACE")
    if not image:
        pytest.skip("FACE not found in .env")

    gallery_name = _first_gallery(env_store)
    if not gallery_name:
        pytest.skip(
            "GALLERY_NAMES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v"
        )

    reg_code = _first_code(env_store)
    if not reg_code:
        pytest.skip(
            "GALLERY_REGISTRATION_CODES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_register_user.py"
            "::test_register_multiple_users -v"
        )

    response = api_client.http_client.post(
        f"{gallery_base_path}/matchFace",
        json={"image": image, "galleryName": gallery_name, "candidateList": [reg_code]},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    result = response.json()
    _assert_match_structure(result)

    for candidate in result["list"]:
        assert candidate.get("registrationCode") == reg_code, (
            f"Expected only {reg_code} in result, got {candidate.get('registrationCode')}"
        )

    print(f"\n[OK] Custom '{gallery_name}' / FACE / candidateList=[{reg_code}] → {result['matchCount']} match(es)")


@allure.feature("Gallery API")
@allure.story("1-N Face Matching — Custom Gallery")
@allure.title("matchFace SPOOF image — custom gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Matches the SPOOF image against the first custom gallery in GALLERY_NAMES. "
    "Expects HTTP 200 and a valid response structure."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_custom_gallery_spoof_image(api_client, gallery_base_path, env_store):
    """SPOOF image, custom gallery from .env."""
    image = _img(env_store, "SPOOF")
    if not image:
        pytest.skip("SPOOF not found in .env")

    gallery_name = _first_gallery(env_store)
    if not gallery_name:
        pytest.skip(
            "GALLERY_NAMES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v"
        )

    response = api_client.http_client.post(
        f"{gallery_base_path}/matchFace",
        json={"image": image, "galleryName": gallery_name},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    result = response.json()
    _assert_match_structure(result)
    print(f"\n[OK] Custom '{gallery_name}' / SPOOF → {result['matchCount']} match(es)")
    if result["list"]:
        top = result["list"][0]
        print(f"     Top candidate score: {top.get('scorePercent', top.get('score', 'N/A'))}%")


@allure.feature("Gallery API")
@allure.story("1-N Face Matching — Custom Gallery")
@allure.title("matchFace TX_DL_FACE image — custom gallery")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Matches the TX_DL_FACE image against the first custom gallery in GALLERY_NAMES. "
    "Skipped if TX_DL_FACE is not present in .env. "
    "Expects HTTP 200 and a valid response structure."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_custom_gallery_tx_dl_face(api_client, gallery_base_path, env_store):
    """TX_DL_FACE image, custom gallery from .env (skipped if key absent in .env)."""
    image = _img(env_store, "TX_DL_FACE")
    if not image:
        pytest.skip("TX_DL_FACE not found in .env — add it to run this test")

    gallery_name = _first_gallery(env_store)
    if not gallery_name:
        pytest.skip(
            "GALLERY_NAMES not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_list_gallery.py::test_list_gallery -v"
        )

    response = api_client.http_client.post(
        f"{gallery_base_path}/matchFace",
        json={"image": image, "galleryName": gallery_name},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    result = response.json()
    _assert_match_structure(result)
    print(f"\n[OK] Custom '{gallery_name}' / TX_DL_FACE → {result['matchCount']} match(es)")


# ---------------------------------------------------------------------------
# Structural / negative tests
# ---------------------------------------------------------------------------

@allure.feature("Gallery API")
@allure.story("1-N Face Matching")
@allure.title("matchFace in brand-new empty gallery returns matchCount == 0")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Creates a fresh empty gallery and performs a match against it. "
    "Expects HTTP 200 and matchCount == 0. Temporary gallery is deleted after the test."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_empty_custom_gallery(api_client, gallery_base_path, env_store):
    """Match against a brand-new empty gallery returns zero results."""
    image = _img(env_store, "FACE")
    if not image:
        pytest.skip("FACE not found in .env")

    fresh_gallery = f"test_gallery_{uuid.uuid4().hex[:8]}"

    create_resp = api_client.http_client.post(
        f"{gallery_base_path}/addGallery",
        json={"galleryName": fresh_gallery},
    )
    if create_resp.status_code != 200:
        pytest.skip(
            f"Could not create temporary gallery '{fresh_gallery}' "
            f"({create_resp.status_code}): {create_resp.text[:200]}"
        )

    print(f"\n[INFO] Matching FACE against fresh empty gallery '{fresh_gallery}'")

    try:
        response = api_client.http_client.post(
            f"{gallery_base_path}/matchFace",
            json={"image": image, "galleryName": fresh_gallery},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        result = response.json()
        assert "matchCount" in result
        assert result["matchCount"] == 0, (
            f"Expected 0 matches in an empty gallery, got {result['matchCount']}"
        )
        print(f"\n[OK] Empty gallery match returned 0 results as expected")
    finally:
        api_client.http_client.post(
            f"{gallery_base_path}/deleteGallery",
            json={"galleryName": fresh_gallery},
        )
        print(f"[CLEANUP] Temporary gallery '{fresh_gallery}' deleted")


@allure.feature("Gallery API")
@allure.story("1-N Face Matching - Negative")
@allure.title("matchFace rejects request with missing image")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a matchFace request without the required 'image' field. "
    "Expects HTTP 400 or 500."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_match_face_missing_image(api_client, gallery_base_path):
    """Negative: missing image field."""
    response = api_client.http_client.post(
        f"{gallery_base_path}/matchFace",
        json={},
    )

    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )
    print(f"\n[OK] Missing image correctly rejected with status {response.status_code}")
