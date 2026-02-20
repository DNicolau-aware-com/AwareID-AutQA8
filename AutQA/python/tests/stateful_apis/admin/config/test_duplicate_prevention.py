import pytest
import json
import copy


@pytest.mark.stateful
@pytest.mark.admin
class TestDuplicatePrevention:
    """
    Tests for Duplicate Enrollment Prevention.
    Nested object: enrollment.checkDuplicateEnrollment { enabled, matchThreshold }
    """

    def test_enable_duplicate_prevention_default(self, api_client):
        """Enable duplicate prevention with default threshold."""
        print(f"\n{'='*80}")
        print("ENABLE DUPLICATE PREVENTION - DEFAULT")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["checkDuplicateEnrollment"] = {
            "enabled": True,
            "matchThreshold": 90
        }

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200

        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("checkDuplicateEnrollment", {})

        print(f"   ✅ Enabled: threshold={verified['matchThreshold']}")
        assert verified["enabled"] is True
        assert verified["matchThreshold"] == 90

    @pytest.mark.parametrize("threshold", [70, 75, 80, 85, 90, 95, 99])
    def test_set_match_threshold(self, api_client, threshold):
        """Test different match thresholds."""
        print(f"\n{'='*80}")
        print(f"MATCH THRESHOLD: {threshold}")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["checkDuplicateEnrollment"] = {
            "enabled": True,
            "matchThreshold": threshold
        }

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        if update_response.status_code == 200:
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("checkDuplicateEnrollment", {})
            
            print(f"   ✅ Threshold: {verified['matchThreshold']}")
            assert verified["matchThreshold"] == threshold

    def test_disable_duplicate_prevention(self, api_client):
        """Disable duplicate prevention."""
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["checkDuplicateEnrollment"] = {
            "enabled": False,
            "matchThreshold": 90
        }

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200

        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("checkDuplicateEnrollment", {})

        print(f"   ✅ Disabled: {verified['enabled']}")
        assert verified["enabled"] is False
