"""
Enhanced Add Face Tests with Validation
Tests face enrollment with liveness validation and transaction tracking
"""
import pytest
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@pytest.mark.stateful
@pytest.mark.enrollment
class TestAddFace:
    """Face enrollment tests with complete validation"""
    
    def test_basic(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Basic face enrollment test with validation"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Basic Face Enrollment")
        logger.info("="*120)
        
        # Enroll
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        enroll_tx_id = enroll_resp.json().get("transactionId", "N/A")
        
        logger.info(f"Transaction ID: {enroll_tx_id}")
        logger.info(f"✅ Enrolled: {unique_username}")
        
        # Add face
        face_resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        
        face_data = face_resp.json()
        face_tx_id = face_data.get("transactionId", "N/A")
        
        # Validate liveness
        liveness = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        liveness_decision = liveness.get("decision")
        
        logger.info(f"Transaction ID: {face_tx_id}")
        logger.info(f"✅ Face added successfully")
        logger.info(f"   Liveness: {liveness_decision}")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        # Validations
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATIONS")
        logger.info("🔥"*60)
        
        assert face_resp.status_code == 200, f"Face enrollment failed: {face_resp.status_code}"
        logger.info("1️⃣  Status Code: ✅ PASSED (200)")
        
        assert liveness_decision == "LIVE", f"Liveness failed: {liveness_decision}"
        logger.info("2️⃣  Liveness: ✅ PASSED (LIVE)")
        
        logger.info("\n✅ TEST PASSED\n")
    
    def test_returns_registration_code(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Test that face enrollment returns registration code"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Face Enrollment Returns Registration Code")
        logger.info("="*120)
        
        # Enroll
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        
        # Add face
        face_resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        
        face_data = face_resp.json()
        registration_code = face_data.get("registrationCode")
        enrollment_status = face_data.get("enrollmentStatus")
        
        logger.info(f"✅ Registration Code: {registration_code}")
        logger.info(f"   Enrollment Status: {enrollment_status} ({'COMPLETE' if enrollment_status == 2 else 'PENDING'})")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        # Validations
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATIONS")
        logger.info("🔥"*60)
        
        assert registration_code, "Registration code missing"
        logger.info("1️⃣  Registration Code: ✅ PASSED")
        
        assert enrollment_status == 2, f"Expected status 2 (Complete), got {enrollment_status}"
        logger.info("2️⃣  Enrollment Status: ✅ PASSED (2=COMPLETE)")
        
        logger.info("\n✅ TEST PASSED\n")
    
    def test_with_full_metadata(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Test face enrollment with complete metadata"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Face Enrollment with Full Metadata")
        logger.info("="*120)
        
        # Enroll
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        
        # Add face with metadata
        face_resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {
                        "username": unique_username,
                        "test_run": "full_metadata",
                        "timestamp": datetime.now().isoformat()
                    },
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        
        logger.info(f"✅ Face enrolled with full metadata")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        # Validations
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATIONS")
        logger.info("🔥"*60)
        
        assert face_resp.status_code == 200
        logger.info("1️⃣  Status Code: ✅ PASSED")
        
        logger.info("\n✅ TEST PASSED\n")
    
    def test_with_5_frames(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Test face enrollment with exactly 5 frames"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Face Enrollment with 5 Frames")
        logger.info("="*120)
        
        # Use only first 5 frames
        five_frames = face_frames[:5]
        
        logger.info(f"   Using {len(five_frames)} frames")
        
        # Enroll
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        
        # Add face
        face_resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": five_frames},
                },
            },
        })
        
        logger.info(f"✅ Face enrolled with 5 frames")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        # Validations
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATIONS")
        logger.info("🔥"*60)
        
        assert face_resp.status_code == 200
        logger.info("1️⃣  Status Code: ✅ PASSED")
        
        logger.info("\n✅ TEST PASSED\n")
