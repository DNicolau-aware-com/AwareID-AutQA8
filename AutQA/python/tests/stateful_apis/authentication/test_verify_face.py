
import pytest


@pytest.mark.stateful
@pytest.mark.authentication
class TestVerifyFace:

    # ==========================================================================
    # POSITIVE TESTS
    # ==========================================================================

    def test_verify_face(self, api_client, enrolled_username, face_frames, workflow):
        """
        Positive: Complete authentication flow - initiate + verifyFace.
        This is what shows as PASSED in the admin portal.

        Response fields per API spec:
            livenessResult  - true = live person
            matchResult     - true = matches enrolled data
            matchScore      - float matching score
            authStatus      - 1=Pending, 2=Complete, 0=Failed
            faceLivenessResults
        """
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
            f"Auth initiation failed: {auth_response.status_code} - {auth_response.text}"
        )
        auth_token = auth_response.json().get("authToken")
        assert auth_token, "Missing authToken"

        # Step 2: Verify face
        verify_payload = {
            "authToken": auth_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {
                        "client_device_brand": "Apple",
                        "client_device_model": "iPhone 8",
                        "client_os_version": "11.0.3",
                        "client_version": "KnomiSLive_v:2.4.1_b:0.0.0_sdk_v:2.4.1_b:0.0.0",
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
            f"Expected 200, got {verify_response.status_code}. Response: {verify_response.text}"
        )
        data = verify_response.json()

        # Validate response fields per API spec
        print(f"\n📋 Response fields:")
        for field in ["livenessResult", "matchResult", "matchScore", "authStatus", "faceLivenessResults"]:
            if field in data:
                print(f"   ✅ PRESENT: {field} = {data[field]}")
            else:
                print(f"   ⚠️  MISSING: {field}")

        # authStatus: 1=Pending, 2=Complete, 0=Failed
        if "authStatus" in data:
            status_map = {0: "Failed", 1: "Pending", 2: "Complete"}
            print(f"\n   authStatus: {data['authStatus']} = {status_map.get(data['authStatus'], 'Unknown')}")
            assert data["authStatus"] in [0, 1, 2], f"Invalid authStatus: {data['authStatus']}"

    def test_response_structure(self, api_client, enrolled_username, face_frames, workflow):
        """
        Positive: Validate all response fields per API spec.
        """
        # Step 1: Initiate authentication
        auth_response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json={"username": enrolled_username}
        )

        print(f"\n>>> STEP 1 STATUS:   {auth_response.status_code}")
        print(f">>> STEP 1 RESPONSE: {auth_response.json()}")

        assert auth_response.status_code == 200
        auth_token = auth_response.json().get("authToken")
        assert auth_token

        # Step 2: Verify face
        verify_response = api_client.http_client.post(
            "/onboarding/authentication/verifyFace",
            json={
                "authToken": auth_token,
                "faceLivenessData": {
                    "video": {
                        "meta_data": {"username": enrolled_username},
                        "workflow_data": {
                            "workflow": workflow,
                            "frames": face_frames,
                        },
                    },
                },
            }
        )

        print(f"\n>>> STEP 2 STATUS:   {verify_response.status_code}")
        print(f">>> STEP 2 RESPONSE: {verify_response.json()}")

        assert verify_response.status_code == 200
        data = verify_response.json()

        # Validate all spec fields
        assert "livenessResult" in data, "Missing livenessResult"
        assert "matchResult" in data, "Missing matchResult"
        assert "matchScore" in data, "Missing matchScore"
        assert "authStatus" in data, "Missing authStatus"
        assert isinstance(data["livenessResult"], bool), "livenessResult must be boolean"
        assert isinstance(data["matchResult"], bool), "matchResult must be boolean"
        assert data["authStatus"] in [0, 1, 2], f"authStatus must be 0, 1 or 2. Got: {data['authStatus']}"

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_invalid_auth_token(self, api_client, face_frames, workflow):
        """
        Negative: verifyFace with invalid authToken.
        Expected: 400 or 500 error.
        """
        payload = {
            "authToken": "cd8d9b72-55bc-4aee-bfc5-a622d4a2a379",
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": "test"},
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames,
                    },
                },
            },
        }

        print(f"\n>>> REQUEST: POST /onboarding/authentication/verifyFace")
        print(f">>> PAYLOAD (authToken): {payload['authToken']}")

        response = api_client.http_client.post(
            "/onboarding/authentication/verifyFace",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data
        assert "errorMsg" in data
        assert "status" in data
        assert "timestamp" in data
        print(f"\n✅ errorCode: {data['errorCode']}")
        print(f"   errorMsg:  {data['errorMsg'][:100]}")

    def test_missing_auth_token(self, api_client, face_frames, workflow):
        """
        Negative: verifyFace without authToken.
        Expected: 400 or 500 error.
        """
        payload = {
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": "test"},
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames,
                    },
                },
            },
        }

        print(f"\n>>> REQUEST: POST /onboarding/authentication/verifyFace")
        print(f">>> PAYLOAD: missing authToken")

        response = api_client.http_client.post(
            "/onboarding/authentication/verifyFace",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data
        assert "errorMsg" in data
        assert "status" in data
        assert "timestamp" in data
        print(f"\n✅ errorCode: {data['errorCode']}")
        print(f"   errorMsg:  {data['errorMsg'][:100]}")
