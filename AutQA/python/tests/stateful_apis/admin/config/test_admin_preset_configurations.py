import pytest
import json
import copy


@pytest.mark.stateful
@pytest.mark.admin
class TestPresetConfigurations:
    """
    Common enrollment configuration presets.
    Complete configurations for typical use cases.
    """

    def test_preset_face_only_basic(self, api_client):
        """
        Preset: Face only (basic).
        - addFace: enabled
        - No age estimation
        - No duplicate prevention
        """
        print(f"\n{'='*80}")
        print("PRESET: FACE ONLY (BASIC)")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        # Only face enabled
        enrollment["addFace"] = True
        enrollment["addDevice"] = False
        enrollment["addDocument"] = False
        enrollment["addVoice"] = False
        enrollment["addPIN"] = False
        
        # Disable extras
        enrollment["ageEstimation"] = {"enabled": False, "minAge": 1, "maxAge": 111, "minTolerance": 1, "maxTolerance": 1}
        enrollment["checkDuplicateEnrollment"] = {"enabled": False, "matchThreshold": 90}

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200
        print(f"   ✅ Applied: Face Only (Basic)")

    def test_preset_face_with_age_verification(self, api_client):
        """
        Preset: Face with age verification.
        - addFace: enabled
        - Age estimation: 18-65, ±2 years
        - No duplicate prevention
        """
        print(f"\n{'='*80}")
        print("PRESET: FACE + AGE VERIFICATION")
        print(f"{'='*80}")

        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["addFace"] = True
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": 18,
            "maxAge": 65,
            "minTolerance": 2,
            "maxTolerance": 2
        }
        enrollment["checkDuplicateEnrollment"] = {"enabled": False, "matchThreshold": 90}

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200
        print(f"   ✅ Applied: Face + Age Verification (18-65)")

    def test_preset_face_with_duplicate_prevention(self, api_client):
        """
        Preset: Face with duplicate prevention.
        - addFace: enabled
        - No age estimation
        - Duplicate prevention: enabled, 85% threshold
        """
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["addFace"] = True
        enrollment["ageEstimation"] = {"enabled": False, "minAge": 1, "maxAge": 111, "minTolerance": 1, "maxTolerance": 1}
        enrollment["checkDuplicateEnrollment"] = {"enabled": True, "matchThreshold": 85}

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200
        print(f"   ✅ Applied: Face + Duplicate Prevention")

    def test_preset_complete_face_verification(self, api_client):
        """
        Preset: Complete face verification.
        - addFace: enabled
        - Age estimation: 21-70, ±3 years
        - Duplicate prevention: enabled, 90% threshold
        """
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["addFace"] = True
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": 21,
            "maxAge": 70,
            "minTolerance": 3,
            "maxTolerance": 3
        }
        enrollment["checkDuplicateEnrollment"] = {
            "enabled": True,
            "matchThreshold": 90
        }

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200
        print(f"   ✅ Applied: Complete Face Verification")

    def test_preset_multimodal_biometric(self, api_client):
        """
        Preset: Multimodal biometric.
        - addFace, addDevice, addDocument: enabled
        - Age estimation: enabled
        - Duplicate prevention: enabled
        """
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        enrollment["addFace"] = True
        enrollment["addDevice"] = True
        enrollment["addDocument"] = True
        enrollment["addVoice"] = False
        enrollment["addPIN"] = False
        
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": 18,
            "maxAge": 65,
            "minTolerance": 1,
            "maxTolerance": 1
        }
        enrollment["checkDuplicateEnrollment"] = {
            "enabled": True,
            "matchThreshold": 90
        }

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        assert update_response.status_code == 200
        print(f"   ✅ Applied: Multimodal Biometric (Face + Device + Document)")
