import pytest
from tests.utils.settings_validator import validate_enrollment_flow
from tests.utils.response_analyzer import analyze_liveness, analyze_document, print_analysis


@pytest.mark.stateful
@pytest.mark.enrollment
class TestCompleteEnrollmentFlowFull:
    """
    Complete enrollment with all portal-required steps:
    - Add Device
    - Add Face  
    - Add Document OCR
    """

    def test_full_enrollment_with_all_steps(self, api_client, unique_username, face_frames, workflow, env_vars):
        """
        Full enrollment flow: device + face + document.
        Validates portal settings match test implementation.
        """
        print(f"\n{'='*80}")
        print("COMPLETE ENROLLMENT FLOW - ALL STEPS")
        print(f"{'='*80}")
        print(f"Username: {unique_username} | Workflow: {workflow}")

        # ======================================================================

        # ======================================================================
        enroll_payload = {
            "username": unique_username,
            "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Test",
            "lastName": env_vars.get("LASTNAME") or "User",
        }
        
        print(f"\n{'='*80}")
        print("STEP 1: INITIATE ENROLLMENT")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/enrollment/enroll")

        enroll_response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
            json=enroll_payload
        )
        
        assert enroll_response.status_code == 200, (
            f"Initiate enrollment failed: {enroll_response.status_code} - {enroll_response.text}"
        )
        
        enroll_data = enroll_response.json()
        enrollment_token = enroll_data.get("enrollmentToken")
        required_checks = enroll_data.get("requiredChecks", [])
        
        assert enrollment_token, "Missing enrollmentToken"
        
        print(f"\n✅ Enrollment initiated")
        print(f"   Token: {enrollment_token[:20]}...")
        print(f"   Required checks: {required_checks}")

        # VALIDATE PORTAL SETTINGS MATCH TEST
        test_implements = ['addDevice', 'addFace', 'addDocument']
        validate_enrollment_flow(required_checks, test_implements)

        # ======================================================================
        # STEP 2: ADD DEVICE
        # ======================================================================
        import time
        device_id = f"test_device_{int(time.time())}"
        
        device_payload = {
            "enrollmentToken": enrollment_token,
            "deviceId": device_id,
            "platform": "web",
            "browser": "Chrome",
            "os": "Windows"
        }
        
        print(f"\n{'='*80}")
        print("STEP 2: ADD DEVICE")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/enrollment/addDevice")
        print(f">>> DEVICE ID: {device_id}")

        device_response = api_client.http_client.post(
            "/onboarding/enrollment/addDevice",
            json=device_payload
        )
        
        assert device_response.status_code == 200, (
            f"Add device failed: {device_response.status_code} - {device_response.text}"
        )
        
        print(f"✅ Device added: {device_id}")

        # ======================================================================
        # STEP 3: ADD FACE
        # ======================================================================
        face_payload = {
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames,
                    },
                },
            },
        }
        
        print(f"\n{'='*80}")
        print("STEP 3: ADD FACE")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/enrollment/addFace")
        print(f">>> FRAMES: {len(face_frames)}")

        face_response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json=face_payload
        )
        
        assert face_response.status_code == 200, (
            f"Add face failed: {face_response.status_code} - {face_response.text}"
        )
        
        face_data = face_response.json()
        
        # ANALYZE LIVENESS
        liveness_analysis = analyze_liveness(face_data)
        print_analysis(liveness_analysis, "FACE LIVENESS ANALYSIS")
        
        # Assert liveness
        assert liveness_analysis["is_live"], (
            f"Face liveness check failed: {liveness_analysis['verdict']}"
        )

        # ======================================================================
        # STEP 4: ADD DOCUMENT OCR
        # ======================================================================
        front_image = env_vars.get("DOCUMENT_FRONT") or env_vars.get("DAN_DOC_FRONT")
        back_image = env_vars.get("DOCUMENT_BACK") or env_vars.get("DAN_DOC_BACK")
        
        if not front_image:
            pytest.skip("DOCUMENT_FRONT not found in .env - cannot complete document step")
        
        # Normalize base64
        if front_image.startswith("data:image"):
            front_image = front_image.split(",")[1]
        if back_image and back_image.startswith("data:image"):
            back_image = back_image.split(",")[1]
        
        front_image = front_image.strip()
        if back_image:
            back_image = back_image.strip()
        
        document_payload = {
            "enrollmentToken": enrollment_token,
            "documentsInfo": {
                "documentImage": [
                    {
                        "lightingScheme": 6,
                        "image": front_image,
                        "format": "jpg"
                    }
                ],
                "documentPayload": {
                    "request": {
                        "vendor": "REGULA",
                        "data": {}
                    }
                },
                "processParam": {
                    "alreadyCropped": False
                }
            },
            "processingInstructions": {
                "documentValidationRules": {
                    "checkLiveness": True,
                    "workflow": workflow,
                    "securityLevel": 4,
                    "minimumAge": 0,
                    "maximumAge": 0,
                    "validateDocumentNotExpired": True,
                    "fieldsToValidate": []
                }
            }
        }
        
        # Add back image if present
        if back_image:
            document_payload["documentsInfo"]["documentImage"].append({
                "lightingScheme": 6,
                "image": back_image,
                "format": "jpg"
            })
        
        print(f"\n{'='*80}")
        print("STEP 4: ADD DOCUMENT OCR")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/enrollment/addDocumentOCR")
        print(f">>> IMAGES: {'Front + Back' if back_image else 'Front only'}")

        doc_response = api_client.http_client.post(
            "/onboarding/enrollment/addDocumentOCR",
            json=document_payload
        )
        
        assert doc_response.status_code == 200, (
            f"Add document failed: {doc_response.status_code} - {doc_response.text}"
        )
        
        doc_data = doc_response.json()
        
        # ANALYZE DOCUMENT
        doc_analysis = analyze_document(doc_data)
        print_analysis(doc_analysis, "DOCUMENT VERIFICATION ANALYSIS")
        
        # Assert document valid and not expired
        assert doc_analysis["document_verified"], (
            f"Document verification failed: {doc_analysis['verdict']}"
        )
        assert not doc_analysis["is_expired"], (
            f"Document is expired: {doc_analysis['expiry_date']}"
        )

        # ======================================================================
        # FINAL VALIDATION
        # ======================================================================
        print(f"\n{'='*80}")
        print("ENROLLMENT COMPLETE")
        print(f"{'='*80}")
        print(f"✅ All required steps completed:")
        print(f"   1. Device: {device_id}")
        print(f"   2. Face: {liveness_analysis['verdict']}")
        print(f"   3. Document: {doc_analysis['verdict']}")
        
        registration_code = doc_data.get("registrationCode") or face_data.get("registrationCode")
        if registration_code:
            print(f"\n🎟️  Registration Code: {registration_code}")

    def test_settings_match_portal(self, enrollment_settings):
        """Verify test suite reflects current portal settings."""
        print(f"\n{'='*60}")
        print("ENROLLMENT SETTINGS (from portal)")
        print(f"{'='*60}")
        for key, value in enrollment_settings.items():
            if value is True: 
                print(f"  ✅ ENABLED:  {key}")
            elif value is False: 
                print(f"  ❌ DISABLED: {key}")
            else: 
                print(f"  📊 VALUE:    {key} = {value}")

        assert enrollment_settings["add_face"] is True
        assert enrollment_settings["add_device"] is True
        assert enrollment_settings["add_document"] is True
        assert enrollment_settings["add_voice"] is False
        assert enrollment_settings["prevent_duplicate_enrollments"] is True
