"""
Gallery size / FPIR conversion tests — Face Matcher 4.0.1 validation.

Tests the FMR→FPIR score conversion introduced in 4.0.1 per ticket:
  "1:N searches should have scores reduced by ~1 per order of magnitude in the gallery"
  Special case: gallerySize == 1 must NOT apply conversion.

Covers:
  1. /nexaface/processScores endpoint — discovery + gallery size sweep
  2. /nexaface/compare — confirm FPIR conversion is NOT applied on 1:1
  3. Isolation test — same input score, different gallery sizes: verify ~1/decade reduction
"""

import allure
import pytest


KNOWN_SAME_PERSON_SCORE = None   # populated at runtime from /compare
PROCESS_SCORES_BASE = "/facematch"
PROCESS_SCORES_PATH = "/facematch/processScores"
GALLERY_SIZES = [1, 10, 100, 1_000, 10_000, 100_000]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compare_same_person(api_client, base_path, face_b64):
    """Return (score, scorePercent) for identical-image 1:1 compare."""
    resp = api_client.http_client.post(
        f"{base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": face_b64},
            "gallery": {"VISIBLE_FRONTAL": face_b64},
            "workflow": {"comparator": {"algorithm": "F500", "faceTypes": ["VISIBLE_FRONTAL"]}},
        },
    )
    assert resp.status_code == 200, f"compare failed: {resp.status_code} {resp.text[:200]}"
    result = resp.json()
    return result.get("score", result.get("matchScore")), result.get("scorePercent", result.get("matchScorePercent"))


def _process_scores(api_client, scores, gallery_size):
    """Call POST /facematch/processScores and return raw response."""
    return api_client.http_client.post(
        PROCESS_SCORES_PATH,
        json={"scores": scores, "gallerySize": gallery_size},
    )


# ---------------------------------------------------------------------------
# 1. /processScores — endpoint discovery
# ---------------------------------------------------------------------------

@allure.feature("Face Matcher API")
@allure.story("Gallery Size — processScores")
@allure.title("Discover whether /processScores endpoint exists on 4.0.1")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_process_scores_endpoint_exists(api_client, face_matcher_base_path):
    """Probe /processScores with a known score and gallerySize=1000. Fail if 404."""
    resp = _process_scores(api_client, scores=[26.0], gallery_size=1000)
    print(f"\n[processScores] status={resp.status_code} body={resp.text[:300]}")
    assert resp.status_code != 404, (
        "/processScores returned 404 — endpoint not deployed on this build"
    )
    assert resp.status_code in [200, 400, 500], f"Unexpected status {resp.status_code}"


# ---------------------------------------------------------------------------
# 2. /processScores — gallerySize == 1 special case (no conversion)
# ---------------------------------------------------------------------------

@allure.feature("Face Matcher API")
@allure.story("Gallery Size — processScores")
@allure.title("processScores gallerySize=1 must not convert (special case)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Per ticket: gallerySize == 1 must skip ConvertFmrScoreToFpirScore. "
    "Output score must equal input score."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_process_scores_gallery_size_1_no_conversion(api_client, face_matcher_base_path):
    """gallerySize=1 → output score must equal input score (no FPIR conversion)."""
    input_score = 26.0
    resp = _process_scores(api_client, scores=[input_score], gallery_size=1)
    if resp.status_code == 404:
        pytest.skip("/processScores not available on this build")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"

    result = resp.json()
    print(f"\n[gallerySize=1] input={input_score} response={result}")
    output_scores = result.get("scores", result.get("convertedScores", [result.get("score")]))
    assert output_scores, f"No scores in response: {result}"
    output = float(output_scores[0])
    assert output == pytest.approx(input_score, abs=0.01), (
        f"gallerySize=1 special case FAILED: input={input_score} output={output} "
        f"(ConvertFmrScoreToFpirScore was called when it should have been skipped)"
    )
    print(f"[OK] gallerySize=1 special case: score unchanged {input_score} → {output}")


# ---------------------------------------------------------------------------
# 3. /processScores — gallery size sweep (~1 reduction per decade)
# ---------------------------------------------------------------------------

@allure.feature("Face Matcher API")
@allure.story("Gallery Size — processScores")
@allure.title("processScores score decreases ~1 per order of magnitude")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Sends the same input score through processScores at sizes 1, 10, 100, 1000, 10000, 100000. "
    "Per ticket, each 10× increase in gallery size should reduce the score by ~1. "
    "Asserts monotonic decrease and roughly 1-point drop per decade."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
@pytest.mark.parametrize("gallery_size", GALLERY_SIZES)
def test_process_scores_gallery_size_sweep(api_client, face_matcher_base_path, gallery_size):
    """Score reduces by ~1 for each 10× increase in gallery size."""
    input_score = 26.0
    resp = _process_scores(api_client, scores=[input_score], gallery_size=gallery_size)
    if resp.status_code == 404:
        pytest.skip("/processScores not available on this build")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"

    result = resp.json()
    output_scores = result.get("scores", result.get("convertedScores", [result.get("score")]))
    assert output_scores, f"No scores in response: {result}"
    output = float(output_scores[0])

    import math
    if gallery_size == 1:
        expected = input_score
        tolerance = 0.01
    else:
        decades = math.log10(gallery_size)
        expected = input_score - decades
        tolerance = 0.5  # allow ±0.5 around the ~1/decade formula

    print(
        f"\n[sweep] gallerySize={gallery_size:>7} → input={input_score} "
        f"output={output:.4f} expected≈{expected:.2f}"
    )
    assert output == pytest.approx(expected, abs=tolerance), (
        f"Gallery size {gallery_size}: expected score≈{expected:.2f} (±{tolerance}), got {output:.4f}"
    )


# ---------------------------------------------------------------------------
# 4. /compare — FPIR must NOT be applied on 1:1 (score percent should be high)
# ---------------------------------------------------------------------------

@allure.feature("Face Matcher API")
@allure.story("Gallery Size — compare 1:1")
@allure.title("compare 1:1 identical images: scorePercent must NOT be FPIR-converted")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Byte-identical probe and gallery — same person, guaranteed match. "
    "scorePercent should be high (>80). If it returns 1%, "
    "FPIR conversion is bleeding into the 1:1 path (bug). "
    "Raw score is also logged for reference."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_1to1_score_percent_not_fpir_converted(api_client, face_matcher_base_path, face_image_base64):
    """1:1 identical images — scorePercent must be >80%, not FPIR-degraded."""
    raw_score, score_pct = _compare_same_person(api_client, face_matcher_base_path, face_image_base64)
    print(f"\n[1:1] score={raw_score} scorePercent={score_pct}%")
    assert score_pct > 80, (
        f"scorePercent={score_pct}% on identical 1:1 images — "
        f"FPIR conversion is incorrectly applied to /compare (expected >80%). "
        f"Raw score={raw_score}. Check gallerySize==1 special case in FaceMatcher2RestServer.cpp."
    )


# ---------------------------------------------------------------------------
# 5. /compare — explicit gallerySize in workflow (does it change behaviour?)
# ---------------------------------------------------------------------------

@allure.feature("Face Matcher API")
@allure.story("Gallery Size — compare 1:1")
@allure.title("compare accepts gallerySize in workflow and uses it correctly")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends gallerySize=1 explicitly inside the workflow block. "
    "If the server reads this field, scorePercent should be unaffected (special case). "
    "Documents whether /compare honours a client-supplied gallerySize."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
@pytest.mark.parametrize("gallery_size", [1, 1000])
def test_compare_with_explicit_gallery_size(api_client, face_matcher_base_path, face_image_base64, gallery_size):
    """Pass gallerySize in workflow — observe if scorePercent changes."""
    resp = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={
            "probe": {"VISIBLE_FRONTAL": face_image_base64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": {
                "comparator": {
                    "algorithm": "F500",
                    "faceTypes": ["VISIBLE_FRONTAL"],
                    "gallerySize": gallery_size,
                }
            },
        },
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    result = resp.json()
    raw = result.get("score", result.get("matchScore"))
    pct = result.get("scorePercent", result.get("matchScorePercent"))
    print(f"\n[compare gallerySize={gallery_size}] score={raw} scorePercent={pct}%")
    assert raw is not None and pct is not None, f"Missing score fields in response: {result}"
