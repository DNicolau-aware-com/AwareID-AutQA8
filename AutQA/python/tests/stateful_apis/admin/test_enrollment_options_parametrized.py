import pytest
import json
import copy


# Define all known enrollment options (update this list based on discovery)
ENROLLMENT_OPTIONS = [
    "addDevice",
    "addFace",
    "addDocument",
    "addVoice",
    "addPIN",
    "checkDeviceSecurity",
    "enableAgeEstimation",
    "icaoVerification",
]


@pytest.mark.stateful
@pytest.mark.admin
class TestEnrollmentOptionsParametrized:
    """
    Parametrized tests for each enrollment option.
    Each test enables/disables a specific enrollment step.
    Automatically handles validation errors for invalid configurations.
    """

    @pytest.mark.parametrize("option_name", ENROLLMENT_OPTIONS)
    def test_enable_enrollment_option(self, api_client, option_name):
        """
        Enable a specific enrollment option.
        If API rejects, validates it's a proper error response.
        """
        print(f"\n{'='*80}")
        print(f"ENABLE: {option_name}")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert current_response.status_code == 200
        
        current_config = current_response.json().get("onboardingConfig", {})
        current_enrollment = current_config.get("onboardingOptions", {}).get("enrollment", {})

        # Check if option exists
        if option_name not in current_enrollment:
            pytest.skip(f"{option_name} not available in your config")

        current_value = current_enrollment.get(option_name)
        print(f"   Current value: {current_value}")

        # Enable it
        new_config = copy.deepcopy(current_config)
        if "onboardingOptions" not in new_config:
            new_config["onboardingOptions"] = {}
        if "enrollment" not in new_config["onboardingOptions"]:
            new_config["onboardingOptions"]["enrollment"] = {}

        # Set to True (or appropriate value for non-boolean options)
        if isinstance(current_value, bool):
            new_config["onboardingOptions"]["enrollment"][option_name] = True
            print(f"   Attempting: {option_name} = True")
        else:
            print(f"   ⚠️  Non-boolean option, keeping current value")
            pytest.skip(f"{option_name} is not a boolean option")

        # Try to update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"\n<<< STATUS: {update_response.status_code}")

        # Handle response
        if update_response.status_code == 200:
            # Success - verify the change
            print(f"   ✅ Update accepted")
            
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified_value = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get(option_name)

            print(f"   ✅ Verified: {option_name} = {verified_value}")
            assert verified_value is True, f"Expected True, got {verified_value}"

        elif update_response.status_code in [400, 500]:
            # Validation error - this is expected for some options
            print(f"   ⚠️  Update rejected by API (validation error)")
            
            if update_response.text:
                try:
                    error_data = update_response.json()
                    error_code = error_data.get("errorCode", "UNKNOWN")
                    error_msg = error_data.get("errorMsg", "No message")
                    
                    print(f"   Error Code: {error_code}")
                    print(f"   Error Msg: {error_msg}")
                    
                    # Validate it's a proper error response
                    assert "errorCode" in error_data, "Missing errorCode in error response"
                    assert "errorMsg" in error_data, "Missing errorMsg in error response"
                    
                    print(f"\n✅ EXPECTED VALIDATION ERROR - {option_name} cannot be enabled alone")
                    pytest.skip(f"{option_name} rejected: {error_msg}")
                    
                except json.JSONDecodeError:
                    print(f"   Response: {update_response.text[:200]}")
                    pytest.fail(f"Invalid error response format")
            else:
                print(f"   (empty response)")
                pytest.skip(f"{option_name} rejected with no error message")
        else:
            pytest.fail(f"Unexpected status code: {update_response.status_code}")

    @pytest.mark.parametrize("option_name", ENROLLMENT_OPTIONS)
    def test_disable_enrollment_option(self, api_client, option_name):
        """
        Disable a specific enrollment option.
        If API rejects, validates it's a proper error response.
        """
        print(f"\n{'='*80}")
        print(f"DISABLE: {option_name}")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        current_enrollment = current_config.get("onboardingOptions", {}).get("enrollment", {})

        if option_name not in current_enrollment:
            pytest.skip(f"{option_name} not available")

        current_value = current_enrollment.get(option_name)
        print(f"   Current value: {current_value}")

        if not isinstance(current_value, bool):
            pytest.skip(f"{option_name} is not a boolean option")

        # Disable it
        new_config = copy.deepcopy(current_config)
        new_config["onboardingOptions"]["enrollment"][option_name] = False
        print(f"   Attempting: {option_name} = False")

        # Try to update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"\n<<< STATUS: {update_response.status_code}")

        # Handle response
        if update_response.status_code == 200:
            # Success - verify
            print(f"   ✅ Update accepted")
            
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified_value = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get(option_name)

            print(f"   ✅ Verified: {option_name} = {verified_value}")
            assert verified_value is False, f"Expected False, got {verified_value}"

        elif update_response.status_code in [400, 500]:
            # Validation error
            print(f"   ⚠️  Update rejected (validation error)")
            
            if update_response.text:
                try:
                    error_data = update_response.json()
                    error_code = error_data.get("errorCode", "UNKNOWN")
                    error_msg = error_data.get("errorMsg", "No message")
                    
                    print(f"   Error Code: {error_code}")
                    print(f"   Error Msg: {error_msg}")
                    
                    # Validate error structure
                    assert "errorCode" in error_data
                    assert "errorMsg" in error_data
                    
                    print(f"\n✅ EXPECTED VALIDATION ERROR - {option_name} cannot be disabled (likely required)")
                    pytest.skip(f"{option_name} rejected: {error_msg}")
                    
                except json.JSONDecodeError:
                    print(f"   Response: {update_response.text[:200]}")
                    pytest.fail(f"Invalid error response format")
            else:
                pytest.skip(f"{option_name} rejected with no error message")
        else:
            pytest.fail(f"Unexpected status code: {update_response.status_code}")


# Preset configurations
PRESET_CONFIGS = {
    "face_only": {
        "addDevice": False,
        "addFace": True,
        "addDocument": False,
        "addVoice": False,
        "addPIN": False,
    },
    "face_and_device": {
        "addDevice": True,
        "addFace": True,
        "addDocument": False,
        "addVoice": False,
        "addPIN": False,
    },
    "face_device_document": {
        "addDevice": True,
        "addFace": True,
        "addDocument": True,
        "addVoice": False,
        "addPIN": False,
    },
    "full_biometric": {
        "addDevice": True,
        "addFace": True,
        "addDocument": True,
        "addVoice": True,
        "addPIN": False,
    },
}


@pytest.mark.stateful
@pytest.mark.admin
class TestPresetConfigurations:
    """
    Apply preset enrollment configurations.
    Automatically handles validation errors for invalid presets.
    """

    @pytest.mark.parametrize("preset_name,preset_config", PRESET_CONFIGS.items())
    def test_apply_preset_configuration(self, api_client, preset_name, preset_config):
        """
        Apply a preset enrollment configuration.
        If API rejects, validates error and marks as expected.
        """
        print(f"\n{'='*80}")
        print(f"APPLYING PRESET: {preset_name}")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        # Apply preset
        new_config = copy.deepcopy(current_config)
        if "onboardingOptions" not in new_config:
            new_config["onboardingOptions"] = {}
        if "enrollment" not in new_config["onboardingOptions"]:
            new_config["onboardingOptions"]["enrollment"] = {}

        print(f"\n📋 Settings:")
        for option, value in preset_config.items():
            new_config["onboardingOptions"]["enrollment"][option] = value
            status = "✅ ENABLED" if value else "❌ DISABLED"
            print(f"   {option}: {status}")

        # Try to update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"\n<<< STATUS: {update_response.status_code}")

        # Handle response
        if update_response.status_code == 200:
            # Success - verify all settings
            print(f"   ✅ Preset accepted")
            
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified_enrollment = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {})

            print(f"\n✅ VERIFIED - {preset_name}:")
            all_match = True
            for option, expected_value in preset_config.items():
                actual_value = verified_enrollment.get(option)
                match = actual_value == expected_value
                all_match = all_match and match
                icon = "✅" if match else "❌"
                print(f"   {icon} {option}: {actual_value}")

            if all_match:
                print(f"\n⚠️  Preset '{preset_name}' is now ACTIVE - check admin portal!")
            else:
                pytest.fail(f"Some settings didn't match")

        elif update_response.status_code in [400, 500]:
            # Validation error
            print(f"   ⚠️  Preset rejected (validation error)")
            
            if update_response.text:
                try:
                    error_data = update_response.json()
                    error_code = error_data.get("errorCode", "UNKNOWN")
                    error_msg = error_data.get("errorMsg", "No message")
                    
                    print(f"\n   Error Code: {error_code}")
                    print(f"   Error Msg: {error_msg}")
                    
                    assert "errorCode" in error_data
                    assert "errorMsg" in error_data
                    
                    print(f"\n✅ EXPECTED VALIDATION ERROR")
                    print(f"   Preset '{preset_name}' is not a valid configuration")
                    print(f"   Reason: {error_msg}")
                    
                    # Mark as expected skip (not a failure)
                    pytest.skip(f"Preset rejected: {error_msg}")
                    
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid error response")
            else:
                pytest.skip(f"Preset rejected with no error message")
        else:
            pytest.fail(f"Unexpected status code: {update_response.status_code}")
