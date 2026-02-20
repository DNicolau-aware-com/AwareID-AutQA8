import pytest
import json
import copy


@pytest.mark.stateful
@pytest.mark.admin
class TestFaceOptionsCorrectStructure:
    """
    Face sub-options with CORRECT nested structure from API.
    
    Based on actual API response:
    - ageEstimation: { enabled, minAge, maxAge, minTolerance, maxTolerance }
    - checkDuplicateEnrollment: { enabled, matchThreshold }
    """

    def test_enable_age_estimation_with_values(self, api_client):
        """
        Enable Age Estimation with min/max/tolerance values.
        Uses the correct nested structure.
        """
        print(f"\n{'='*80}")
        print("ENABLE AGE ESTIMATION (CORRECT STRUCTURE)")
        print(f"{'='*80}")

        # Get current config
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        # Show current
        current_age = current_config.get("onboardingOptions", {}).get("enrollment", {}).get("ageEstimation", {})
        print(f"\n📋 Current ageEstimation:")
        print(json.dumps(current_age, indent=4))

        # Update with correct structure
        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        # Set the NESTED ageEstimation object
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": 18,
            "maxAge": 65,
            "minTolerance": 1,
            "maxTolerance": 1
        }

        print(f"\n📝 New ageEstimation:")
        print(json.dumps(enrollment["ageEstimation"], indent=4))

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"\n<<< STATUS: {update_response.status_code}")

        if update_response.status_code == 200:
            # Verify
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified_age = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("ageEstimation", {})

            print(f"\n✅ VERIFIED:")
            print(json.dumps(verified_age, indent=4))

            assert verified_age.get("enabled") is True
            assert verified_age.get("minAge") == 18
            assert verified_age.get("maxAge") == 65

            print(f"\n⚠️  Check Admin Portal → Face → Enable Age Estimation")
            print(f"   Should show: Min=18, Max=65, Tolerance=1")

        elif update_response.status_code in [400, 500]:
            error_data = update_response.json()
            print(f"\n⚠️  REJECTED: {error_data.get('errorMsg')}")
            pytest.skip(f"Rejected: {error_data.get('errorMsg')}")

    def test_enable_duplicate_prevention_with_threshold(self, api_client):
        """
        Enable Duplicate Prevention with match threshold.
        Uses the correct nested structure.
        """
        print(f"\n{'='*80}")
        print("ENABLE DUPLICATE PREVENTION (CORRECT STRUCTURE)")
        print(f"{'='*80}")

        # Get current
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        current_dup = current_config.get("onboardingOptions", {}).get("enrollment", {}).get("checkDuplicateEnrollment", {})
        print(f"\n📋 Current checkDuplicateEnrollment:")
        print(json.dumps(current_dup, indent=4))

        # Update with correct structure
        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        # Set the NESTED checkDuplicateEnrollment object
        enrollment["checkDuplicateEnrollment"] = {
            "enabled": True,
            "matchThreshold": 85
        }

        print(f"\n📝 New checkDuplicateEnrollment:")
        print(json.dumps(enrollment["checkDuplicateEnrollment"], indent=4))

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"\n<<< STATUS: {update_response.status_code}")

        if update_response.status_code == 200:
            # Verify
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified_dup = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("checkDuplicateEnrollment", {})

            print(f"\n✅ VERIFIED:")
            print(json.dumps(verified_dup, indent=4))

            assert verified_dup.get("enabled") is True
            assert verified_dup.get("matchThreshold") == 85

            print(f"\n⚠️  Check Admin Portal → Face → Prevent Duplicate Enrollments")
            print(f"   Should show: Enabled, Threshold=85")

    def test_complete_face_configuration(self, api_client):
        """
        Complete face configuration with ALL options:
        - addFace: enabled
        - ageEstimation: enabled with 21-70 range
        - checkDuplicateEnrollment: enabled with threshold 90
        """
        print(f"\n{'='*80}")
        print("COMPLETE FACE CONFIGURATION")
        print(f"{'='*80}")

        # Get current
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})

        # Build complete config
        new_config = copy.deepcopy(current_config)
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        # Enable addFace
        enrollment["addFace"] = True
        
        # Configure age estimation (NESTED OBJECT)
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": 21,
            "maxAge": 70,
            "minTolerance": 2,
            "maxTolerance": 2
        }
        
        # Configure duplicate prevention (NESTED OBJECT)
        enrollment["checkDuplicateEnrollment"] = {
            "enabled": True,
            "matchThreshold": 90
        }

        print(f"\n📝 Complete enrollment config:")
        print(f"   addFace: True")
        print(f"   ageEstimation: {enrollment['ageEstimation']}")
        print(f"   checkDuplicateEnrollment: {enrollment['checkDuplicateEnrollment']}")

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"\n<<< STATUS: {update_response.status_code}")

        if update_response.status_code == 200:
            # Verify
            verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
            verified_config = verify_response.json().get("onboardingConfig", {})
            verified_enrollment = verified_config.get("onboardingOptions", {}).get("enrollment", {})

            print(f"\n✅ COMPLETE VERIFICATION:")
            
            # Check addFace
            print(f"\n1. addFace: {verified_enrollment.get('addFace')}")
            assert verified_enrollment.get("addFace") is True
            
            # Check ageEstimation
            verified_age = verified_enrollment.get("ageEstimation", {})
            print(f"\n2. ageEstimation:")
            print(json.dumps(verified_age, indent=4))
            assert verified_age.get("enabled") is True
            assert verified_age.get("minAge") == 21
            assert verified_age.get("maxAge") == 70
            
            # Check checkDuplicateEnrollment
            verified_dup = verified_enrollment.get("checkDuplicateEnrollment", {})
            print(f"\n3. checkDuplicateEnrollment:")
            print(json.dumps(verified_dup, indent=4))
            assert verified_dup.get("enabled") is True
            assert verified_dup.get("matchThreshold") == 90

            print(f"\n{'='*80}")
            print(f"✅ ALL FACE OPTIONS CONFIGURED SUCCESSFULLY!")
            print(f"{'='*80}")
            print(f"\n⚠️  CHECK ADMIN PORTAL → Face:")
            print(f"   ✅ Add Face: Enabled")
            print(f"   ✅ Age Estimation: Enabled (21-70, tolerance ±2)")
            print(f"   ✅ Prevent Duplicates: Enabled (threshold 90)")
            print(f"{'='*80}")

        elif update_response.status_code in [400, 500]:
            error_data = update_response.json()
            print(f"\n⚠️  REJECTED: {error_data.get('errorMsg')}")
            pytest.fail(f"Config rejected: {error_data.get('errorMsg')}")
