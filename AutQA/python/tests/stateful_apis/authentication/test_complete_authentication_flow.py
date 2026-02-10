
import pytest


@pytest.mark.stateful
@pytest.mark.authentication
class TestCompleteAuthenticationFlow:

    def test_complete_flow_live(self, api_client, enrolled_username, face_frames, workflow):
        """
        Positive: Complete authentication with LIVE face image.
        Expected:
            livenessResult = true
            decision       = LIVE
        """
        print(f"\n{'='*60}")
        print("COMPLETE AUTHENTICATION FLOW - LIVE IMAGE")
        print(f"{'='*60}")
        print(f"Username: {enrolled_username} | Workflow: {workflow}")

        # Step 1: Initiate authentication
        auth_payload = {"username": enrolled_username}

        print(f"\n>>> STEP 1: POST /onboarding/authentication/authenticate")
        print(f">>> PAYLOAD: {auth_payload}")

        auth_response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json=auth_payload
        )

        print(f"\n<<< STATUS:   {auth_response.status_code}")
        print(f"<<< RESPONSE: {auth_response.json()}")

        assert auth_response.status_code == 200, (
            f"Step 1 failed: {auth_response.status_code} - {auth_response.text}"
        )
        auth_token = auth_response.json().get("authToken")
        assert auth_token, "Missing authToken"
        print(f"\n✅ Step 1 - Auth initiated | Token: {auth_token[:20]}...")

        # Step 2: Verify face with LIVE image
        verify_payload = {
            "authToken": auth_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {
                        "client_device_brand": "Apple",
                        "client_device_model": "iPhone 8",
                        "client_os_version": "11.0.3",
                        "client_version": "KnomiSLive_v:2.4.1_b:0.0.0",
                        "localization": "en-US",
                        "programming_language_version": "Swift 4.1",
                        "username": enrolled_username,
                    },
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames,
                    },
                },
            },
        }

        print(f"\n>>> STEP 2: POST /onboarding/authentication/verifyFace")
        print(f">>> PAYLOAD (authToken): {auth_token[:20]}...")

        verify_response = api_client.http_client.post(
            "/onboarding/authentication/verifyFace",
            json=verify_payload
        )

        print(f"\n<<< STATUS:   {verify_response.status_code}")
        print(f"<<< RESPONSE: {verify_response.json()}")

        assert verify_response.status_code == 200, (
            f"Step 2 failed: {verify_response.status_code} - {verify_response.text}"
        )
        data = verify_response.json()

        # Log results
        auth_status_map = {0: "Failed", 1: "Pending", 2: "Complete"}
        print(f"\n📋 Results:")
        print(f"   livenessResult: {data.get('livenessResult', 'N/A')}")
        print(f"   matchResult:    {data.get('matchResult', 'N/A')}")
        print(f"   matchScore:     {data.get('matchScore', 'N/A')}%")
        print(f"   authStatus:     {data.get('authStatus', 'N/A')} = {auth_status_map.get(data.get('authStatus'), 'N/A')}")

        # Log liveness detail
        liveness_detail = data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        if liveness_detail:
            print(f"\n📋 Liveness Detail:")
            print(f"   decision:  {liveness_detail.get('decision', 'N/A')}")
            print(f"   score_frr: {liveness_detail.get('score_frr', 'N/A')}")
            print(f"   feedback:  {liveness_detail.get('feedback', [])}")

        # Assertions - LIVE image must pass liveness
        assert "livenessResult" in data, "Missing livenessResult"
        assert "matchResult" in data, "Missing matchResult"
        assert "matchScore" in data, "Missing matchScore"
        assert "authStatus" in data, "Missing authStatus"
        assert data["authStatus"] in [0, 1, 2], f"Invalid authStatus: {data['authStatus']}"

        if liveness_detail:
            decision = liveness_detail.get("decision")
            assert decision == "LIVE", (
                f"Liveness check failed! Expected 'LIVE' got '{decision}'. "
                f"score_frr={liveness_detail.get('score_frr', 'N/A')}"
            )
            print(f"\n✅ decision: {decision} - LIVE confirmed")

        assert data["livenessResult"] is True, (
            f"livenessResult is False - sample is NOT from a live person. Response: {data}"
        )
        print(f"\n✅ livenessResult: {data['livenessResult']} - LIVE person confirmed")

    def test_complete_flow_spoof(self, api_client, enrolled_username, env_vars, workflow):
        """
        Negative: Complete authentication with SPOOF image.
        Expected:
            livenessResult = false
            decision       != LIVE
        """
        # Load spoof image from .env
        spoof_image = (
            env_vars.get("SPOOF") or
            env_vars.get("SPOOF_FACE") or
            env_vars.get("SPOOF_IMAGE")
        )
        if not spoof_image:
            pytest.skip("Spoof image not found in .env (set SPOOF=<base64>)")

        if spoof_image.startswith("data:image"):
            spoof_image = spoof_image.split(",")[1]
        spoof_image = spoof_image.strip()

        # Build spoof frames
        import time
        now_ms = int(time.time() * 1000)
        spoof_frames = [
            {"data": spoof_image, "timestamp": now_ms + (i * 30), "tags": []}
            for i in range(3)
        ]

        print(f"\n{'='*60}")
        print("COMPLETE AUTHENTICATION FLOW - SPOOF IMAGE")
        print(f"{'='*60}")
        print(f"Username: {enrolled_username} | Workflow: {workflow}")

        # Step 1: Initiate authentication
        auth_payload = {"username": enrolled_username}

        print(f"\n>>> STEP 1: POST /onboarding/authentication/authenticate")
        print(f">>> PAYLOAD: {auth_payload}")

        auth_response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json=auth_payload
        )

        print(f"\n<<< STATUS:   {auth_response.status_code}")
        print(f"<<< RESPONSE: {auth_response.json()}")

        assert auth_response.status_code == 200, (
            f"Step 1 failed: {auth_response.status_code} - {auth_response.text}"
        )
        auth_token = auth_response.json().get("authToken")
        assert auth_token, "Missing authToken"
        print(f"\n✅ Step 1 - Auth initiated | Token: {auth_token[:20]}...")

        # Step 2: Verify face with SPOOF image
        verify_payload = {
            "authToken": auth_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {
                        "client_device_brand": "Apple",
                        "client_device_model": "iPhone 8",
                        "client_os_version": "11.0.3",
                        "client_version": "KnomiSLive_v:2.4.1_b:0.0.0",
                        "localization": "en-US",
                        "programming_language_version": "Swift 4.1",
                        "username": enrolled_username,
                    },
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": spoof_frames,
                    },
                },
            },
        }

        print(f"\n>>> STEP 2: POST /onboarding/authentication/verifyFace (SPOOF)")
        print(f">>> PAYLOAD (authToken): {auth_token[:20]}...")

        verify_response = api_client.http_client.post(
            "/onboarding/authentication/verifyFace",
            json=verify_payload
        )

        print(f"\n<<< STATUS:   {verify_response.status_code}")
        print(f"<<< RESPONSE: {verify_response.json()}")

        assert verify_response.status_code == 200, (
            f"Step 2 failed: {verify_response.status_code} - {verify_response.text}"
        )
        data = verify_response.json()

        # Log results
        auth_status_map = {0: "Failed", 1: "Pending", 2: "Complete"}
        print(f"\n📋 Results:")
        print(f"   livenessResult: {data.get('livenessResult', 'N/A')}")
        print(f"   matchResult:    {data.get('matchResult', 'N/A')}")
        print(f"   matchScore:     {data.get('matchScore', 'N/A')}%")
        print(f"   authStatus:     {data.get('authStatus', 'N/A')} = {auth_status_map.get(data.get('authStatus'), 'N/A')}")

        # Log liveness detail
        liveness_detail = data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        if liveness_detail:
            print(f"\n📋 Liveness Detail:")
            print(f"   decision:  {liveness_detail.get('decision', 'N/A')}")
            print(f"   score_frr: {liveness_detail.get('score_frr', 'N/A')}")
            print(f"   feedback:  {liveness_detail.get('feedback', [])}")

        # Assertions - SPOOF image must FAIL liveness
        assert "livenessResult" in data, "Missing livenessResult"

        if liveness_detail:
            decision = liveness_detail.get("decision")
            assert decision != "LIVE", (
                f"Spoof detection failed! Expected NOT 'LIVE' but got '{decision}'. "
                f"score_frr={liveness_detail.get('score_frr', 'N/A')}"
            )
            print(f"\n✅ decision: {decision} - SPOOF correctly detected")

        assert data["livenessResult"] is False, (
            f"livenessResult is True - SPOOF was not detected! Response: {data}"
        )
        print(f"\n✅ livenessResult: {data['livenessResult']} - SPOOF correctly detected")
