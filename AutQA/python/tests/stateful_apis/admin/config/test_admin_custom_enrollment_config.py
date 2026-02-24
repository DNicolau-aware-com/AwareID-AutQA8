"""
Custom Enrollment Configuration + Full Enrollment Flow Test
Uses the EXACT enrollment flow from test_full_enrollment_flow.py
"""
import pytest
import copy
import time

@pytest.mark.stateful
@pytest.mark.admin
@pytest.mark.enrollment
@pytest.mark.custom
class TestCustomEnrollmentConfigurationWithFlow:
    """Test custom enrollment configuration with complete enrollment flow"""
    
    def test_configure_admin_and_enroll_user(self, api_client, unique_username, face_frames, workflow, env_vars):
        """
        Part 1: Configure Admin Settings (ONLY CHANGE WHAT'S NEEDED)
        Part 2: Perform Full Enrollment (EXACT flow from test_full_enrollment_flow.py)
        """
        print("\n" + "="*80)
        print("PART 1: CONFIGURE ADMIN SETTINGS (MINIMAL CHANGES)")
        print("="*80)
        
        # ====================================================================
        # GET CURRENT CONFIGURATION
        # ====================================================================
        print("\n[STEP 1/2] Get current configuration")
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert current_response.status_code == 200, f"Failed to get config: {current_response.text}"
        
        full_config = current_response.json()
        onboarding_config = full_config.get("onboardingConfig", {})
        new_config = copy.deepcopy(onboarding_config)
        
        print("    Current configuration retrieved")
        
        # ====================================================================
        # ANALYZE AND UPDATE SETTINGS
        # ====================================================================
        print("\n[STEP 2/2] Analyze and update only required settings")
        
        current_options = onboarding_config.get("onboardingOptions", {})
        current_enrollment = current_options.get("enrollment", {})
        current_auth = current_options.get("authentication", {})
        current_reenroll = current_options.get("reenrollment", {})
        current_age = current_options.get("ageEstimation", {})
        
        changes_needed = []
        
        onboarding_options = new_config.setdefault("onboardingOptions", {})
        enrollment = onboarding_options.setdefault("enrollment", {})
        authentication = onboarding_options.setdefault("authentication", {})
        reenrollment = onboarding_options.setdefault("reenrollment", {})
        age_estimation = onboarding_options.setdefault("ageEstimation", {})
        
        print("\n    Checking Enrollment Settings:")
        
        # Check required settings
        if current_enrollment.get('addFace') != True:
            enrollment['addFace'] = True
            changes_needed.append("enrollment.addFace = TRUE")
            print("      CHANGE: addFace  TRUE")
        else:
            print("      KEEP: addFace = TRUE (already set)")
        
        if current_enrollment.get('addDevice') != True:
            enrollment['addDevice'] = True
            changes_needed.append("enrollment.addDevice = TRUE")
            print("      CHANGE: addDevice  TRUE")
        else:
            print("      KEEP: addDevice = TRUE (already set)")
        
        if current_enrollment.get('addDocument') != False:
            enrollment['addDocument'] = False
            changes_needed.append("enrollment.addDocument = FALSE")
            print("      CHANGE: addDocument  FALSE")
        else:
            print("      KEEP: addDocument = FALSE (already set)")
        
        if current_enrollment.get('addVoice') != False:
            enrollment['addVoice'] = False
            changes_needed.append("enrollment.addVoice = FALSE")
            print("      CHANGE: addVoice  FALSE")
        else:
            print("      KEEP: addVoice = FALSE (already set)")
        
        if current_enrollment.get('addPIN') != False:
            enrollment['addPIN'] = False
            changes_needed.append("enrollment.addPIN = FALSE")
            print("      CHANGE: addPIN  FALSE")
        else:
            print("      KEEP: addPIN = FALSE (already set)")
        
        print("\n    Checking Authentication Settings:")
        
        if current_auth.get('verifyFace') != True:
            authentication['verifyFace'] = True
            changes_needed.append("authentication.verifyFace = TRUE")
            print("      CHANGE: authentication.verifyFace  TRUE")
        else:
            print("      KEEP: authentication.verifyFace = TRUE (already set)")
        
        print("\n    Checking Re-enrollment Settings:")
        
        if current_reenroll.get('verifyFace') != True:
            reenrollment['verifyFace'] = True
            changes_needed.append("reenrollment.verifyFace = TRUE")
            print("      CHANGE: reenrollment.verifyFace  TRUE")
        else:
            print("      KEEP: reenrollment.verifyFace = TRUE (already set)")
        
        print("\n    Checking Age Estimation Settings:")
        
        if current_age.get('enabled') != True:
            age_estimation['enabled'] = True
            changes_needed.append("ageEstimation.enabled = TRUE")
            print("      CHANGE: ageEstimation.enabled  TRUE")
        else:
            print("      KEEP: ageEstimation.enabled = TRUE (already set)")
        
        if current_age.get('minAge') != 1:
            age_estimation['minAge'] = 1
            changes_needed.append("ageEstimation.minAge = 1")
            print("      CHANGE: ageEstimation.minAge  1")
        else:
            print("      KEEP: ageEstimation.minAge = 1 (already set)")
        
        if current_age.get('maxAge') != 101:
            age_estimation['maxAge'] = 101
            changes_needed.append("ageEstimation.maxAge = 101")
            print("      CHANGE: ageEstimation.maxAge  101")
        else:
            print("      KEEP: ageEstimation.maxAge = 101 (already set)")
        
        # ====================================================================
        # SAVE CHANGES IF NEEDED
        # ====================================================================
        print("\n" + "="*80)
        
        if changes_needed:
            print(f" Changes Required: {len(changes_needed)} settings need updating")
            print("="*80)
            for change in changes_needed:
                print(f"    {change}")
            
            print("\n Saving changes...")
            
            update_response = api_client.http_client.post(
                "/onboarding/admin/customerConfig",
                json={"onboardingConfig": new_config}
            )
            
            print(f"   POST /onboarding/admin/customerConfig")
            print(f"   Status: {update_response.status_code}")
            
            assert update_response.status_code == 200, f"Failed to save config: {update_response.text}"
            
            print("    Changes saved successfully")
            time.sleep(3)
            
        else:
            print(" No Changes Needed - Configuration Already Correct!")
            print("="*80)
        
        # ====================================================================
        # VERIFY CONFIGURATION
        # ====================================================================
        print("\n[VERIFICATION] Verify final configuration state")
        
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified_config = verify_response.json().get("onboardingConfig", {})
        verified_options = verified_config.get("onboardingOptions", {})
        
        verified_enrollment = verified_options.get("enrollment", {})
        assert verified_enrollment.get("addFace") == True
        assert verified_enrollment.get("addDevice") == True
        assert verified_enrollment.get("addDocument") == False
        
        verified_auth = verified_options.get("authentication", {})
        assert verified_auth.get("verifyFace") == True
        
        verified_reenroll = verified_options.get("reenrollment", {})
        assert verified_reenroll.get("verifyFace") == True
        
        verified_age = verified_options.get("ageEstimation", {})
        assert verified_age.get("enabled") == True
        assert verified_age.get("minAge") == 1
        assert verified_age.get("maxAge") == 101
        
        print("\n    All required settings verified")
        print("\n" + "="*80)
        print("ADMIN CONFIGURATION SUMMARY")
        print("="*80)
        print("\n Settings:")
        print("    addFace = TRUE")
        print("    addDevice = TRUE")
        print("    addDocument = FALSE")
        print("    Age: 1-101 years")
        print("="*80)
        
        time.sleep(2)
        
        # ====================================================================
        # PART 2: FULL ENROLLMENT FLOW (EXACT COPY FROM WORKING TEST)
        # ====================================================================
        print("\n" + "="*80)
        print("PART 2: FULL USER ENROLLMENT FLOW")
        print("="*80)
        print(f"Username: {unique_username} | Workflow: {workflow}")
        
        # ====================================================================
        # STEP 1: INITIATE ENROLLMENT
        # ====================================================================
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
        
        print(f"\n Enrollment initiated")
        print(f"   Token: {enrollment_token[:20]}...")
        print(f"   Required checks: {required_checks}")
        
        # ====================================================================
        # STEP 2: ADD DEVICE
        # ====================================================================
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
        
        print(f" Device added: {device_id}")
        
        # ====================================================================
        # STEP 3: ADD FACE
        # ====================================================================
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
        
        print(f" Face enrolled successfully")
        
        registration_code = face_data.get("registrationCode")
        if registration_code:
            print(f"\n  Registration Code: {registration_code}")
        
        # ====================================================================
        # FINAL SUMMARY
        # ====================================================================
        print(f"\n{'='*80}")
        print(" TEST COMPLETED SUCCESSFULLY!")
        print(f"{'='*80}")
        print(f"\n Admin Config: Set correctly (age 1-101, face + device)")
        print(f" User Enrolled: {unique_username}")
        print(f" Device: {device_id}")
        print(f" Face: Enrolled")
        if registration_code:
            print(f" Registration Code: {registration_code}")
        print("="*80)


@pytest.fixture(autouse=True, scope="function")
def delay_after_flow():
    """Add delay after enrollment flow"""
    yield
    time.sleep(3)
