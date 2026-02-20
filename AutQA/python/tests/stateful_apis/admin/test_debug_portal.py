import pytest
import json
import copy
import time


@pytest.mark.stateful
@pytest.mark.admin
class TestDebugPortalUpdates:
    """
    Debug why portal settings aren't updating.
    """

    def test_simple_update_with_verification(self, api_client):
        """
        Simple test: Change ONE setting and verify it appears in portal.
        """
        print(f"\n{'='*80}")
        print("DEBUG: SIMPLE SETTING UPDATE")
        print(f"{'='*80}")

        # Step 1: Get current config
        print(f"\n>>> STEP 1: Get current config")
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert current_response.status_code == 200
        
        current_config = current_response.json().get("onboardingConfig", {})
        current_max_auth = current_config.get("maxAuthenticationAttempts", "NOT_FOUND")
        
        print(f"   Current maxAuthenticationAttempts: {current_max_auth}")

        # Step 2: Change it to something obvious
        print(f"\n>>> STEP 2: Change to obvious value (99)")
        
        new_config = copy.deepcopy(current_config)
        new_config["maxAuthenticationAttempts"] = 99
        
        print(f"   Sending update...")
        print(f"   Payload keys: {list(new_config.keys())}")

        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"\n   <<< STATUS: {update_response.status_code}")
        if update_response.text:
            print(f"   <<< RESPONSE: {update_response.text[:200]}")

        assert update_response.status_code == 200, f"Update failed: {update_response.text}"

        # Step 3: Verify via API
        print(f"\n>>> STEP 3: Verify via API")
        
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified_config = verify_response.json().get("onboardingConfig", {})
        verified_max_auth = verified_config.get("maxAuthenticationAttempts")

        print(f"   API shows: maxAuthenticationAttempts = {verified_max_auth}")
        assert verified_max_auth == 99, f"API verification failed! Got {verified_max_auth}"

        # Step 4: Wait and check again
        print(f"\n>>> STEP 4: Wait 3 seconds, check again")
        time.sleep(3)
        
        recheck_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        recheck_value = recheck_response.json().get("onboardingConfig", {}).get("maxAuthenticationAttempts")
        
        print(f"   After 3s: maxAuthenticationAttempts = {recheck_value}")

        print(f"\n{'='*80}")
        print(f"✅ UPDATE SUCCESSFUL")
        print(f"{'='*80}")
        print(f"   Old value: {current_max_auth}")
        print(f"   New value: {recheck_value}")
        print(f"\n⚠️  NOW CHECK ADMIN PORTAL:")
        print(f"   1. Go to Settings → Summary")
        print(f"   2. Look for 'Max Authentication Attempts'")
        print(f"   3. Should show: 99")
        print(f"   4. If you DON'T see 99, the portal may cache or need refresh")
        print(f"\n   Try:")
        print(f"   - Refresh browser (F5)")
        print(f"   - Hard refresh (Ctrl+F5)")
        print(f"   - Clear cache and reload")
        print(f"   - Log out and log back in")
        print(f"{'='*80}")

    def test_face_toggle_simple(self, api_client):
        """
        Test: Toggle addFace on/off to see if portal updates.
        """
        print(f"\n{'='*80}")
        print("DEBUG: TOGGLE ADD FACE")
        print(f"{'='*80}")

        # Get current
        current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = current_response.json().get("onboardingConfig", {})
        current_add_face = current_config.get("onboardingOptions", {}).get("enrollment", {}).get("addFace", False)

        print(f"\n   Current addFace: {current_add_face}")

        # Toggle it
        new_value = not current_add_face
        new_config = copy.deepcopy(current_config)
        new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})["addFace"] = new_value

        print(f"   Changing to: {new_value}")

        # Update
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )

        print(f"\n   Status: {update_response.status_code}")
        assert update_response.status_code == 200

        # Verify
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {}).get("addFace")

        print(f"   Verified: {verified}")

        print(f"\n⚠️  CHECK PORTAL:")
        print(f"   Settings → Summary → Face")
        print(f"   Add Face toggle should be: {'ON' if new_value else 'OFF'}")
        print(f"   If not visible, try refreshing the page")
