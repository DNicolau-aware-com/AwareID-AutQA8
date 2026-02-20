"""
Complete Admin Configuration Test Suite
========================================
This suite contains ALL admin configuration tests.

Test Organization:
1. Document Settings
2. Age Estimation
3. Duplicate Prevention
4. Enrollment Toggles
5. Other Parameters
6. Preset Configurations
7. Dependency Rules

Note: Some tests may fail due to backend issues:
- Duplicate "serviceVersion" JSON key (500 errors)
- Null authentication object (500 errors)
- Session timeouts
"""

import pytest
import copy
import time

# ============================================================================
# DOCUMENT SETTINGS TESTS
# ============================================================================

@pytest.mark.stateful
@pytest.mark.admin
@pytest.mark.document
class TestDocumentSettings:
    """All document-related configuration tests"""
    
    def test_enable_add_document(self, api_client):
        """Enable document upload feature"""
        print("\n" + "="*80)
        print("ENABLE ADD DOCUMENT")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment['addDocument'] = True
        
        print("   Setting: addDocument = True")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200
        
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("addDocument")
        
        print(f"   ✅ Verified: {verified}")
        assert verified == True
    
    @pytest.mark.parametrize("verification_mode", ["DISABLED", "OPTIONAL", "MANDATORY"])
    def test_set_icao_verification(self, api_client, verification_mode):
        """Set ICAO verification mode"""
        print(f"\n{'='*80}")
        print(f"SET ICAO VERIFICATION = {verification_mode}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment['icaoVerification'] = verification_mode
        
        print(f"   Setting: icaoVerification = {verification_mode}")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200
        
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("icaoVerification")
        
        print(f"   ✅ Verified: {verified}")
        assert verified == verification_mode
    
    @pytest.mark.parametrize("threshold", [1.5, 2.0, 2.5, 3.0])
    def test_set_ocr_portrait_threshold(self, api_client, threshold):
        """Set OCR portrait-selfie match threshold"""
        print(f"\n{'='*80}")
        print(f"SET OCR PORTRAIT THRESHOLD = {threshold}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        full_config = current_response.json()
        
        doc_config = full_config.setdefault("documentVerificationConfig", {})
        doc_config['ocrPortraitSelfieMatchThreshold'] = threshold
        
        print(f"   Setting: ocrPortraitSelfieMatchThreshold = {threshold}")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json=full_config
        )
        
        assert update_response.status_code == 200
        
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify_response.json().get("documentVerificationConfig", {}).get("ocrPortraitSelfieMatchThreshold")
        
        print(f"   ✅ Verified: {verified}")
        assert verified == threshold
    
    @pytest.mark.parametrize("threshold", [2.0, 2.5, 3.0, 3.5])
    def test_set_rfid_portrait_threshold(self, api_client, threshold):
        """Set RFID portrait-selfie match threshold"""
        print(f"\n{'='*80}")
        print(f"SET RFID PORTRAIT THRESHOLD = {threshold}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        full_config = current_response.json()
        
        doc_config = full_config.setdefault("documentVerificationConfig", {})
        doc_config['rfidPortraitSelfieMatchThreshold'] = threshold
        
        print(f"   Setting: rfidPortraitSelfieMatchThreshold = {threshold}")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json=full_config
        )
        
        assert update_response.status_code == 200
        
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify_response.json().get("documentVerificationConfig", {}).get("rfidPortraitSelfieMatchThreshold")
        
        print(f"   ✅ Verified: {verified}")
        assert verified == threshold
    
    def test_disable_document_with_dependencies(self, api_client):
        """Disable document (with ICAO disabled first)"""
        print("\n" + "="*80)
        print("DISABLE DOCUMENT - WITH DEPENDENCIES")
        print("="*80)
        
        # Step 1: Disable ICAO first
        print("\n[STEP 1] Set icaoVerification = DISABLED")
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment['icaoVerification'] = "DISABLED"
        
        update1 = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        print(f"   Status: {update1.status_code}")
        assert update1.status_code == 200
        time.sleep(2)
        
        # Step 2: Disable addDocument
        print("\n[STEP 2] Disable addDocument")
        current_response2 = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config2 = current_response2.json().get("onboardingConfig", {})
        new_config2 = copy.deepcopy(current_config2)
        
        enrollment2 = new_config2.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment2['addDocument'] = False
        
        update2 = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config2}
        )
        print(f"   Status: {update2.status_code}")
        assert update2.status_code == 200
        
        print("\n   ✅ Document disabled successfully")


# ============================================================================
# AGE ESTIMATION TESTS
# ============================================================================

@pytest.mark.stateful
@pytest.mark.admin
@pytest.mark.age
class TestAgeEstimation:
    """All age estimation configuration tests"""
    
    def test_enable_age_estimation(self, api_client):
        """Enable age estimation"""
        print("\n" + "="*80)
        print("ENABLE AGE ESTIMATION")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        age_settings = new_config.setdefault("onboardingOptions", {}).setdefault("ageEstimation", {})
        age_settings['enabled'] = True
        
        print("   Setting: ageEstimation.enabled = True")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200
    
    def test_disable_age_estimation(self, api_client):
        """Disable age estimation"""
        print("\n" + "="*80)
        print("DISABLE AGE ESTIMATION")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        age_settings = new_config.setdefault("onboardingOptions", {}).setdefault("ageEstimation", {})
        age_settings['enabled'] = False
        
        print("   Setting: ageEstimation.enabled = False")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200
    
    @pytest.mark.parametrize("min_age,max_age", [(18, 65), (21, 70), (25, 80), (16, 100)])
    def test_set_age_range(self, api_client, min_age, max_age):
        """Set age range"""
        print(f"\n{'='*80}")
        print(f"SET AGE RANGE = {min_age}-{max_age}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        age_settings = new_config.setdefault("onboardingOptions", {}).setdefault("ageEstimation", {})
        age_settings['minAge'] = min_age
        age_settings['maxAge'] = max_age
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200
    
    @pytest.mark.parametrize("tolerance", [0, 1, 2, 3, 5])
    def test_set_age_tolerance(self, api_client, tolerance):
        """Set age tolerance"""
        print(f"\n{'='*80}")
        print(f"SET AGE TOLERANCE = {tolerance}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        age_settings = new_config.setdefault("onboardingOptions", {}).setdefault("ageEstimation", {})
        age_settings['ageTolerance'] = tolerance
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200


# ============================================================================
# DUPLICATE PREVENTION TESTS
# ============================================================================

@pytest.mark.stateful
@pytest.mark.admin
@pytest.mark.duplicate
class TestDuplicatePrevention:
    """All duplicate prevention configuration tests"""
    
    def test_enable_duplicate_prevention(self, api_client):
        """Enable duplicate prevention"""
        print("\n" + "="*80)
        print("ENABLE DUPLICATE PREVENTION")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        dup_settings = new_config.setdefault("onboardingOptions", {}).setdefault("duplicatePrevention", {})
        dup_settings['enabled'] = True
        
        print("   Setting: duplicatePrevention.enabled = True")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200
    
    def test_disable_duplicate_prevention(self, api_client):
        """Disable duplicate prevention"""
        print("\n" + "="*80)
        print("DISABLE DUPLICATE PREVENTION")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        dup_settings = new_config.setdefault("onboardingOptions", {}).setdefault("duplicatePrevention", {})
        dup_settings['enabled'] = False
        
        print("   Setting: duplicatePrevention.enabled = False")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200
    
    @pytest.mark.parametrize("threshold", [70, 75, 80, 85, 90, 95, 99])
    def test_set_duplicate_match_threshold(self, api_client, threshold):
        """Set duplicate match threshold"""
        print(f"\n{'='*80}")
        print(f"SET DUPLICATE MATCH THRESHOLD = {threshold}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        dup_settings = new_config.setdefault("onboardingOptions", {}).setdefault("duplicatePrevention", {})
        dup_settings['matchThreshold'] = threshold
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200


# ============================================================================
# ENROLLMENT TOGGLES TESTS
# ============================================================================

@pytest.mark.stateful
@pytest.mark.admin
@pytest.mark.enrollment
class TestEnrollmentToggles:
    """All enrollment toggle tests"""
    
    @pytest.mark.parametrize("toggle_name", ["addFace", "addDevice", "addDocument", "addVoice", "addPIN"])
    def test_enable_enrollment_toggle(self, api_client, toggle_name):
        """Enable enrollment toggle"""
        print(f"\n{'='*80}")
        print(f"ENABLE: {toggle_name}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment[toggle_name] = True
        
        print(f"   Setting: {toggle_name} = True")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200
    
    @pytest.mark.parametrize("toggle_name", ["addFace", "addDevice", "addDocument", "addVoice", "addPIN"])
    def test_disable_enrollment_toggle(self, api_client, toggle_name):
        """Disable enrollment toggle"""
        print(f"\n{'='*80}")
        print(f"DISABLE: {toggle_name}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment[toggle_name] = False
        
        print(f"   Setting: {toggle_name} = False")
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200


# ============================================================================
# SYSTEM PARAMETERS TESTS
# ============================================================================

@pytest.mark.stateful
@pytest.mark.admin
@pytest.mark.parameters
class TestSystemParameters:
    """All system parameter tests"""
    
    @pytest.mark.parametrize("max_devices", [1, 2, 3, 5, 10])
    def test_set_max_device_ids(self, api_client, max_devices):
        """Set maximum device IDs"""
        print(f"\n{'='*80}")
        print(f"SET MAX DEVICE IDS = {max_devices}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        new_config['maxDeviceIds'] = max_devices
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200
    
    @pytest.mark.parametrize("max_attempts", [1, 2, 3, 4, 5, 10])
    def test_set_max_authentication_attempts(self, api_client, max_attempts):
        """Set maximum authentication attempts"""
        print(f"\n{'='*80}")
        print(f"SET MAX AUTH ATTEMPTS = {max_attempts}")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        new_config['maxAuthenticationAttempts'] = max_attempts
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update_response.status_code}")
        assert update_response.status_code == 200


# ============================================================================
# DEPENDENCY RULES TESTS
# ============================================================================

@pytest.mark.stateful
@pytest.mark.admin
@pytest.mark.dependencies
class TestDependencyRules:
    """Tests for configuration dependencies"""
    
    def test_enable_face_with_dependencies(self, api_client):
        """Enable face with correct dependency order"""
        print("\n" + "="*80)
        print("ENABLE FACE - WITH DEPENDENCIES")
        print("="*80)
        
        # Step 1: authentication.verifyFace
        print("\n[STEP 1] Enable authentication.verifyFace")
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        auth = new_config.setdefault("onboardingOptions", {}).setdefault("authentication", {})
        auth['verifyFace'] = True
        
        update1 = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        print(f"   Status: {update1.status_code}")
        assert update1.status_code == 200
        time.sleep(2)
        
        # Step 2: reenrollment.verifyFace
        print("[STEP 2] Enable reenrollment.verifyFace")
        current_response2 = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config2 = current_response2.json().get("onboardingConfig", {})
        new_config2 = copy.deepcopy(current_config2)
        
        reenroll = new_config2.setdefault("onboardingOptions", {}).setdefault("reenrollment", {})
        reenroll['verifyFace'] = True
        
        update2 = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config2}
        )
        print(f"   Status: {update2.status_code}")
        assert update2.status_code == 200
        time.sleep(2)
        
        # Step 3: enrollment.addFace
        print("[STEP 3] Enable enrollment.addFace")
        current_response3 = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config3 = current_response3.json().get("onboardingConfig", {})
        new_config3 = copy.deepcopy(current_config3)
        
        enrollment = new_config3.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment['addFace'] = True
        
        update3 = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config3}
        )
        print(f"   Status: {update3.status_code}")
        assert update3.status_code == 200
        
        print("\n   ✅ Face enabled with all dependencies")
    
    def test_disable_face_all_at_once(self, api_client):
        """Disable face (all 3 settings at once - system requirement)"""
        print("\n" + "="*80)
        print("DISABLE FACE - ALL AT ONCE")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        print("\n[SINGLE REQUEST] Disable all 3 together:")
        print("   - enrollment.addFace = False")
        print("   - reenrollment.verifyFace = False")
        print("   - authentication.verifyFace = False")
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment['addFace'] = False
        
        reenroll = new_config.setdefault("onboardingOptions", {}).setdefault("reenrollment", {})
        reenroll['verifyFace'] = False
        
        auth = new_config.setdefault("onboardingOptions", {}).setdefault("authentication", {})
        auth['verifyFace'] = False
        
        update = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        print(f"   Status: {update.status_code}")
        assert update.status_code == 200
        
        print("\n   ✅ Face disabled (all settings at once)")


# ============================================================================
# CONFTEST - Smart Delays
# ============================================================================

@pytest.fixture(autouse=True, scope="function")
def delay_between_tests():
    """Add 2 second delay after each test to protect admin portal"""
    yield
    time.sleep(2)

@pytest.fixture(autouse=True, scope="class")
def delay_between_classes():
    """Add 5 second delay between test classes"""
    yield
    time.sleep(5)
