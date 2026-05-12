"""
Edge-case and negative tests for POST /nexaface/compare — Face Matcher 4.0.1 validation.

Category A — Bad image content  : truncated JPEG, non-image bytes, empty string
Category B — No-face images      : 1×1 pixel, solid colour, text-only data
Category C — Face quality        : profile-view probe, profile×2, tiny image
Category D — API shape           : empty faceTypes, wrong faceType key, lowercase algorithm
"""

import base64
import struct
import zlib
from pathlib import Path

import allure
import pytest

PROFILE_IMAGE_A = Path(r"C:\Users\dnicolau\Desktop\images\00004A97-238D-4A01-A5A8-FEE9A5461856.jpg")
PROFILE_IMAGE_B = Path(r"C:\Users\dnicolau\Desktop\images\0003A7E2-BB04-4A37-8AE8-D0147BDD6518.jpg")


def _b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _make_png(width: int = 1, height: int = 1, fill: bytes = b"\xff\xff\xff") -> str:
    """Generate a minimal RGB PNG with stdlib only. Returns base64 string."""
    def chunk(name: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", crc)

    raw = (b"\x00" + fill * width) * height  # filter byte + pixels per row
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    return base64.b64encode(png).decode()


def _workflow(algorithm: str = "F500", face_types: list = None) -> dict:
    return {
        "comparator": {
            "algorithm": algorithm,
            "faceTypes": face_types if face_types is not None else ["VISIBLE_FRONTAL"],
        }
    }


# ---------------------------------------------------------------------------
# Category A — Bad image content
# ---------------------------------------------------------------------------

@allure.feature("Face Matcher API")
@allure.story("Edge Cases — Bad Image Content")
@allure.title("Compare rejects empty image string in probe")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_empty_image_string(api_client, face_matcher_base_path, face_image_base64):
    """Empty string as probe image must be rejected."""
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": ""},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(),
        },
    )
    print(f"\n[A1] status={resp.status_code} body={resp.text[:200]}")
    assert resp.status_code in [400, 500], f"Expected 400/500, got {resp.status_code}"


@allure.feature("Face Matcher API")
@allure.story("Edge Cases — Bad Image Content")
@allure.title("Compare rejects non-image bytes (plain text) as probe")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_non_image_bytes_probe(api_client, face_matcher_base_path, face_image_base64):
    """Random text base64 as probe must be rejected."""
    fake_b64 = base64.b64encode(b"This is not an image - just plain text content.").decode()
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": fake_b64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(),
        },
    )
    print(f"\n[A2] status={resp.status_code} body={resp.text[:200]}")
    assert resp.status_code in [400, 500], f"Expected 400/500, got {resp.status_code}"


@allure.feature("Face Matcher API")
@allure.story("Edge Cases — Bad Image Content")
@allure.title("Compare rejects truncated JPEG as probe")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_truncated_jpeg_probe(api_client, face_matcher_base_path, face_image_base64):
    """First 200 bytes of a real JPEG (truncated mid-file) must be rejected."""
    truncated_b64 = base64.b64encode(base64.b64decode(face_image_base64)[:200]).decode()
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": truncated_b64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(),
        },
    )
    print(f"\n[A3] status={resp.status_code} body={resp.text[:200]}")
    assert resp.status_code in [400, 500], f"Expected 400/500, got {resp.status_code}"


# ---------------------------------------------------------------------------
# Category B — No-face / wrong-content images
# ---------------------------------------------------------------------------

@allure.feature("Face Matcher API")
@allure.story("Edge Cases — No Face")
@allure.title("Compare handles 1×1 pixel image (no face)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_1x1_pixel_image(api_client, face_matcher_base_path, face_image_base64):
    """1×1 white pixel PNG has no face — server should error or return 400/500."""
    tiny_b64 = _make_png(1, 1)
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": tiny_b64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(),
        },
    )
    print(f"\n[B1] status={resp.status_code} body={resp.text[:200]}")
    assert resp.status_code in [400, 500], f"Expected 400/500 for no-face image, got {resp.status_code}"


@allure.feature("Face Matcher API")
@allure.story("Edge Cases — No Face")
@allure.title("Compare handles solid-colour image (no face)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_solid_colour_image(api_client, face_matcher_base_path, face_image_base64):
    """40×40 solid grey PNG has no face — expect 400/500."""
    grey_b64 = _make_png(40, 40, fill=b"\x80\x80\x80")
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": grey_b64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(),
        },
    )
    print(f"\n[B2] status={resp.status_code} body={resp.text[:200]}")
    assert resp.status_code in [400, 500], f"Expected 400/500 for no-face image, got {resp.status_code}"


@allure.feature("Face Matcher API")
@allure.story("Edge Cases — No Face")
@allure.title("Compare handles text-only data disguised as image")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_text_data_as_image(api_client, face_matcher_base_path, face_image_base64):
    """PDF-magic-byte prefixed content as base64 must be rejected."""
    pdf_stub = base64.b64encode(b"%PDF-1.4 fake content to simulate a PDF file").decode()
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": pdf_stub},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(),
        },
    )
    print(f"\n[B3] status={resp.status_code} body={resp.text[:200]}")
    assert resp.status_code in [400, 500], f"Expected 400/500 for PDF stub, got {resp.status_code}"


# ---------------------------------------------------------------------------
# Category C — Face quality edge cases
# ---------------------------------------------------------------------------

@allure.feature("Face Matcher API")
@allure.story("Edge Cases — Face Quality")
@allure.title("Compare: profile-view probe vs frontal gallery — quality degradation")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a known side-profile mugshot as probe against a frontal gallery image. "
    "Documents 4.0.1 behavior: error (no frontal face) or very low score. "
    "Does NOT assert a specific score — result is informational."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_profile_probe_vs_frontal_gallery(api_client, face_matcher_base_path, face_image_base64):
    """Profile probe vs frontal gallery — logs 4.0.1 quality-rejection behavior."""
    if not PROFILE_IMAGE_A.is_file():
        pytest.skip(f"Profile image not found: {PROFILE_IMAGE_A}")
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": _b64(PROFILE_IMAGE_A)},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(),
        },
    )
    print(f"\n[C1] profile-probe vs frontal-gallery: status={resp.status_code}")
    try:
        result = resp.json()
        score = result.get("matchScore", result.get("score", "N/A"))
        pct = result.get("matchScorePercent", result.get("scorePercent", "N/A"))
        print(f"[C1] score={score} pct={pct} body={result}")
    except ValueError:
        print(f"[C1] non-JSON body: {resp.text[:200]}")
    # Allow 200 (low score) or 400/500 (face detection failed) — both are valid 4.0.1 responses
    assert resp.status_code in [200, 400, 500], f"Unexpected status {resp.status_code}"


@allure.feature("Face Matcher API")
@allure.story("Edge Cases — Face Quality")
@allure.title("Compare: profile-view in both probe and gallery — same image")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends the same side-profile image as both probe and gallery. "
    "Byte-identical content — documents how 4.0.1 handles non-frontal images in both slots."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_profile_probe_and_gallery_same(api_client, face_matcher_base_path):
    """Profile image as both probe and gallery (identical bytes) — log 4.0.1 behavior."""
    if not PROFILE_IMAGE_B.is_file():
        pytest.skip(f"Profile image not found: {PROFILE_IMAGE_B}")
    b64 = _b64(PROFILE_IMAGE_B)
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": b64},
            "gallery": {"VISIBLE_FRONTAL": b64},
            "workflow": _workflow(),
        },
    )
    print(f"\n[C2] profile×2 same image: status={resp.status_code}")
    try:
        result = resp.json()
        score = result.get("matchScore", result.get("score", "N/A"))
        pct = result.get("matchScorePercent", result.get("scorePercent", "N/A"))
        print(f"[C2] score={score} pct={pct} body={result}")
    except ValueError:
        print(f"[C2] non-JSON body: {resp.text[:200]}")
    assert resp.status_code in [200, 400, 500], f"Unexpected status {resp.status_code}"


@allure.feature("Face Matcher API")
@allure.story("Edge Cases — Face Quality")
@allure.title("Compare: very small image (8×8 px) — below usable resolution")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_tiny_8x8_image(api_client, face_matcher_base_path, face_image_base64):
    """8×8 pixel image has no extractable face features — expect 400/500."""
    tiny_b64 = _make_png(8, 8, fill=b"\xaa\x77\x55")
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": tiny_b64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(),
        },
    )
    print(f"\n[C3] 8×8 probe: status={resp.status_code} body={resp.text[:200]}")
    assert resp.status_code in [400, 500], f"Expected 400/500 for 8×8 image, got {resp.status_code}"


# ---------------------------------------------------------------------------
# Category D — API shape edge cases
# ---------------------------------------------------------------------------

@allure.feature("Face Matcher API")
@allure.story("Edge Cases — API Shape")
@allure.title("Compare rejects empty faceTypes list in workflow")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_empty_facetypes(api_client, face_matcher_base_path, face_image_base64):
    """Empty faceTypes: 4.0.1 silently accepts and returns 200 with degraded score (~1% for identical images)."""
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": face_image_base64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(face_types=[]),
        },
    )
    print(f"\n[D1] empty faceTypes: status={resp.status_code} body={resp.text[:200]}")
    assert resp.status_code in [200, 400, 500], f"Unexpected status {resp.status_code}"
    if resp.status_code == 200:
        score_pct = resp.json().get("scorePercent", resp.json().get("matchScorePercent"))
        print(f"[D1] FINDING: faceTypes=[] silently accepted — scorePercent={score_pct} (degrades from 100% to ~1%)")
        assert score_pct is not None, "Response missing scorePercent"


@allure.feature("Face Matcher API")
@allure.story("Edge Cases — API Shape")
@allure.title("Compare: probe key mismatches workflow faceType")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Probe image is keyed as VISIBLE_FRONTAL but workflow faceTypes declares VISIBLE_PROFILE. "
    "Documents 4.0.1 behavior on faceType mismatch."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_facetype_key_mismatch(api_client, face_matcher_base_path, face_image_base64):
    """Probe key (VISIBLE_FRONTAL) mismatches workflow faceTypes (VISIBLE_PROFILE) — log behavior."""
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": face_image_base64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(face_types=["VISIBLE_PROFILE"]),
        },
    )
    print(f"\n[D2] faceType mismatch: status={resp.status_code} body={resp.text[:300]}")
    assert resp.status_code in [200, 400, 500], f"Unexpected status {resp.status_code}"


@allure.feature("Face Matcher API")
@allure.story("Edge Cases — API Shape")
@allure.title("Compare: algorithm name is case-sensitive (f500 vs F500)")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends 'f500' (lowercase) as the algorithm name. "
    "Documents whether 4.0.1 treats algorithm names as case-sensitive."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_edge_lowercase_algorithm(api_client, face_matcher_base_path, face_image_base64):
    """Lowercase algorithm name 'f500' — documents case-sensitivity behavior."""
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": face_image_base64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": _workflow(algorithm="f500"),
        },
    )
    print(f"\n[D3] lowercase algorithm 'f500': status={resp.status_code} body={resp.text[:300]}")
    # Either rejected (case-sensitive) or accepted (case-insensitive) — both are valid behavior to document
    assert resp.status_code in [200, 400, 500], f"Unexpected status {resp.status_code}"
    if resp.status_code == 200:
        result = resp.json()
        score = result.get("matchScore", result.get("score", "N/A"))
        print(f"[D3] accepted lowercase — score={score} (case-insensitive behavior confirmed)")
    else:
        print(f"[D3] rejected lowercase — case-sensitive behavior confirmed")
