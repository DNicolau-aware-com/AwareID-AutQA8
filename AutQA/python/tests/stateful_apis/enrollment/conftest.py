import pytest

@pytest.fixture
def enrollment_token(api_client, unique_username, env_vars):
    payload = {
        "username": unique_username,
        "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
        "firstName": env_vars.get("FIRSTNAME") or "Test",
        "lastName": env_vars.get("LASTNAME") or "User",
    }
    response = api_client.http_client.post(
        "/onboarding/enrollment/enroll",
        json=payload
    )
    if response.status_code != 200:
        pytest.skip(f"Could not initiate enrollment: {response.status_code}")

    token = response.json().get("enrollmentToken") or response.json().get("etoken")
    if not token:
        pytest.skip("No enrollmentToken returned from /enroll endpoint")

    yield token

    try:
        api_client.http_client.post(
            "/onboarding/enrollment/cancel",
            json={"enrollmentToken": token}
        )
    except Exception:
        pass


@pytest.fixture
def enrolled_user(api_client, unique_username, env_vars, face_frames, workflow):
    enroll_response = api_client.http_client.post(
        "/onboarding/enrollment/enroll",
        json={
            "username": unique_username,
            "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Test",
            "lastName": env_vars.get("LASTNAME") or "User",
        }
    )
    if enroll_response.status_code != 200:
        pytest.skip(f"Enrollment failed: {enroll_response.status_code}")

    enrollment_token = enroll_response.json().get("enrollmentToken")
    if not enrollment_token:
        pytest.skip("No enrollmentToken in enrollment response")

    face_response = api_client.http_client.post(
        "/onboarding/enrollment/addFace",
        json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames,
                    },
                },
            },
        }
    )
    if face_response.status_code != 200:
        pytest.skip(f"Add face failed: {face_response.status_code}")

    yield {
        "username": unique_username,
        "enrollmentToken": enrollment_token,
        "registrationCode": face_response.json().get("registrationCode"),
        "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
    }

    try:
        api_client.http_client.post("/onboarding/enrollment/cancel", json={"enrollmentToken": enrollment_token})
    except Exception:
        pass
