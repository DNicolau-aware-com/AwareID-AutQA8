import pytest
import json
import time


@pytest.mark.stateful
@pytest.mark.admin
class TestUpdateConfigNoRestore:
    """
    Tests for POST /onboarding/admin/customerConfig
    Updates config WITHOUT restoring - changes persist!
    
    ⚠️  PERMANENT CHANGES - Does NOT restore original config.
    Use for manual verification in admin portal.
    """

    # ==========================================================================
    # TESTS THAT MAKE PERMANENT CHANGES
    # ==========================================================================

    def test_increment_max_authentication_attempts(self, api_client):
        """
        Update: Increment maxAuthenticationAttempts by 1.
        ⚠️  DOES NOT RESTORE - change is permanent!
        """
        print(f"\n{'='*80}")
        print("INCREMENT MAX AUTHENTICATION ATTEMPTS")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert current_response.status_code == 200
        current_config = current_response.json().get("onboardingConfig", {})

        # Increment maxAuthenticationAttempts
        current_value = current_config.get("maxAuthenticationAttempts", 4)
        new_value = current_value + 1

        current_config["maxAuthenticationAttempts"] = new_value

        print(f"\n>>> CHANGE: maxAuthenticationAttempts {current_value} → {new_value}")
        print(f">>> Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": current_config}
        )

        print(f"\n<<< STATUS: {update_response.status_code}")
        assert update_response.status_code == 200

        # Verify
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        updated_value = verify_response.json().get("onboardingConfig", {}).get("maxAuthenticationAttempts")

        print(f"\n✅ UPDATED: maxAuthenticationAttempts = {updated_value}")
        print(f"⚠️  CHANGE IS PERMANENT - check admin portal now!")

        assert updated_value == new_value

    def test_toggle_record_enrollment_video(self, api_client):
        """
        Update: Toggle recordEnrollmentVideo (true ↔ false).
        ⚠️  DOES NOT RESTORE - change is permanent!
        """
        print(f"\n{'='*80}")
        print("TOGGLE RECORD ENROLLMENT VIDEO")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        # Toggle recordEnrollmentVideo
        current_flag = current_config.get("recordEnrollmentVideo", True)
        new_flag = not current_flag

        current_config["recordEnrollmentVideo"] = new_flag

        print(f"\n>>> CHANGE: recordEnrollmentVideo {current_flag} → {new_flag}")
        print(f">>> Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": current_config}
        )

        assert update_response.status_code == 200

        # Verify
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        updated_flag = verify_response.json().get("onboardingConfig", {}).get("recordEnrollmentVideo")

        print(f"\n✅ UPDATED: recordEnrollmentVideo = {updated_flag}")
        print(f"⚠️  CHANGE IS PERMANENT - check admin portal now!")

        assert updated_flag == new_flag

    def test_set_max_device_ids_unique(self, api_client):
        """
        Update: Set maxDeviceIds to a unique value based on timestamp.
        ⚠️  DOES NOT RESTORE - change is permanent!
        """
        print(f"\n{'='*80}")
        print("SET MAX DEVICE IDS (UNIQUE VALUE)")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        # Generate unique value (3-10 based on current second)
        import random
        random.seed(int(time.time()))
        new_value = random.randint(3, 10)

        current_value = current_config.get("maxDeviceIds", 3)
        current_config["maxDeviceIds"] = new_value

        print(f"\n>>> CHANGE: maxDeviceIds {current_value} → {new_value}")
        print(f">>> Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": current_config}
        )

        assert update_response.status_code == 200

        # Verify
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        updated_value = verify_response.json().get("onboardingConfig", {}).get("maxDeviceIds")

        print(f"\n✅ UPDATED: maxDeviceIds = {updated_value}")
        print(f"⚠️  CHANGE IS PERMANENT - check admin portal now!")

        assert updated_value == new_value

    def test_update_multiple_settings_unique(self, api_client):
        """
        Update: Change multiple settings with unique timestamp-based values.
        ⚠️  DOES NOT RESTORE - changes are permanent!
        """
        print(f"\n{'='*80}")
        print("UPDATE MULTIPLE SETTINGS (UNIQUE)")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        # Generate unique values
        timestamp = int(time.time())
        
        # maxAuthenticationAttempts: rotate between 3-7
        new_max_auth = (timestamp % 5) + 3
        
        # maxDeviceIds: rotate between 2-8
        new_max_devices = (timestamp % 7) + 2
        
        # Toggle all video flags
        toggle_enrollment = not current_config.get("recordEnrollmentVideo", True)
        toggle_authentication = not current_config.get("recordAuthenticationVideo", True)
        toggle_reenrollment = not current_config.get("recordRenrollmentVideo", True)

        print(f"\n>>> CHANGES:")
        print(f"   maxAuthenticationAttempts: {current_config.get('maxAuthenticationAttempts')} → {new_max_auth}")
        print(f"   maxDeviceIds: {current_config.get('maxDeviceIds')} → {new_max_devices}")
        print(f"   recordEnrollmentVideo: {current_config.get('recordEnrollmentVideo')} → {toggle_enrollment}")
        print(f"   recordAuthenticationVideo: {current_config.get('recordAuthenticationVideo')} → {toggle_authentication}")
        print(f"   recordRenrollmentVideo: {current_config.get('recordRenrollmentVideo')} → {toggle_reenrollment}")
        print(f">>> Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Apply changes
        current_config["maxAuthenticationAttempts"] = new_max_auth
        current_config["maxDeviceIds"] = new_max_devices
        current_config["recordEnrollmentVideo"] = toggle_enrollment
        current_config["recordAuthenticationVideo"] = toggle_authentication
        current_config["recordRenrollmentVideo"] = toggle_reenrollment

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": current_config}
        )

        assert update_response.status_code == 200

        # Verify all changes
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified_config = verify_response.json().get("onboardingConfig", {})

        print(f"\n✅ ALL UPDATES VERIFIED:")
        print(f"   maxAuthenticationAttempts: {verified_config.get('maxAuthenticationAttempts')}")
        print(f"   maxDeviceIds: {verified_config.get('maxDeviceIds')}")
        print(f"   recordEnrollmentVideo: {verified_config.get('recordEnrollmentVideo')}")
        print(f"   recordAuthenticationVideo: {verified_config.get('recordAuthenticationVideo')}")
        print(f"   recordRenrollmentVideo: {verified_config.get('recordRenrollmentVideo')}")
        print(f"\n⚠️  ALL CHANGES ARE PERMANENT - check admin portal now!")

        # Verify
        assert verified_config["maxAuthenticationAttempts"] == new_max_auth
        assert verified_config["maxDeviceIds"] == new_max_devices
        assert verified_config["recordEnrollmentVideo"] == toggle_enrollment

    def test_show_current_config(self, api_client):
        """
        Just display current config (no changes).
        Use to verify what's currently in admin portal.
        """
        print(f"\n{'='*80}")
        print("CURRENT CUSTOMER CONFIG")
        print(f"{'='*80}")

        response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert response.status_code == 200

        data = response.json()
        config = data.get("onboardingConfig", {})

        print(f"\n📊 Current Settings:")
        print(f"   Service Version: {data.get('serviceVersion')}")
        print(f"   Expiration: {data.get('expirationTime')}")
        print(f"\n   maxDeviceIds: {config.get('maxDeviceIds')}")
        print(f"   maxAuthenticationAttempts: {config.get('maxAuthenticationAttempts')}")
        print(f"   saveToSubjectManager: {config.get('saveToSubjectManager')}")
        print(f"\n   recordEnrollmentVideo: {config.get('recordEnrollmentVideo')}")
        print(f"   recordAuthenticationVideo: {config.get('recordAuthenticationVideo')}")
        print(f"   recordRenrollmentVideo: {config.get('recordRenrollmentVideo')}")

        print(f"\n📋 Full Config:")
        print(json.dumps(data, indent=4))
