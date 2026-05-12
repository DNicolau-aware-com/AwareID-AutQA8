"""
1:N matchFace test for Face Matcher 4.0.1 upgrade validation (Santander POC106 task).

Uses images from C:\\Users\\dnicolau\\Desktop\\images:
  - Enroll: 10 originals (have a ' - Copy.jpg' counterpart) + 80 other distinct UUID images = 90 enrollees
  - Probe : 10 ' - Copy.jpg' duplicates against the freshly-built gallery

Acceptance:
  - Each probe returns matchCount >= 1 (server threshold lets it through)
  - The top-1 candidate's registrationCode equals the original's enrolled code
"""

import base64
import uuid
from pathlib import Path

import allure
import pytest


IMAGE_DIR = Path(r"C:\Users\dnicolau\Desktop\images")
ENROLL_FILLER_COUNT = 80


def _b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _discover_dataset():
    """Return (originals, copies, filler) — paired originals/copies plus extra enrollees."""
    if not IMAGE_DIR.is_dir():
        return [], [], []

    copies = sorted(p for p in IMAGE_DIR.glob("* - Copy.jpg"))
    originals, ordered_copies = [], []
    for copy_path in copies:
        original_path = IMAGE_DIR / copy_path.name.replace(" - Copy.jpg", ".jpg")
        if original_path.is_file():
            originals.append(original_path)
            ordered_copies.append(copy_path)

    excluded = {p.name for p in originals} | {p.name for p in ordered_copies}
    filler = [
        p for p in sorted(IMAGE_DIR.glob("*.jpg"))
        if p.name not in excluded and " - Copy" not in p.name
    ][:ENROLL_FILLER_COUNT]
    return originals, ordered_copies, filler


@pytest.fixture
def populated_default(api_client, gallery_base_path):
    """Enroll 10 originals + 80 fillers into the default gallery; yield (originals, copies, code_for, all_codes)."""
    originals, copies, filler = _discover_dataset()
    if len(originals) < 10 or len(filler) < ENROLL_FILLER_COUNT:
        pytest.skip(
            f"Need >=10 paired originals and {ENROLL_FILLER_COUNT} filler images; "
            f"got originals={len(originals)} filler={len(filler)}"
        )

    code_for = {}
    all_codes = []
    enrollees = originals + filler

    for idx, path in enumerate(enrollees, 1):
        uname = f"fm41_{uuid.uuid4().hex[:8]}"
        resp = api_client.http_client.post(
            f"{gallery_base_path}/registerUser",
            json={
                "username": uname,
                "email": f"{uname}@test.aware.com",
                "image": _b64(path),
            },
        )
        if resp.status_code != 200:
            pytest.skip(
                f"registerUser failed on enrollee {idx}/{len(enrollees)} ({path.name}): "
                f"{resp.status_code} {resp.text[:200]}"
            )
        reg_code = resp.json().get("registrationCode")
        assert reg_code, f"Empty registrationCode for {path.name}"
        code_for[path] = reg_code
        all_codes.append(reg_code)

    yield originals, copies, code_for, all_codes


@allure.feature("Gallery API")
@allure.story("1-N Face Matching — 4.0.1 dataset validation")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.stateful
@pytest.mark.gallery
def test_copy_duplicates_top1_match_original(api_client, gallery_base_path, populated_default):
    """For each Copy duplicate, top-1 match (default gallery, candidateList scoped to 90 enrollees) is its original's reg code."""
    originals, copies, code_for, all_codes = populated_default

    failures = []
    for original, copy in zip(originals, copies):
        expected_code = code_for[original]
        resp = api_client.http_client.post(
            f"{gallery_base_path}/matchFace",
            json={"image": _b64(copy), "candidateList": all_codes},
        )
        if resp.status_code != 200:
            failures.append(f"{copy.name}: HTTP {resp.status_code} {resp.text[:200]}")
            continue
        result = resp.json()
        match_count = result.get("matchCount", 0)
        matches = result.get("list", [])
        if match_count < 1 or not matches:
            print(f"[1:N ZERO] {copy.name} -> matchCount={match_count} raw={result}")
            failures.append(f"{copy.name}: matchCount={match_count} body={result}")
            continue
        top = matches[0]
        top_code = top.get("registrationCode")
        print(
            f"[1:N] {copy.name} -> top_keys={list(top.keys())} top={top} "
            f"expected={expected_code} matchCount={match_count}"
        )
        if top_code != expected_code:
            failures.append(
                f"{copy.name}: top-1={top_code} top={top} expected={expected_code}"
            )

    assert not failures, "Top-1 match did not equal enrolled original for:\n  - " + "\n  - ".join(failures)
