"""
Document + Face Age Verification Test Suite (RFID DISABLED)
Uses TX_DL_FRONT_b64, TX_DL_BACK_b64, and TX_DL_FACE_B64 from .env
"""
import pytest
import copy
import time
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================================
# TEST DATA: Age scenarios
# ============================================================================
DOCUMENT_FACE_AGE_SCENARIOS = [
    (1, 16, "Child/Teen only (1-16)", "FAIL"),
    (18, 65, "Adult working age (18-65)", "PASS"),
    (21, 100, "Legal adult (21-100)", "PASS"),
    (1, 30, "Young person (1-30)", "FAIL"),
    (40, 60, "Middle age (40-60)", "PASS"),
    (65, 120, "Senior only (65-120)", "FAIL"),
    (1, 101, "All ages (1-101)", "PASS"),
]


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.document
@pytest.mark.age_verification
class TestDocumentFaceAgeVerificationNoRFID:
    """Age verification with DOCUMENT + FACE - RFID DISABLED - Uses TX documents"""
    
    @pytest.mark.parametrize("min_age,max_age,scenario_name,expected_result", DOCUMENT_FACE_AGE_SCENARIOS)
    def test_document_face_no_rfid(
        self, 
        api_client, 
        unique_username, 
        face_frames, 
        workflow, 
        env_vars,
        caplog,
        min_age,
        max_age,
        scenario_name,
        expected_result
    ):
        """Document + Face enrollment - Uses TX (Texas) DL images"""
        
        caplog.set_level(logging.INFO)
        
        # Get TX images from env_vars
        face_image = env_vars.get("TX_DL_FACE_B64")
        doc_front = env_vars.get("TX_DL_FRONT_b64")
        doc_back = env_vars.get("TX_DL_BACK_b64")
        
        if not face_image:
            pytest.skip("TX_DL_FACE_B64 not found in .env")
        if not doc_front:
            pytest.skip("TX_DL_FRONT_b64 not found in .env")
        
        # Normalize base64
        if face_image.startswith('data:'):
            face_image = face_image.split(',')[1]
        if doc_front.startswith('data:'):
            doc_front = doc_front.split(',')[1]
        if doc_back and doc_back.startswith('data:'):
            doc_back = doc_back.split(',')[1]
        
        logger.info(f"\n Using TX (Texas) DL images from .env:")
        logger.info(f"   TX_DL_FRONT_b64: ")
        logger.info(f"   TX_DL_BACK_b64: {'' if doc_back else ''}")
        logger.info(f"   TX_DL_FACE_B64: ")
        
        # ====================================================================
        # HEADER
        # ====================================================================
        logger.info("\n" + ""*60)
        logger.info(f"TX DL TEST: {scenario_name}")
        logger.info(f"Age Range: {min_age}-{max_age} years")
        logger.info(f"Expected: {expected_result}")
        logger.info(""*60)
        
        # ====================================================================
        # STEP 1: CONFIGURE ADMIN
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 1: ADMIN CONFIG - DOCUMENT + FACE (NO RFID)")
        logger.info("="*120)
        
        config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = config_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": min_age,
            "maxAge": max_age,
            "minTolerance": 0,
            "maxTolerance": 0
        }
        
        enrollment['addDocument'] = True
        enrollment['addFace'] = True
        enrollment['addDevice'] = False
        
        document_settings = new_config.setdefault("onboardingOptions", {}).setdefault("document", {})
        document_settings['rfid'] = "DISABLED"
        
        authentication = new_config.setdefault("onboardingOptions", {}).setdefault("authentication", {})
        authentication['verifyFace'] = True
        
        reenrollment = new_config.setdefault("onboardingOptions", {}).setdefault("reenrollment", {})
        reenrollment['verifyFace'] = True
        
        api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": new_config})
        
        logger.info(f" Config: Document , Face , Device , RFID ")
        logger.info(f"   Age: {min_age}-{max_age} years")
        time.sleep(2)
        
        # ====================================================================
        # STEP 2: ENROLL
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 2: ENROLL")
        logger.info("="*120)
        
        enroll_response = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Test",
            "lastName": env_vars.get("LASTNAME") or "User",
        })
        
        enroll_data = enroll_response.json()
        enrollment_token = enroll_data.get("enrollmentToken")
        
        logger.info(f" Username: {unique_username}")
        assert enroll_response.status_code == 200
        time.sleep(1)
        
        # ====================================================================
        # STEP 3: ADD DOCUMENT (TX DL)
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 3: ADD DOCUMENT (TX DL - NO RFID)")
        logger.info("="*120)
        
        doc_payload = {
            "enrollmentToken": enrollment_token,
            "documentData": {
                "images": [{"data": doc_front, "light": "WHITE", "side": "FRONT", "metrics": {}}]
            }
        }
        
        if doc_back:
            doc_payload["documentData"]["images"].append({
                "data": doc_back, "light": "WHITE", "side": "BACK", "metrics": {}
            })
        
        logger.info(f"   TX DL Images: {len(doc_payload['documentData']['images'])}")
        
        try:
            doc_response = api_client.http_client.post("/onboarding/enrollment/addDocument", json=doc_payload)
            
            if doc_response.status_code != 200:
                logger.error(f" Document failed: {doc_response.status_code}")
                logger.error(f"   {doc_response.text[:200]}")
                pytest.fail(f"Document failed: {doc_response.text}")
            
            logger.info(f" TX DL enrolled")
        except Exception as e:
            logger.error(f" Document upload error: {str(e)}")
            pytest.fail(f"Document upload failed: {str(e)}")
        
        time.sleep(1)
        
        # ====================================================================
        # STEP 4: ADD FACE (TX DL face)
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 4: ADD FACE (TX DL Face with Age Verification)")
        logger.info("="*120)
        
        # Create face_frames from TX face image (repeat 3 times for liveness)
        tx_face_frames = [face_image, face_image, face_image]
        
        face_response = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": tx_face_frames},
                },
            },
        })
        
        face_data = face_response.json() if face_response.status_code == 200 else {}
        
        # Extract data
        age_check = face_data.get("ageEstimationCheck", {})
        age_from_server = age_check.get("ageFromFaceLivenessServer")
        actual_result = age_check.get("result", "UNKNOWN")
        
        liveness_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        liveness_decision = liveness_data.get("decision", "UNKNOWN")
        
        logger.info(f"Age: {age_from_server}, Result: {actual_result}, Liveness: {liveness_decision}")
        
        # ====================================================================
        # VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("VERDICT - TX DL ENROLLMENT")
        logger.info("="*120)
        
        behavior_match = actual_result == expected_result
        
        logger.info(f"Scenario: {scenario_name}")
        logger.info(f"Expected: {expected_result}, Actual: {actual_result}")
        logger.info(f"{' PASSED' if behavior_match else ' FAILED'}")
        
        if age_from_server:
            age_in_range = min_age <= age_from_server <= max_age
            if not age_in_range:
                diff = abs(age_from_server - (max_age if age_from_server > max_age else min_age))
                logger.info(f" TX DL Age {age_from_server} is {diff} years {'above max' if age_from_server > max_age else 'below min'}")
        
        # Assertions
        if liveness_decision != "LIVE":
            logger.error(f" Liveness: {liveness_decision}")
            pytest.fail(f"Liveness: {liveness_decision}")
        
        if not behavior_match:
            logger.error(f" Behavior mismatch")
            pytest.fail(f"Expected {expected_result}, got {actual_result}")
        
        logger.info(f"\n TX DL test passed\n")


@pytest.fixture(autouse=True, scope="function")
def cleanup():
    yield
    time.sleep(3)
