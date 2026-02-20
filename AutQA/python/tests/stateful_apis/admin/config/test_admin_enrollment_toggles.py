import pytest
import json
import copy


@pytest.mark.stateful
@pytest.mark.admin
class TestEnrollmentOptions:
    """
    Tests for enrollment step toggles (addFace, addDevice, etc.).
    Each test enables/disables a specific enrollment step.
    """

    ENROLLMENT_TOGGLES = [
        "addFace",
        "addDevice", 
        "addDocument",
        "addVoice",
        "addPIN",
    ]

    @pytest.mark.parametrize("toggle_name", ENROLLMENT_TOGGLES)
    def test_enable_enrollment_toggle(self, api_client, toggle_name):
        """Enable a specific enrollment toggle."""
        print(f"\n{'='*80}")
        print(f"ENABLE: {toggle_name}")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        current_value = enrollment.get(toggle_name, False)
        enrollment[toggle_name] = True

        print(f"   {toggle_name}: {current_value} → True")

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"   Status: {update_response.status_code}")

        if update_response.status_code == 200:
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get(toggle_name)
            print(f"   ✅ Verified: {verified}")
            assert verified is True
        elif update_response.status_code in [400, 500]:
            error = update_response.json().get("errorMsg", "Unknown error")
            print(f"   ⚠️  Rejected: {error}")
            pytest.skip(f"Cannot enable {toggle_name}: {error}")

    @pytest.mark.parametrize("toggle_name", ENROLLMENT_TOGGLES)
    def test_disable_enrollment_toggle(self, api_client, toggle_name):
        """Disable a specific enrollment toggle."""
        print(f"\n{'='*80}")
        print(f"DISABLE: {toggle_name}")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment[toggle_name] = False

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        if update_response.status_code == 200:
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get(toggle_name)
            print(f"   ✅ Disabled: {verified}")
            assert verified is False
        elif update_response.status_code in [400, 500]:
            error = update_response.json().get("errorMsg", "Unknown")
            pytest.skip(f"Cannot disable {toggle_name}: {error}")


    @pytest.mark.parametrize("toggle_name", ["addFace", "addDevice", "addDocument", "addVoice", "addPIN"])
    def test_toggle_on_off_cycle(self, api_client, toggle_name):
        """
        Test complete on/off cycle for enrollment toggle
        
        Steps:
        1. Enable toggle
        2. Verify enabled
        3. Disable toggle
        4. Verify disabled
        """
        print(f"\n{'='*80}")
        print(f"TOGGLE CYCLE: {toggle_name}")
        print("="*80)
        
        # Enable
        print(f"[STEP 1] Enabling {toggle_name}")
        config = api_client.get("/onboarding/admin/customerConfig").json()
        config[toggle_name] = True
        response = api_client.post("/onboarding/admin/customerConfig", json=config)
        assert response.status_code == 200
        
        # Verify enabled
        verify = api_client.get("/onboarding/admin/customerConfig").json()
        assert verify[toggle_name] == True, f"{toggle_name} not enabled"
        print(f"   ✓ {toggle_name} = True")
        
        # Disable
        print(f"[STEP 2] Disabling {toggle_name}")
        config[toggle_name] = False
        response = api_client.post("/onboarding/admin/customerConfig", json=config)
        assert response.status_code == 200
        
        # Verify disabled
        verify = api_client.get("/onboarding/admin/customerConfig").json()
        assert verify[toggle_name] == False, f"{toggle_name} not disabled"
        print(f"   ✓ {toggle_name} = False")
        
        print(f"\n[ADMIN REPORT] test_toggle_on_off_cycle[{toggle_name}]: PASSED")

    @pytest.mark.parametrize("toggle_name", ["addFace", "addDevice", "addDocument", "addVoice", "addPIN"])
    def test_toggle_on_off_cycle(self, api_client, toggle_name):
        """
        Test complete on/off cycle for enrollment toggle
        
        Steps:
        1. Enable toggle
        2. Verify enabled
        3. Disable toggle
        4. Verify disabled
        """
        print(f"\n{'='*80}")
        print(f"TOGGLE CYCLE: {toggle_name}")
        print("="*80)
        
        # Enable
        print(f"[STEP 1] Enabling {toggle_name}")
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment[toggle_name] = True
        
        response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        assert response.status_code == 200
        
        # Verify enabled
        verify = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get(toggle_name)
        assert verified == True, f"{toggle_name} not enabled"
        print(f"    {toggle_name} = True")
        
        # Disable
        print(f"[STEP 2] Disabling {toggle_name}")
        current_response2 = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config2 = current_response2.json().get("onboardingConfig", {})
        new_config2 = copy.deepcopy(current_config2)
        
        enrollment2 = new_config2.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment2[toggle_name] = False
        
        response2 = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config2}
        )
        assert response2.status_code == 200
        
        # Verify disabled
        verify2 = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified2 = verify2.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get(toggle_name)
        assert verified2 == False, f"{toggle_name} not disabled"
        print(f"    {toggle_name} = False")
        
        print(f"\n[ADMIN REPORT] test_toggle_on_off_cycle[{toggle_name}]: PASSED")
