import pytest
import json
import copy


@pytest.mark.stateful
@pytest.mark.admin
class TestAgeEstimation:
    """
    Tests for Age Estimation configuration.
    Nested object: enrollment.ageEstimation { enabled, minAge, maxAge, minTolerance, maxTolerance }
    """

    def test_enable_age_estimation_defaults(self, api_client):
        """Enable age estimation with default values."""
        print(f"\n{'='*80}")
        print("ENABLE AGE ESTIMATION - DEFAULTS")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": 18,
            "maxAge": 65,
            "minTolerance": 1,
            "maxTolerance": 1
        }

        print(f"   Config: {enrollment['ageEstimation']}")

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200

        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("ageEstimation", {})

        print(f"   ✅ Verified: {verified}")
        assert verified["enabled"] is True
        assert verified["minAge"] == 18
        assert verified["maxAge"] == 65

    @pytest.mark.parametrize("min_age,max_age", [
        (18, 65),
        (21, 70),
        (25, 80),
        (16, 100),
    ])
    def test_set_age_range(self, api_client, min_age, max_age):
        """Test different age ranges."""
        print(f"\n{'='*80}")
        print(f"AGE RANGE: {min_age}-{max_age}")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": min_age,
            "maxAge": max_age,
            "minTolerance": 1,
            "maxTolerance": 1
        }

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        if update_response.status_code == 200:
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("ageEstimation", {})
            
            print(f"   ✅ Set: {verified['minAge']}-{verified['maxAge']}")
            assert verified["minAge"] == min_age
            assert verified["maxAge"] == max_age

    @pytest.mark.parametrize("tolerance", [0, 1, 2, 3, 5])
    def test_set_age_tolerance(self, api_client, tolerance):
        """Test different tolerance values."""
        print(f"\n{'='*80}")
        print(f"AGE TOLERANCE: ±{tolerance} years")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": 18,
            "maxAge": 65,
            "minTolerance": tolerance,
            "maxTolerance": tolerance
        }

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        if update_response.status_code == 200:
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("ageEstimation", {})
            
            print(f"   ✅ Tolerance: {verified['minTolerance']}/{verified['maxTolerance']}")
            assert verified["minTolerance"] == tolerance
            assert verified["maxTolerance"] == tolerance

    def test_disable_age_estimation(self, api_client):
        """Disable age estimation."""
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["ageEstimation"] = {
            "enabled": False,
            "minAge": 1,
            "maxAge": 111,
            "minTolerance": 1,
            "maxTolerance": 1
        }

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200

        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("ageEstimation", {})

        print(f"   ✅ Disabled: {verified['enabled']}")
        assert verified["enabled"] is False
