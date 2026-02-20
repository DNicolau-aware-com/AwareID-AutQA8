"""
Admin Configuration Tests with Dependency Rules
"""
import pytest
import copy
import time

@pytest.mark.stateful
@pytest.mark.admin
class TestAdminFaceDependencies:
    """Tests for Face enrollment with proper dependency order"""
    
    def test_enable_face_correct_order(self, api_client):
        """
        Enable face with dependencies in correct order
        1. authentication.verifyFace = true
        2. reenrollment.verifyFace = true
        3. enrollment.addFace = true
        """
        print("\n" + "="*80)
        print("ENABLE FACE - CORRECT DEPENDENCY ORDER")
        print("="*80)
        
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        print("\n[STEP 1] Enable authentication.verifyFace")
        auth = new_config.setdefault("onboardingOptions", {}).setdefault("authentication", {})
        auth['verifyFace'] = True
        
        update1 = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        print(f"   Status: {update1.status_code}")
        assert update1.status_code == 200
        time.sleep(2)
        
        print("\n[STEP 2] Enable reenrollment.verifyFace")
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
        
        print("\n[STEP 3] Enable enrollment.addFace")
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
        
        print("\n   ✅ All face settings enabled successfully")
    
    def test_disable_face_all_at_once(self, api_client):
        """
        Disable face - MUST disable all 3 in ONE request
        System rule: When addFace=false, verifyFace must also be false
        """
        print("\n" + "="*80)
        print("DISABLE FACE - ALL AT ONCE (Required by System)")
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
        assert update.status_code == 200, f"Failed: {update.text}"
        
        verify = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified_config = verify.json().get("onboardingConfig", {}).get("onboardingOptions", {})
        
        assert verified_config.get("enrollment", {}).get("addFace") == False
        assert verified_config.get("reenrollment", {}).get("verifyFace") == False
        assert verified_config.get("authentication", {}).get("verifyFace") == False
        
        print("\n   ✅ All face settings disabled (in one request)")


@pytest.mark.stateful
@pytest.mark.admin
class TestAdminDocumentDependencies:
    
    def test_disable_document_with_dependencies(self, api_client):
        """Disable document with icaoVerification first"""
        print("\n" + "="*80)
        print("DISABLE DOCUMENT - WITH DEPENDENCIES")
        print("="*80)
        
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
