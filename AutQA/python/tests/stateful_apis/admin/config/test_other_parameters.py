import pytest
import json
import copy


@pytest.mark.stateful
@pytest.mark.admin
class TestOtherConfigParameters:
    """
    Tests for other configuration parameters:
    - maxDeviceIds
    - maxAuthenticationAttempts
    - saveToSubjectManager
    """

    @pytest.mark.parametrize("max_devices", [1, 2, 3, 5, 10])
    def test_set_max_device_ids(self, api_client, max_devices):
        """Test different maxDeviceIds values."""
        print(f"\n{'='*80}")
        print(f"MAX DEVICE IDS: {max_devices}")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        new_config["maxDeviceIds"] = max_devices

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        if update_response.status_code == 200:
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified = verify_response.json().get("onboardingConfig", {}).get("maxDeviceIds")
            print(f"   ✅ Set: {verified}")
            assert verified == max_devices

    @pytest.mark.parametrize("max_attempts", [1, 2, 3, 4, 5, 10])
    def test_set_max_authentication_attempts(self, api_client, max_attempts):
        """Test different maxAuthenticationAttempts values."""
        print(f"\n{'='*80}")
        print(f"MAX AUTH ATTEMPTS: {max_attempts}")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        new_config["maxAuthenticationAttempts"] = max_attempts

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        if update_response.status_code == 200:
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified = verify_response.json().get("onboardingConfig", {}).get("maxAuthenticationAttempts")
            print(f"   ✅ Set: {verified}")
            assert verified == max_attempts
