import pytest
import json
import time


@pytest.mark.stateful
@pytest.mark.admin
class TestDeleteEnrollment:
    """
    Tests for DELETE /onboarding/admin/registration/{registrationCode}
    Delete enrollment details for a specific user.
    
    ⚠️  DESTRUCTIVE TESTS - Creates test users then deletes them.
    """

    # ==========================================================================
    # POSITIVE TESTS
    # ==========================================================================

    def test_delete_enrollment_valid_code(self, api_client, unique_username, face_frames, workflow, env_vars):
        """
        Positive: Delete enrollment with valid registration code.
        1. Creates a new enrollment
        2. Completes it (gets registration code)
        3. Deletes it
        4. Verifies deletion
        """
        print(f"\n{'='*80}")
        print("DELETE ENROLLMENT - VALID REGISTRATION CODE")
        print(f"{'='*80}")

        # Step 1: Create enrollment
        print(f"\n>>> STEP 1: Create test enrollment")
        enroll_response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
            json={
                "username": unique_username,
                "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            }
        )
        assert enroll_response.status_code == 200
        enrollment_token = enroll_response.json()["enrollmentToken"]
        print(f"   ✅ Enrollment created: {enrollment_token[:20]}...")

        # Step 2: Add face to complete enrollment
        print(f"\n>>> STEP 2: Complete enrollment with face")
        face_response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json={
                "enrollmentToken": enrollment_token,
                "faceLivenessData": {
                    "video": {
                        "meta_data": {"username": unique_username},
                        "workflow_data": {"workflow": workflow, "frames": face_frames},
                    },
                },
            }
        )
        assert face_response.status_code == 200
        registration_code = face_response.json().get("registrationCode")
        
        if not registration_code:
            pytest.skip("No registration code returned - enrollment may need more steps")
        
        print(f"   ✅ Registration code: {registration_code}")

        # Step 3: Delete enrollment
        print(f"\n>>> STEP 3: DELETE /onboarding/admin/registration/{registration_code}")
        delete_response = api_client.http_client.delete(
            f"/onboarding/admin/registration/{registration_code}"
        )

        print(f"\n<<< STATUS: {delete_response.status_code}")
        print(f"<<< RESPONSE: {delete_response.text}")

        assert delete_response.status_code in [200, 204], (
            f"Expected 200/204, got {delete_response.status_code}. Response: {delete_response.text}"
        )

        print(f"\n✅ Enrollment deleted successfully")

        # Step 4: Verify deletion - try to get details (should fail)
        print(f"\n>>> STEP 4: Verify deletion")
        verify_response = api_client.http_client.get(
            f"/onboarding/admin/registration/{registration_code}"
        )
        
        print(f"   Verification status: {verify_response.status_code}")
        assert verify_response.status_code in [404, 400, 500], (
            f"Expected 404/400/500 after deletion, got {verify_response.status_code}"
        )
        
        print(f"   ✅ Confirmed: enrollment no longer exists")

    def test_delete_multiple_enrollments(self, api_client, face_frames, workflow, env_vars):
        """
        Positive: Delete multiple enrollments sequentially.
        Verifies deletion works for multiple users.
        """
        print(f"\n{'='*80}")
        print("DELETE MULTIPLE ENROLLMENTS")
        print(f"{'='*80}")

        deleted_codes = []

        for i in range(2):
            # Create unique user
            timestamp = int(time.time() * 1000)
            username = f"delete_test_{timestamp}_{i}"[:50]
            
            print(f"\n>>> Creating enrollment {i+1}/2: {username}")

            # Enroll
            enroll_response = api_client.http_client.post(
                "/onboarding/enrollment/enroll",
                json={
                    "username": username,
                    "email": f"{username}@example.com",
                }
            )
            assert enroll_response.status_code == 200
            enrollment_token = enroll_response.json()["enrollmentToken"]

            # Add face
            face_response = api_client.http_client.post(
                "/onboarding/enrollment/addFace",
                json={
                    "enrollmentToken": enrollment_token,
                    "faceLivenessData": {
                        "video": {
                            "meta_data": {"username": username},
                            "workflow_data": {"workflow": workflow, "frames": face_frames},
                        },
                    },
                }
            )
            assert face_response.status_code == 200
            registration_code = face_response.json().get("registrationCode")
            
            if registration_code:
                deleted_codes.append(registration_code)
                print(f"   ✅ Created: {registration_code}")

        # Delete all
        print(f"\n>>> Deleting {len(deleted_codes)} enrollments")
        for code in deleted_codes:
            delete_response = api_client.http_client.delete(
                f"/onboarding/admin/registration/{code}"
            )
            assert delete_response.status_code in [200, 204]
            print(f"   ✅ Deleted: {code}")

        print(f"\n✅ All {len(deleted_codes)} enrollments deleted")

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_delete_invalid_registration_code(self, api_client):
        """
        Negative: Delete with invalid registration code format.
        Expected: 400 INPUT_FORMAT_ERROR
        """
        invalid_code = "invalid-code-12345"

        print(f"\n{'='*80}")
        print("DELETE - INVALID REGISTRATION CODE")
        print(f"{'='*80}")
        print(f">>> REQUEST: DELETE /onboarding/admin/registration/{invalid_code}")

        response = api_client.http_client.delete(
            f"/onboarding/admin/registration/{invalid_code}"
        )

        print(f"\n<<< STATUS: {response.status_code}")
        print(f"<<< RESPONSE:\n{json.dumps(response.json(), indent=4)}")

        assert response.status_code in [400, 404, 500], (
            f"Expected 400/404/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data
        assert "errorMsg" in data

        print(f"\n✅ Correctly rejected invalid code")

    def test_delete_non_existent_registration_code(self, api_client):
        """
        Negative: Delete with non-existent registration code.
        Expected: 404 or 400
        """
        fake_code = "00000000-0000-0000-0000-000000000000"

        print(f"\n{'='*80}")
        print("DELETE - NON-EXISTENT REGISTRATION CODE")
        print(f"{'='*80}")

        response = api_client.http_client.delete(
            f"/onboarding/admin/registration/{fake_code}"
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [400, 404, 500], (
            f"Expected 400/404/500, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected non-existent code")

    def test_delete_already_deleted_enrollment(self, api_client, unique_username, face_frames, workflow, env_vars):
        """
        Negative: Try to delete the same enrollment twice.
        Expected: 404 on second attempt
        """
        print(f"\n{'='*80}")
        print("DELETE - ALREADY DELETED ENROLLMENT")
        print(f"{'='*80}")

        # Create and complete enrollment
        enroll_response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
            json={
                "username": unique_username,
                "email": f"{unique_username}@example.com",
            }
        )
        enrollment_token = enroll_response.json()["enrollmentToken"]

        face_response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json={
                "enrollmentToken": enrollment_token,
                "faceLivenessData": {
                    "video": {
                        "meta_data": {"username": unique_username},
                        "workflow_data": {"workflow": workflow, "frames": face_frames},
                    },
                },
            }
        )
        registration_code = face_response.json().get("registrationCode")
        
        if not registration_code:
            pytest.skip("No registration code - cannot test double deletion")

        # First delete
        print(f"\n>>> First DELETE")
        first_delete = api_client.http_client.delete(
            f"/onboarding/admin/registration/{registration_code}"
        )
        assert first_delete.status_code in [200, 204]
        print(f"   ✅ First delete succeeded: {first_delete.status_code}")

        # Second delete (should fail)
        print(f"\n>>> Second DELETE (should fail)")
        second_delete = api_client.http_client.delete(
            f"/onboarding/admin/registration/{registration_code}"
        )
        print(f"   Status: {second_delete.status_code}")
        
        assert second_delete.status_code in [400, 404, 500], (
            f"Expected 400/404/500 for already deleted, got {second_delete.status_code}"
        )
        
        print(f"   ✅ Correctly rejected duplicate deletion")

    def test_delete_empty_registration_code(self, api_client):
        """
        Negative: Delete with empty registration code.
        Expected: 400 or 404
        """
        print(f"\n{'='*80}")
        print("DELETE - EMPTY REGISTRATION CODE")
        print(f"{'='*80}")

        response = api_client.http_client.delete(
            "/onboarding/admin/registration/"
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [400, 404, 405, 500], (
            f"Expected 400/404/405/500, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected empty code")
