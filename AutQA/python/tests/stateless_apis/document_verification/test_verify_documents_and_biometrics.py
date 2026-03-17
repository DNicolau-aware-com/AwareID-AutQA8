"""Document and biometrics verification tests.

POST /documentVerification/verifyDocumentsAndBiometrics
Verifies document OCR fields (MRZ/Barcode/Visual) and performs facial match
against the portrait extracted from the ID card.

Images sourced from .env: DAN_DOC_FRONT, DAN_DOC_BACK, FACE
"""

import pytest


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_document_and_face(
    api_client,
    doc_verification_base_path,
    document_image_base64,
    document_image_rear_base64,
    face_image_base64,
):
    """
    Positive test: submit front + back document images with a face image.
    Expects 200 with overallAuthenticationResult, documentAuthenticationResult,
    and biometricsAuthenticationResult in the response.
    """
    payload = {
        "documentsInfo": {
            "documentImage": [
                {
                    "lightingScheme": 6,
                    "image": document_image_base64,
                    "format": "jpg"
                },
                {
                    "lightingScheme": 6,
                    "image": document_image_rear_base64,
                    "format": "jpg"
                }
            ]
        },
        "biometricsInfo": {
            "facialImage": {
                "image": face_image_base64
            }
        }
    }

    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json=payload
    )

    if response.status_code == 400:
        try:
            err = response.json()
            if "base64" in err.get("errorMsg", "").lower() or err.get("errorCode") == "INVALID_INPUT":
                pytest.skip(
                    f"Document image rejected by server: {err.get('errorMsg')} — "
                    "check DAN_DOC_FRONT/DAN_DOC_BACK encoding in .env"
                )
        except Exception:
            pass

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()

    # ── Required top-level fields ──────────────────────────────────────────────
    assert "overallAuthenticationResult" in result, "Missing overallAuthenticationResult"
    assert "documentAuthenticationResult" in result, "Missing documentAuthenticationResult"
    assert "biometricsAuthenticationResult" in result, "Missing biometricsAuthenticationResult"

    assert result["overallAuthenticationResult"] in ["OK", "FAILED", "UNDEFINED"], (
        f"Unexpected overallAuthenticationResult: {result['overallAuthenticationResult']}"
    )

    # ── documentAuthenticationResult ──────────────────────────────────────────
    doc = result["documentAuthenticationResult"]
    assert "overallResult" in doc, "Missing documentAuthenticationResult.overallResult"
    assert doc["overallResult"] in ["OK", "FAILED", "UNDEFINED"], (
        f"Unexpected documentAuthenticationResult.overallResult: {doc['overallResult']}"
    )

    # ── biometricsAuthenticationResult ────────────────────────────────────────
    bio = result["biometricsAuthenticationResult"]
    assert "matchResult" in bio, "Missing biometricsAuthenticationResult.matchResult"
    assert "modality" in bio, "Missing biometricsAuthenticationResult.modality"
    assert bio["matchResult"] in ["OK", "FAILED", "UNDEFINED"], (
        f"Unexpected biometricsAuthenticationResult.matchResult: {bio['matchResult']}"
    )
    assert bio["modality"] == "FACE", (
        f"Expected modality FACE, got: {bio['modality']}"
    )

    # ── Print summary ──────────────────────────────────────────────────────────
    print(f"\nOverall Result:   {result['overallAuthenticationResult']}")
    print(f"\nDocument Authentication:")
    print(f"  Type:           {doc.get('documentType', 'N/A')}")
    print(f"  Country:        {doc.get('countryName', 'N/A')}")
    print(f"  ICAO Code:      {doc.get('icaoCode', 'N/A')}")
    print(f"  Year:           {doc.get('year', 'N/A')}")
    print(f"  Overall:        {doc.get('overallResult', 'N/A')} (score: {doc.get('overallResultScore', 'N/A')})")
    print(f"  MRZ Present:    {doc.get('mrzPresence', 'N/A')}")
    print(f"  RFID Present:   {doc.get('rfidPresence', 'N/A')}")
    print(f"\nBiometric Authentication:")
    print(f"  Match Result:   {bio.get('matchResult', 'N/A')}")
    print(f"  Match Score:    {bio.get('matchScore', 'N/A')}")
    print(f"  Modality:       {bio.get('modality', 'N/A')}")
    print(f"\nRetry Capture:    {result.get('retryDocumentCapture', 'N/A')}")
    print(f"ICAO Chip:        {result.get('icaoChipAvailable', 'N/A')}")
    print(f"ICAO Verification:{result.get('icaoVerificationResult', 'N/A')}")


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_document_front_only(
    api_client,
    doc_verification_base_path,
    document_image_base64,
    face_image_base64,
):
    """
    Submit front-only document with face image.
    Server should accept a single-image submission and return 200.
    """
    payload = {
        "documentsInfo": {
            "documentImage": [
                {
                    "lightingScheme": 6,
                    "image": document_image_base64,
                    "format": "jpg"
                }
            ]
        },
        "biometricsInfo": {
            "facialImage": {
                "image": face_image_base64
            }
        }
    }

    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json=payload
    )

    if response.status_code == 400:
        try:
            err = response.json()
            if "base64" in err.get("errorMsg", "").lower() or err.get("errorCode") == "INVALID_INPUT":
                pytest.skip(
                    f"Document image rejected by server: {err.get('errorMsg')} — "
                    "check DAN_DOC_FRONT encoding in .env"
                )
        except Exception:
            pass

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    result = response.json()
    assert "overallAuthenticationResult" in result
    assert result["overallAuthenticationResult"] in ["OK", "FAILED", "UNDEFINED"]

    print(f"\nFront-only Overall Result: {result['overallAuthenticationResult']}")
