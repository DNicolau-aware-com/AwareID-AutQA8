"""
Comprehensive Document Verification Test Suite
Tests each validation parameter separately based on API specification
"""
import pytest
import copy
import time
import logging
from datetime import datetime
from autqa.utils.your_document_validator import (
    extract_document_ocr_data, 
    validate_document, 
    generate_document_report
)

logger = logging.getLogger(__name__)


def normalize_base64(data: str) -> str:
    """Remove data URI prefix if present"""
    if not data:
        return data
    data = data.strip()
    if data.startswith('data:') and ',' in data:
        data = data.split(',', 1)[1]
    return data


# ============================================================================
# TEST 1: DOCUMENT VERIFICATION RESULT
# ============================================================================
@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.document
class TestDocumentVerificationResult:
    """
    Test: documentVerificationResult field
    Expected: true for valid document, false for invalid
    """
    
    def test_valid_document_returns_true(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Valid document should return documentVerificationResult: true"""
        
        caplog.set_level(logging.INFO)
        
        # Get images
        face_image = normalize_base64(env_vars.get("FACE", "").strip())
        doc_front = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        doc_back = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not face_image or not doc_front:
            pytest.skip("Missing FACE or DAN_DOC_FRONT")
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Document Verification Result (Valid Document)")
        logger.info("="*120)
        
        # Setup
        self._setup_config(api_client)
        enrollment_token = self._enroll_user(api_client, unique_username, env_vars)
        self._add_face(api_client, enrollment_token, unique_username, workflow, face_frames)
        
        # Add Document
        logger.info("\n📄 Adding VALID document...")
        doc_response = self._add_document(api_client, enrollment_token, doc_front, doc_back)
        doc_data = doc_response.json()
        
        # Extract and validate
        extracted_data = extract_document_ocr_data(doc_data)
        validation_result = validate_document(extracted_data)
        
        # Log report
        logger.info(generate_document_report(extracted_data, validation_result))
        
        # ASSERTIONS
        logger.info("\n" + "="*120)
        logger.info("🔍 VERIFICATION:")
        logger.info("="*120)
        
        doc_verification = doc_data.get("documentVerificationResult")
        logger.info(f"documentVerificationResult: {doc_verification}")
        
        assert doc_verification == True, f"Expected documentVerificationResult=true, got {doc_verification}"
        logger.info("✅ Document verification returned TRUE as expected")
    
    def _setup_config(self, api_client):
        """Configure admin for document enrollment"""
        config_resp = api_client.http_client.get("/onboarding/admin/customerConfig")
        config = copy.deepcopy(config_resp.json().get("onboardingConfig", {}))
        
        enrollment = config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment['addDocument'] = True
        enrollment['addFace'] = True
        enrollment['addDevice'] = False
        
        doc_settings = config.setdefault("onboardingOptions", {}).setdefault("document", {})
        doc_settings['rfid'] = "DISABLED"
        
        api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": config})
        time.sleep(1)
    
    def _enroll_user(self, api_client, username, env_vars):
        """Enroll user and return token"""
        resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": username,
            "email": env_vars.get("EMAIL") or f"{username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Test",
            "lastName": env_vars.get("LASTNAME") or "User",
        })
        time.sleep(1)
        return resp.json().get("enrollmentToken")
    
    def _add_face(self, api_client, token, username, workflow, frames):
        """Add face biometric"""
        api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": username},
                    "workflow_data": {"workflow": workflow, "frames": frames},
                },
            },
        })
        time.sleep(3)
    
    def _add_document(self, api_client, token, front, back):
        """Add document OCR"""
        doc_images = [{"lightingScheme": 6, "image": front, "format": "JPG"}]
        if back:
            doc_images.append({"lightingScheme": 6, "image": back, "format": "JPG"})
        
        payload = {
            "enrollmentToken": token,
            "documentsInfo": {
                "documentImage": doc_images,
                "documentPayload": {"request": {"vendor": "REGULA", "data": {}}}
            }
        }
        
        return api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json=payload)


# ============================================================================
# TEST 2: MATCH RESULT (Face vs Document Photo)
# ============================================================================
@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.document
class TestDocumentFaceMatch:
    """
    Test: matchResult and matchScore fields
    Expected: matchResult=true, matchScore > threshold
    Verifies selfie matches portrait on document
    """
    
    def test_face_matches_document_photo(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Face should match document photo"""
        
        caplog.set_level(logging.INFO)
        
        face_image = normalize_base64(env_vars.get("FACE", "").strip())
        doc_front = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        doc_back = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not face_image or not doc_front:
            pytest.skip("Missing FACE or DAN_DOC_FRONT")
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Face Match (Selfie vs Document Photo)")
        logger.info("="*120)
        
        # Setup and enroll
        helper = TestHelper(api_client, env_vars)
        helper.setup_config()
        token = helper.enroll_user(unique_username)
        helper.add_face(token, unique_username, workflow, face_frames)
        
        # Add document
        logger.info("\n📄 Adding document for face match verification...")
        doc_resp = helper.add_document(token, doc_front, doc_back)
        doc_data = doc_resp.json()
        
        # ASSERTIONS
        logger.info("\n" + "="*120)
        logger.info("🔍 FACE MATCH VERIFICATION:")
        logger.info("="*120)
        
        match_result = doc_data.get("matchResult")
        match_score = doc_data.get("matchScore")
        
        logger.info(f"matchResult: {match_result}")
        logger.info(f"matchScore: {match_score}")
        
        assert match_result is not None, "matchResult field missing"
        assert match_score is not None, "matchScore field missing"
        
        if match_result == True:
            logger.info(f"✅ Face MATCHES document photo (score: {match_score})")
        else:
            logger.error(f"❌ Face DOES NOT MATCH document photo (score: {match_score})")
            pytest.fail(f"Face match failed: matchResult={match_result}, matchScore={match_score}")


# ============================================================================
# TEST 3: ENROLLMENT STATUS
# ============================================================================
@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.document
class TestEnrollmentStatus:
    """
    Test: enrollmentStatus field
    Expected: 2 (Complete) after all required steps
    Values: 0=Failed, 1=Pending, 2=Complete
    """
    
    def test_enrollment_status_complete(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Enrollment status should be 2 (Complete) after document"""
        
        caplog.set_level(logging.INFO)
        
        face_image = normalize_base64(env_vars.get("FACE", "").strip())
        doc_front = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        doc_back = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not face_image or not doc_front:
            pytest.skip("Missing FACE or DAN_DOC_FRONT")
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Enrollment Status (Should be 2=Complete)")
        logger.info("="*120)
        
        # Setup
        helper = TestHelper(api_client, env_vars)
        helper.setup_config()
        token = helper.enroll_user(unique_username)
        
        logger.info("\n📊 Tracking enrollment status through workflow...")
        
        # After face
        helper.add_face(token, unique_username, workflow, face_frames)
        logger.info("Status after face: Likely 1 (Pending - document required)")
        
        # After document
        doc_resp = helper.add_document(token, doc_front, doc_back)
        doc_data = doc_resp.json()
        
        # ASSERTIONS
        logger.info("\n" + "="*120)
        logger.info("🔍 ENROLLMENT STATUS:")
        logger.info("="*120)
        
        enrollment_status = doc_data.get("enrollmentStatus")
        registration_code = doc_data.get("registrationCode")
        
        logger.info(f"enrollmentStatus: {enrollment_status}")
        logger.info(f"registrationCode: {registration_code}")
        
        status_map = {0: "FAILED", 1: "PENDING", 2: "COMPLETE"}
        logger.info(f"Status meaning: {status_map.get(enrollment_status, 'UNKNOWN')}")
        
        assert enrollment_status == 2, f"Expected enrollmentStatus=2 (Complete), got {enrollment_status}"
        assert registration_code, "Registration code missing (enrollment incomplete)"
        
        logger.info(f"✅ Enrollment COMPLETE with registration code: {registration_code}")


# ============================================================================
# TEST 4: ICAO VERIFICATION (RFID)
# ============================================================================
@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.document
class TestICAOVerification:
    """
    Test: icaoVerificationResult field
    Expected: false when RFID disabled, true when RFID enabled
    """
    
    def test_icao_verification_rfid_disabled(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """ICAO verification should be false when RFID disabled"""
        
        caplog.set_level(logging.INFO)
        
        face_image = normalize_base64(env_vars.get("FACE", "").strip())
        doc_front = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        doc_back = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not face_image or not doc_front:
            pytest.skip("Missing FACE or DAN_DOC_FRONT")
        
        logger.info("\n" + "="*120)
        logger.info("TEST: ICAO Verification (RFID Disabled)")
        logger.info("="*120)
        
        # Setup with RFID DISABLED
        helper = TestHelper(api_client, env_vars)
        helper.setup_config(rfid_enabled=False)
        
        token = helper.enroll_user(unique_username)
        helper.add_face(token, unique_username, workflow, face_frames)
        
        logger.info("\n📄 Adding document with RFID DISABLED...")
        doc_resp = helper.add_document(token, doc_front, doc_back)
        doc_data = doc_resp.json()
        
        # Extract OCR data
        extracted = extract_document_ocr_data(doc_data)
        
        # ASSERTIONS
        logger.info("\n" + "="*120)
        logger.info("🔍 ICAO/RFID VERIFICATION:")
        logger.info("="*120)
        
        icao_result = doc_data.get("icaoVerificationResult")
        rfid_presence = extracted["overall_results"].get("rfid_presence")
        
        logger.info(f"icaoVerificationResult: {icao_result}")
        logger.info(f"rfidPresence: {rfid_presence}")
        
        assert icao_result == False, f"Expected icaoVerificationResult=false (RFID disabled), got {icao_result}"
        assert rfid_presence == 0, f"Expected rfidPresence=0 (no RFID), got {rfid_presence}"
        
        logger.info("✅ ICAO verification is FALSE (RFID disabled as expected)")


# ============================================================================
# TEST 5: RETRY DOCUMENT CAPTURE
# ============================================================================
@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.document
class TestRetryDocumentCapture:
    """
    Test: retryDocumentCapture field
    Expected: false for good quality docs, true for poor quality
    """
    
    def test_good_quality_no_retry(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Good quality document should not require retry"""
        
        caplog.set_level(logging.INFO)
        
        face_image = normalize_base64(env_vars.get("FACE", "").strip())
        doc_front = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        doc_back = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not face_image or not doc_front:
            pytest.skip("Missing FACE or DAN_DOC_FRONT")
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Document Capture Quality (Retry Flag)")
        logger.info("="*120)
        
        # Setup
        helper = TestHelper(api_client, env_vars)
        helper.setup_config()
        token = helper.enroll_user(unique_username)
        helper.add_face(token, unique_username, workflow, face_frames)
        
        logger.info("\n📄 Uploading GOOD QUALITY document...")
        doc_resp = helper.add_document(token, doc_front, doc_back)
        doc_data = doc_resp.json()
        
        # ASSERTIONS
        logger.info("\n" + "="*120)
        logger.info("🔍 CAPTURE QUALITY CHECK:")
        logger.info("="*120)
        
        retry_capture = doc_data.get("retryDocumentCapture")
        doc_verification = doc_data.get("documentVerificationResult")
        
        logger.info(f"retryDocumentCapture: {retry_capture}")
        logger.info(f"documentVerificationResult: {doc_verification}")
        
        assert retry_capture == False, f"Expected retryDocumentCapture=false (good quality), got {retry_capture}"
        
        if retry_capture:
            logger.warning("⚠️  Document requires recapture (poor quality)")
        else:
            logger.info("✅ Document quality ACCEPTABLE (no retry needed)")


# ============================================================================
# TEST 6: FIELD COMPARISON (Visual vs Barcode)
# ============================================================================
@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.document
class TestFieldComparison:
    """
    Test: MRZ/Barcode/Visual field comparison
    Expected: All fields should match across sources
    """
    
    def test_visual_barcode_fields_match(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Visual and barcode fields should match"""
        
        caplog.set_level(logging.INFO)
        
        face_image = normalize_base64(env_vars.get("FACE", "").strip())
        doc_front = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        doc_back = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not face_image or not doc_front:
            pytest.skip("Missing FACE or DAN_DOC_FRONT")
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Field Comparison (Visual vs Barcode vs MRZ)")
        logger.info("="*120)
        
        # Setup
        helper = TestHelper(api_client, env_vars)
        helper.setup_config()
        token = helper.enroll_user(unique_username)
        helper.add_face(token, unique_username, workflow, face_frames)
        
        logger.info("\n📄 Verifying field consistency across sources...")
        doc_resp = helper.add_document(token, doc_front, doc_back)
        doc_data = doc_resp.json()
        
        # Extract data
        extracted = extract_document_ocr_data(doc_data)
        
        # ASSERTIONS
        logger.info("\n" + "="*120)
        logger.info("🔍 FIELD COMPARISON RESULTS:")
        logger.info("="*120)
        
        mismatches = []
        matches = []
        
        for field_name, field_data in extracted["all_fields"].items():
            visual = field_data.get("visual", "")
            barcode = field_data.get("barcode", "")
            
            if visual and barcode and visual != barcode:
                mismatches.append(f"{field_name}: visual='{visual}' vs barcode='{barcode}'")
            elif visual and barcode and visual == barcode:
                matches.append(f"{field_name}: ✅ MATCH")
        
        logger.info(f"\n✅ Fields matching: {len(matches)}")
        for match in matches[:10]:  # Show first 10
            logger.info(f"   {match}")
        
        if mismatches:
            logger.error(f"\n❌ Fields mismatching: {len(mismatches)}")
            for mismatch in mismatches:
                logger.error(f"   {mismatch}")
            pytest.fail(f"Field mismatches found: {mismatches}")
        else:
            logger.info(f"\n✅ ALL {len(matches)} fields match across visual and barcode")


# ============================================================================
# HELPER CLASS
# ============================================================================
class TestHelper:
    """Helper class for common test operations"""
    
    def __init__(self, api_client, env_vars):
        self.api_client = api_client
        self.env_vars = env_vars
    
    def setup_config(self, rfid_enabled=False):
        """Configure admin"""
        config_resp = self.api_client.http_client.get("/onboarding/admin/customerConfig")
        config = copy.deepcopy(config_resp.json().get("onboardingConfig", {}))
        
        enrollment = config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment['addDocument'] = True
        enrollment['addFace'] = True
        enrollment['addDevice'] = False
        
        doc_settings = config.setdefault("onboardingOptions", {}).setdefault("document", {})
        doc_settings['rfid'] = "ENABLED" if rfid_enabled else "DISABLED"
        
        self.api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": config})
        time.sleep(1)
    
    def enroll_user(self, username):
        """Enroll and return token"""
        resp = self.api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": username,
            "email": self.env_vars.get("EMAIL") or f"{username}@example.com",
            "firstName": self.env_vars.get("FIRSTNAME") or "Test",
            "lastName": self.env_vars.get("LASTNAME") or "User",
        })
        time.sleep(1)
        return resp.json().get("enrollmentToken")
    
    def add_face(self, token, username, workflow, frames):
        """Add face"""
        self.api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": username},
                    "workflow_data": {"workflow": workflow, "frames": frames},
                },
            },
        })
        time.sleep(3)
    
    def add_document(self, token, front, back):
        """Add document"""
        doc_images = [{"lightingScheme": 6, "image": front, "format": "JPG"}]
        if back:
            doc_images.append({"lightingScheme": 6, "image": back, "format": "JPG"})
        
        payload = {
            "enrollmentToken": token,
            "documentsInfo": {
                "documentImage": doc_images,
                "documentPayload": {"request": {"vendor": "REGULA", "data": {}}}
            }
        }
        
        time.sleep(5)  # Wait for OCR processing
        return self.api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json=payload)
