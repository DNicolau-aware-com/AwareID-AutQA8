"""
Pair-dataset compare tests for Face Matcher 4.0.1 upgrade validation (Santander POC106 task).

Uses images from C:\\Users\\dnicolau\\Desktop\\images:
  - Same-person pairs: 10 ' - Copy.jpg' duplicates paired with their originals
  - Different-person pairs: 80 other distinct UUID images, formed into 40 pairs

Threshold: raw score >= 4 => match (per Santander 4.0.1 acceptance criteria).
Algorithm: F500.
"""

import base64
import os
from pathlib import Path

import allure
import pytest


IMAGE_DIR = Path(r"C:\Users\dnicolau\Desktop\images")
THRESHOLD = 4.0
ALGORITHM = "F500"


def _b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _discover_pairs():
    """Return (same_person_pairs, different_person_pairs).

    same_person: [(original_path, copy_path), ...] from ' - Copy.jpg' duplicates.
    different_person: [(a_path, b_path), ...] from 80 other distinct UUID images.
    """
    if not IMAGE_DIR.is_dir():
        return [], []

    copy_files = sorted(p for p in IMAGE_DIR.glob("* - Copy.jpg"))
    same_pairs = []
    excluded = set()
    for copy_path in copy_files:
        original_name = copy_path.name.replace(" - Copy.jpg", ".jpg")
        original_path = IMAGE_DIR / original_name
        if original_path.is_file():
            same_pairs.append((original_path, copy_path))
            excluded.add(original_path.name)
            excluded.add(copy_path.name)

    all_jpgs = sorted(
        p for p in IMAGE_DIR.glob("*.jpg")
        if p.name not in excluded and " - Copy" not in p.name
    )
    diff_pool = all_jpgs[:80]
    diff_pairs = [(diff_pool[i], diff_pool[i + 1]) for i in range(0, len(diff_pool) - 1, 2)]
    return same_pairs, diff_pairs


SAME_PAIRS, DIFF_PAIRS = _discover_pairs()


def _pair_id(pair):
    return f"{pair[0].stem[:8]}__vs__{pair[1].stem[:8]}"


def _compare(api_client, base_path, probe_b64, gallery_b64):
    payload = {
        "probe": {"VISIBLE_FRONTAL": probe_b64},
        "gallery": {"VISIBLE_FRONTAL": gallery_b64},
        "workflow": {
            "comparator": {
                "algorithm": ALGORITHM,
                "faceTypes": ["VISIBLE_FRONTAL"],
            }
        },
    }
    return api_client.http_client.post(f"{base_path}/compare", json=payload)


@allure.feature("Face Matcher API")
@allure.story("Pair dataset — same-person")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.stateless
@pytest.mark.face_matcher
@pytest.mark.parametrize("pair", SAME_PAIRS, ids=[_pair_id(p) for p in SAME_PAIRS])
def test_same_person_pair_above_threshold(api_client, face_matcher_base_path, pair):
    """Same-person duplicate must score at or above threshold 4."""
    if not SAME_PAIRS:
        pytest.skip("No same-person ' - Copy.jpg' duplicates found in image dir")

    original, copy = pair
    response = _compare(api_client, face_matcher_base_path, _b64(original), _b64(copy))
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    result = response.json()
    assert "score" in result and "scorePercent" in result, f"Missing score fields: {result}"
    score = float(result["score"])
    pct = float(result["scorePercent"])
    print(f"\n[SAME] {original.name} vs {copy.name} -> score={score} pct={pct}%")
    assert score >= THRESHOLD, (
        f"Expected same-person score >= {THRESHOLD}, got score={score} ({pct}%)"
    )
    assert 0 <= pct <= 100, (
        f"scorePercent={pct} out of 0–100 range — "
        f"likely the ×100 multiplication bug (returns 0–1 instead of 0–100)"
    )
    assert pct > 80, (
        f"Same-person scorePercent={pct}% expected >80 after fix "
        f"(raw score={score})"
    )


@allure.feature("Face Matcher API")
@allure.story("Pair dataset — different-person")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.stateless
@pytest.mark.face_matcher
@pytest.mark.parametrize("pair", DIFF_PAIRS, ids=[_pair_id(p) for p in DIFF_PAIRS])
def test_different_person_pair_below_threshold(api_client, face_matcher_base_path, pair):
    """Different-person pair must score below threshold 4."""
    if not DIFF_PAIRS:
        pytest.skip("Not enough distinct UUID images for different-person pairs")

    a, b = pair
    response = _compare(api_client, face_matcher_base_path, _b64(a), _b64(b))
    if response.status_code == 500:
        try:
            err = response.json().get("error", {})
            if err.get("code") in (113, 1001, 1002):
                pytest.skip(f"Server rejected pair ({err}) — likely no-face-detected")
        except ValueError:
            pass
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    result = response.json()
    assert "score" in result and "scorePercent" in result, f"Missing score fields: {result}"
    score = float(result["score"])
    pct = float(result["scorePercent"])
    print(f"\n[DIFF] {a.name} vs {b.name} -> score={score} pct={pct}%")
    assert score < THRESHOLD, (
        f"Expected different-person score < {THRESHOLD}, got score={score} ({pct}%)"
    )
    assert 0 <= pct <= 100, (
        f"scorePercent={pct} out of 0–100 range — "
        f"likely the ×100 multiplication bug (returns 0–1 instead of 0–100)"
    )
    assert pct < 10, (
        f"Different-person scorePercent={pct}% expected <10 after fix "
        f"(raw score={score})"
    )
