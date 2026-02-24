"""
Document + Face Age Verification - CORRECT PAYLOAD STRUCTURE
"""
import pytest
import copy
import time
import logging

logger = logging.getLogger(__name__)

DOCUMENT_FACE_AGE_SCENARIOS = [
    (1, 16, "Child/Teen (1-16)", "FAIL"),
    (18, 65, "Adult (18-65)", "PASS"),
    (21, 100, "Legal adult (21-100)", "PASS"),
    (1, 30, "Young (1-30)", "FAIL"),
    (40, 60, "Middle age (40-60)", "PASS"),
    (65, 120, "Senior (65-120)", "FAIL"),
    (1, 101, "All ages (1-101)", "PASS"),
]

DELAYS = {"after_initiate": 1.0, "after_face": 3.0, "after_document": 5.0}

def normalize_base64(data: str) -> str:
    if not data:
        return data
    data = data.strip()
    if data.startswith('data:') and ',' in data:
        data = data.split(',', 1)[1]
    return data


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.document
@pytest.mark.age_verification
class TestDocumentFaceAgeVerification:
    """Age verification with Document + Face (correct payload)"""
    
    @pytest.mark.parametrize("min_age,max_age,scenario_name,expected_result", DOCUMENT_FACE_AGE_SCENARIOS)
    def test_face_then_document(self, api_client, unique_username, face_frames, workflow, env_vars, caplog, min_age, max_age, scenario_name, expected_result):
        """Face → Document with correct OCR payload"""
        
        caplog.set_level(logging.INFO)
        
        face_image = normalize_base64(env_vars.get("FACE", "").strip())
        front_image = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        back_image = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not face_image or not front_image:
            pytest.skip("Missing FACE or DAN_DOC_FRONT")
        
        logger.info(f"\n📄 {scenario_name}: Age {min_age}-{max_age}, Expected: {expected_result}")
        
        # ================================================================
        # CONFIG
        # ================================================================
        logger.info("\nSTEP 1: CONFIG")
        
        config_resp = api_client.http_client.get("/onboarding/admin/customerConfig")
        config = copy.deepcopy(config_resp.json().get("onboardingConfig", {}))
        
        enroll = config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enroll["ageEstimation"] = {"enabled": True, "minAge": min_age, "maxAge": max_age, "minTolerance": 0, "maxTolerance": 0}
        enroll['addDocument'] = True
        enroll['addFace'] = True
        enroll['addDevice'] = False
        
        config.setdefault("onboardingOptions", {}).setdefault("document", {})['rfid'] = "DISABLED"
        
        api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": config})
        logger.info(f"✅ Config: Age {min_age}-{max_age}")
        time.sleep(DELAYS['after_initiate'])
        
        # ================================================================
        # ENROLL
        # ================================================================
        logger.info("\nSTEP 2: ENROLL")
        
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Test",
            "lastName": env_vars.get("LASTNAME") or "User",
        })
        
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        logger.info(f"✅ Username: {unique_username}")
        time.sleep(DELAYS['after_initiate'])
        
        # ================================================================
        # FACE FIRST
        # ================================================================
        logger.info("\nSTEP 3: ADD FACE")
        
        face_resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        
        face_data = face_resp.json() if face_resp.status_code == 200 else {}
        
        age_check = face_data.get("ageEstimationCheck", {})
        age_from_server = age_check.get("ageFromFaceLivenessServer")
        actual_result = age_check.get("result", "UNKNOWN")
        
        liveness_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        liveness_decision = liveness_data.get("decision", "UNKNOWN")
        
        logger.info(f"✅ Face: Age={age_from_server}, Result={actual_result}, Liveness={liveness_decision}")
        time.sleep(DELAYS['after_face'])
        
        # ================================================================
        # DOCUMENT SECOND (CORRECT PAYLOAD!)
        # ================================================================
        logger.info("\nSTEP 4: ADD DOCUMENT OCR")
        
        # Build document images array (same as working script)
        document_images = [
            {
                "lightingScheme": 6,
                "image": front_image,
                "format": "JPG"
            }
        ]
        
        if back_image:
            document_images.append({
                "lightingScheme": 6,
                "image": back_image,
                "format": "JPG"
            })
        
        # CORRECT PAYLOAD STRUCTURE (from working script)
        ocr_payload = {
            "enrollmentToken": enrollment_token,
            "documentsInfo": {
                "documentImage": document_images,
                "documentPayload": {
                    "request": {
                        "vendor": "REGULA",
                        "data": {}
                    }
                }
            }
        }
        
        logger.info(f"   Images: {len(document_images)} (using working script payload structure)")
        
        try:
            doc_resp = api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json=ocr_payload)
            
            if doc_resp.status_code != 200:
                logger.error(f"❌ Document OCR: {doc_resp.status_code} - {doc_resp.text[:300]}")
                pytest.fail(f"Document OCR failed: {doc_resp.text}")
            
            logger.info(f"✅ Document OCR completed")
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            pytest.fail(f"Document OCR failed: {str(e)}")
        
        time.sleep(DELAYS['after_document'])
        
        # ================================================================
        # VERDICT
        # ================================================================
        logger.info("\nVERDICT")
        
        match = actual_result == expected_result
        logger.info(f"Expected: {expected_result}, Actual: {actual_result} → {'✅ PASS' if match else '❌ FAIL'}")
        
        if liveness_decision != "LIVE":
            pytest.fail(f"Liveness: {liveness_decision}")
        
        if not match:
            pytest.fail(f"Expected {expected_result}, got {actual_result}")
        
        logger.info(f"✅ Test passed\n")


@pytest.fixture(autouse=True, scope="function")
def cleanup():
    yield
    time.sleep(3)
