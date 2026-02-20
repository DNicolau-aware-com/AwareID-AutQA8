import pytest
import json
import copy


@pytest.mark.stateful
@pytest.mark.admin
class TestEnableEnrollmentSteps:
    """
    Enable/disable specific enrollment steps in customer config.
    
    ⚠️  PERMANENT CHANGES - Does NOT restore original config.
    Use to configure portal settings via API.
    """

    def test_enable_add_device_and_add_document(self, api_client):
        """
        Enable addDevice and addDocument in enrollment options.
        ⚠️  DOES NOT RESTORE - changes are permanent!
        """
        print(f"\n{'='*80}")
        print("ENABLE ADD DEVICE AND ADD DOCUMENT")
        print(f"{'='*80}")

        # Get current config
        print(f"\n>>> Getting current config...")
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert current_response.status_code == 200
        
        data = current_response.json()
        current_config = data.get("onboardingConfig", {})

        # Show current enrollment settings
        current_enrollment = current_config.get("onboardingOptions", {}).get("enrollment", {})
        print(f"\n📋 Current Enrollment Settings:")
        print(f"   addDevice: {current_enrollment.get('addDevice', False)}")
        print(f"   addFace: {current_enrollment.get('addFace', False)}")
        print(f"   addDocument: {current_enrollment.get('addDocument', False)}")
        print(f"   addVoice: {current_enrollment.get('addVoice', False)}")
        print(f"   addPIN: {current_enrollment.get('addPIN', False)}")

        # Update config to enable addDevice and addDocument
        new_config = copy.deepcopy(current_config)
        
        # Ensure structure exists
        if "onboardingOptions" not in new_config:
            new_config["onboardingOptions"] = {}
        if "enrollment" not in new_config["onboardingOptions"]:
            new_config["onboardingOptions"]["enrollment"] = {}

        # Enable addDevice and addDocument
        new_config["onboardingOptions"]["enrollment"]["addDevice"] = True
        new_config["onboardingOptions"]["enrollment"]["addDocument"] = True

        print(f"\n>>> ENABLING:")
        print(f"   addDevice: {current_enrollment.get('addDevice', False)} → True")
        print(f"   addDocument: {current_enrollment.get('addDocument', False)} → True")

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"\n<<< UPDATE STATUS: {update_response.status_code}")
        assert update_response.status_code == 200, (
            f"Update failed: {update_response.status_code} - {update_response.text}"
        )

        # Verify changes
        print(f"\n>>> Verifying changes...")
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert verify_response.status_code == 200
        
        verified_config = verify_response.json().get("onboardingConfig", {})
        verified_enrollment = verified_config.get("onboardingOptions", {}).get("enrollment", {})

        print(f"\n✅ VERIFIED - New Enrollment Settings:")
        print(f"   addDevice: {verified_enrollment.get('addDevice')}")
        print(f"   addFace: {verified_enrollment.get('addFace')}")
        print(f"   addDocument: {verified_enrollment.get('addDocument')}")
        print(f"   addVoice: {verified_enrollment.get('addVoice')}")
        print(f"   addPIN: {verified_enrollment.get('addPIN')}")

        # Assert the changes
        assert verified_enrollment.get("addDevice") is True, (
            f"addDevice not enabled! Got: {verified_enrollment.get('addDevice')}"
        )
        assert verified_enrollment.get("addDocument") is True, (
            f"addDocument not enabled! Got: {verified_enrollment.get('addDocument')}"
        )

        print(f"\n⚠️  CHANGES ARE PERMANENT!")
        print(f"   Go to Admin Portal → Settings → Summary")
        print(f"   You should see:")
        print(f"   ✅ Add Device: ENABLED")
        print(f"   ✅ Add Document: ENABLED")

    def test_disable_add_device_and_add_document(self, api_client):
        """
        Disable addDevice and addDocument in enrollment options.
        ⚠️  DOES NOT RESTORE - changes are permanent!
        """
        print(f"\n{'='*80}")
        print("DISABLE ADD DEVICE AND ADD DOCUMENT")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert current_response.status_code == 200
        
        current_config = current_response.json().get("onboardingConfig", {})
        current_enrollment = current_config.get("onboardingOptions", {}).get("enrollment", {})

        print(f"\n📋 Current Enrollment Settings:")
        print(f"   addDevice: {current_enrollment.get('addDevice', False)}")
        print(f"   addDocument: {current_enrollment.get('addDocument', False)}")

        # Disable both
        new_config = copy.deepcopy(current_config)
        
        if "onboardingOptions" not in new_config:
            new_config["onboardingOptions"] = {}
        if "enrollment" not in new_config["onboardingOptions"]:
            new_config["onboardingOptions"]["enrollment"] = {}

        new_config["onboardingOptions"]["enrollment"]["addDevice"] = False
        new_config["onboardingOptions"]["enrollment"]["addDocument"] = False

        print(f"\n>>> DISABLING:")
        print(f"   addDevice → False")
        print(f"   addDocument → False")

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200

        # Verify
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified_enrollment = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {})

        print(f"\n✅ VERIFIED:")
        print(f"   addDevice: {verified_enrollment.get('addDevice')}")
        print(f"   addDocument: {verified_enrollment.get('addDocument')}")

        assert verified_enrollment.get("addDevice") is False
        assert verified_enrollment.get("addDocument") is False

        print(f"\n⚠️  CHANGES ARE PERMANENT - check admin portal!")

    def test_enable_all_enrollment_steps(self, api_client):
        """
        Enable ALL enrollment steps: device, face, document, voice, PIN.
        ⚠️  DOES NOT RESTORE - changes are permanent!
        """
        print(f"\n{'='*80}")
        print("ENABLE ALL ENROLLMENT STEPS")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        # Enable everything
        new_config = copy.deepcopy(current_config)
        
        if "onboardingOptions" not in new_config:
            new_config["onboardingOptions"] = {}
        if "enrollment" not in new_config["onboardingOptions"]:
            new_config["onboardingOptions"]["enrollment"] = {}

        enrollment_options = {
            "addDevice": True,
            "addFace": True,
            "addDocument": True,
            "addVoice": True,
            "addPIN": True,
        }

        print(f"\n>>> ENABLING ALL ENROLLMENT STEPS:")
        for step, value in enrollment_options.items():
            new_config["onboardingOptions"]["enrollment"][step] = value
            print(f"   {step}: True")

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200

        # Verify
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified_enrollment = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {})

        print(f"\n✅ VERIFIED - All Steps Enabled:")
        for step in enrollment_options.keys():
            value = verified_enrollment.get(step)
            status = "✅" if value else "❌"
            print(f"   {status} {step}: {value}")
            assert value is True, f"{step} not enabled!"

        print(f"\n⚠️  ALL ENROLLMENT STEPS NOW REQUIRED!")
        print(f"   Check admin portal → Settings → Summary")

    def test_enable_only_face(self, api_client):
        """
        Enable ONLY addFace, disable all other enrollment steps.
        ⚠️  DOES NOT RESTORE - changes are permanent!
        """
        print(f"\n{'='*80}")
        print("ENABLE ONLY FACE (DISABLE ALL OTHERS)")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        # Enable only face
        new_config = copy.deepcopy(current_config)
        
        if "onboardingOptions" not in new_config:
            new_config["onboardingOptions"] = {}
        if "enrollment" not in new_config["onboardingOptions"]:
            new_config["onboardingOptions"]["enrollment"] = {}

        enrollment_settings = {
            "addDevice": False,
            "addFace": True,
            "addDocument": False,
            "addVoice": False,
            "addPIN": False,
        }

        print(f"\n>>> SETTING:")
        for step, value in enrollment_settings.items():
            new_config["onboardingOptions"]["enrollment"][step] = value
            status = "✅ ENABLED" if value else "❌ DISABLED"
            print(f"   {step}: {status}")

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200

        # Verify
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified_enrollment = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {})

        print(f"\n✅ VERIFIED:")
        for step, expected in enrollment_settings.items():
            actual = verified_enrollment.get(step)
            match = "✅" if actual == expected else "❌"
            print(f"   {match} {step}: {actual}")
            assert actual == expected, f"{step} should be {expected}, got {actual}"

        print(f"\n⚠️  ONLY FACE REQUIRED NOW - check admin portal!")
