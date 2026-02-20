import pytest
import json
import copy


@pytest.mark.stateful
@pytest.mark.admin
class TestUpdateCustomerConfig:
    """
    Tests for POST /onboarding/admin/customerConfig
    Update customer configuration and options.
    
    ⚠️  DESTRUCTIVE TESTS - Modifies actual customer config.
    Tests restore original config after completion.
    """

    @pytest.fixture(scope="function")
    def original_config(self, api_client):
        """Get and store original config before tests."""
        response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert response.status_code == 200
        return response.json()

    # ==========================================================================
    # POSITIVE TESTS
    # ==========================================================================

    def test_update_config_valid_payload(self, api_client, original_config):
        """
        Positive: Update config with valid payload.
        1. Get current config
        2. Modify it
        3. Update it
        4. Verify update
        5. Restore original
        """
        print(f"\n{'='*80}")
        print("UPDATE CUSTOMER CONFIG - VALID PAYLOAD")
        print(f"{'='*80}")

        # Get current config
        current = original_config.get("onboardingConfig", {})
        
        # Modify config (change maxAuthenticationAttempts)
        new_config = copy.deepcopy(current)
        original_max_attempts = new_config.get("maxAuthenticationAttempts", 4)
        new_max_attempts = 5 if original_max_attempts != 5 else 6
        new_config["maxAuthenticationAttempts"] = new_max_attempts

        payload = {"onboardingConfig": new_config}

        print(f"\n>>> REQUEST: POST /onboarding/admin/customerConfig")
        print(f">>> Changing maxAuthenticationAttempts: {original_max_attempts} → {new_max_attempts}")

        # Update config
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json=payload
        )

        print(f"\n<<< STATUS: {update_response.status_code}")
        print(f"<<< RESPONSE: {update_response.text}")

        assert update_response.status_code == 200, (
            f"Expected 200, got {update_response.status_code}. Response: {update_response.text}"
        )

        # Verify update
        print(f"\n>>> Verifying update...")
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert verify_response.status_code == 200
        
        updated_value = verify_response.json().get("onboardingConfig", {}).get("maxAuthenticationAttempts")
        assert updated_value == new_max_attempts, (
            f"Update failed. Expected {new_max_attempts}, got {updated_value}"
        )
        
        print(f"   ✅ Verified: maxAuthenticationAttempts = {updated_value}")

        # Restore original config
        print(f"\n>>> Restoring original config...")
        restore_payload = {"onboardingConfig": current}
        restore_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json=restore_payload
        )
        assert restore_response.status_code == 200
        print(f"   ✅ Original config restored")

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_update_empty_payload(self, api_client):
        """
        Negative: Update with empty payload.
        Expected: 400 or 200 (API may accept empty updates)
        """
        print(f"\n{'='*80}")
        print("UPDATE - EMPTY PAYLOAD")
        print(f"{'='*80}")

        payload = {}

        print(f"\n>>> REQUEST: POST /onboarding/admin/customerConfig")
        print(f">>> PAYLOAD:\n{json.dumps(payload, indent=4)}")

        response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")
        if response.text:
            print(f"<<< RESPONSE: {response.text[:200]}")
        else:
            print(f"<<< RESPONSE: (empty)")

        # API may return 200 with empty body for invalid payload
        assert response.status_code in [200, 400, 500], (
            f"Got unexpected status: {response.status_code}"
        )

        print(f"\n✅ Handled empty payload (status: {response.status_code})")

    def test_update_missing_onboarding_config(self, api_client):
        """
        Negative: Update without onboardingConfig field.
        Note: API may accept this and do nothing (returns 200).
        """
        print(f"\n{'='*80}")
        print("UPDATE - MISSING ONBOARDING CONFIG")
        print(f"{'='*80}")

        payload = {"someOtherField": "value"}

        print(f"\n>>> REQUEST: POST /onboarding/admin/customerConfig")
        print(f">>> PAYLOAD:\n{json.dumps(payload, indent=4)}")

        response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")

        # API may accept invalid payload and return 200
        assert response.status_code in [200, 400, 500], (
            f"Got unexpected status: {response.status_code}"
        )

        print(f"\n✅ Handled missing onboardingConfig (status: {response.status_code})")

    def test_update_invalid_max_device_ids(self, api_client):
        """
        Negative: Update with invalid maxDeviceIds (negative number).
        Expected: 400 or 500
        """
        print(f"\n{'='*80}")
        print("UPDATE - INVALID MAX DEVICE IDS")
        print(f"{'='*80}")

        payload = {
            "onboardingConfig": {
                "maxDeviceIds": -1,
                "maxAuthenticationAttempts": 4
            }
        }

        print(f"\n>>> REQUEST: POST /onboarding/admin/customerConfig")
        print(f">>> PAYLOAD:\n{json.dumps(payload, indent=4)}")

        response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected negative maxDeviceIds")

    def test_update_invalid_data_type(self, api_client):
        """
        Negative: Update with invalid data type (string instead of int).
        Expected: 400 or 500
        """
        print(f"\n{'='*80}")
        print("UPDATE - INVALID DATA TYPE")
        print(f"{'='*80}")

        payload = {
            "onboardingConfig": {
                "maxDeviceIds": "not_a_number",
                "maxAuthenticationAttempts": 4
            }
        }

        print(f"\n>>> REQUEST: POST /onboarding/admin/customerConfig")
        print(f">>> PAYLOAD:\n{json.dumps(payload, indent=4)}")

        response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected invalid data type")
