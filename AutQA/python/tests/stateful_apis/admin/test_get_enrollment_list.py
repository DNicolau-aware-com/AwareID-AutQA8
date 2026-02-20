import pytest
import json


@pytest.mark.stateful
@pytest.mark.admin
class TestGetEnrollmentList:
    """
    Tests for GET /onboarding/admin/registration
    Get completed enrollment list with pagination.
    """

    # ==========================================================================
    # POSITIVE TESTS
    # ==========================================================================

    def test_get_enrollment_list_default_pagination(self, api_client):
        """
        Positive: Get enrollment list with default pagination.
        Request first page with 100 records.
        """
        payload = {
            "pageNumber": 1,
            "pageSize": 100
        }

        print(f"\n{'='*80}")
        print("GET ENROLLMENT LIST - DEFAULT PAGINATION")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/admin/registration")
        print(f">>> PAYLOAD:\n{json.dumps(payload, indent=4)}")

        response = api_client.http_client.post(
            "/onboarding/admin/registration",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")
        print(f"<<< RESPONSE:\n{json.dumps(response.json(), indent=4)}")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()

        # Validate response structure
        assert "pageNumber" in data, "Missing pageNumber"
        assert "pageSize" in data, "Missing pageSize"
        assert "totalPages" in data, "Missing totalPages"
        assert "totalRecords" in data, "Missing totalRecords"
        assert "list" in data, "Missing list"

        # Validate pagination values
        assert data["pageNumber"] == 1, f"Expected pageNumber 1, got {data['pageNumber']}"
        assert data["pageSize"] == 100, f"Expected pageSize 100, got {data['pageSize']}"
        assert isinstance(data["list"], list), "list must be an array"

        print(f"\n✅ Enrollment list retrieved")
        print(f"   Total records: {data['totalRecords']}")
        print(f"   Total pages: {data['totalPages']}")
        print(f"   Records in this page: {len(data['list'])}")

    def test_get_enrollment_list_small_page_size(self, api_client):
        """
        Positive: Get enrollment list with small page size (10 records).
        Tests pagination with smaller batches.
        """
        payload = {
            "pageNumber": 1,
            "pageSize": 10
        }

        print(f"\n{'='*80}")
        print("GET ENROLLMENT LIST - SMALL PAGE SIZE")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/admin/registration")
        print(f">>> PAYLOAD:\n{json.dumps(payload, indent=4)}")

        response = api_client.http_client.post(
            "/onboarding/admin/registration",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code == 200
        data = response.json()

        assert data["pageSize"] == 10, f"Expected pageSize 10, got {data['pageSize']}"
        assert len(data["list"]) <= 10, f"Expected max 10 records, got {len(data['list'])}"

        print(f"\n✅ Small page size working")
        print(f"   Page size: {data['pageSize']}")
        print(f"   Records returned: {len(data['list'])}")

    def test_get_enrollment_list_second_page(self, api_client):
        """
        Positive: Get second page of enrollment list.
        Tests multi-page pagination.
        """
        payload = {
            "pageNumber": 2,
            "pageSize": 10
        }

        print(f"\n{'='*80}")
        print("GET ENROLLMENT LIST - SECOND PAGE")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/admin/registration")
        print(f">>> PAYLOAD:\n{json.dumps(payload, indent=4)}")

        response = api_client.http_client.post(
            "/onboarding/admin/registration",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code == 200
        data = response.json()

        assert data["pageNumber"] == 2, f"Expected pageNumber 2, got {data['pageNumber']}"

        print(f"\n✅ Second page retrieved")
        print(f"   Page: {data['pageNumber']}/{data['totalPages']}")
        print(f"   Records: {len(data['list'])}")

    def test_response_structure_validation(self, api_client):
        """
        Positive: Validate complete response structure per API spec.
        """
        payload = {"pageNumber": 1, "pageSize": 5}

        print(f"\n{'='*80}")
        print("RESPONSE STRUCTURE VALIDATION")
        print(f"{'='*80}")

        response = api_client.http_client.post(
            "/onboarding/admin/registration",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields per API spec
        required_fields = ["pageNumber", "pageSize", "totalPages", "totalRecords", "list"]

        print(f"\n📋 Validating response structure:")
        for field in required_fields:
            if field in data:
                print(f"   ✅ {field}: {data[field] if field != 'list' else f'{len(data[field])} records'}")
                assert field in data, f"Missing required field: {field}"
            else:
                print(f"   ❌ MISSING: {field}")
                pytest.fail(f"Missing required field: {field}")

        # Validate list contains enrollment records
        if data["list"]:
            first_record = data["list"][0]
            print(f"\n📋 First record keys: {list(first_record.keys())}")

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_missing_page_number(self, api_client):
        """
        Negative: Request without pageNumber.
        Expected: 400 INPUT_FORMAT_ERROR or INPUT_VALUES_ERROR
        """
        payload = {"pageSize": 100}

        print(f"\n{'='*80}")
        print("MISSING PAGE NUMBER")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/admin/registration")
        print(f">>> PAYLOAD:\n{json.dumps(payload, indent=4)}")

        response = api_client.http_client.post(
            "/onboarding/admin/registration",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")
        print(f"<<< RESPONSE:\n{json.dumps(response.json(), indent=4)}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data
        assert "errorMsg" in data
        assert "status" in data
        assert "timestamp" in data

        print(f"\n✅ Correctly rejected missing pageNumber")

    def test_missing_page_size(self, api_client):
        """
        Negative: Request without pageSize.
        Expected: 400 INPUT_FORMAT_ERROR or INPUT_VALUES_ERROR
        """
        payload = {"pageNumber": 1}

        print(f"\n{'='*80}")
        print("MISSING PAGE SIZE")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/admin/registration")
        print(f">>> PAYLOAD:\n{json.dumps(payload, indent=4)}")

        response = api_client.http_client.post(
            "/onboarding/admin/registration",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")
        print(f"<<< RESPONSE:\n{json.dumps(response.json(), indent=4)}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data

        print(f"\n✅ Correctly rejected missing pageSize")

    def test_invalid_page_number_zero(self, api_client):
        """
        Negative: Request with pageNumber = 0.
        Expected: 400 or validation error
        """
        payload = {"pageNumber": 0, "pageSize": 100}

        print(f"\n{'='*80}")
        print("INVALID PAGE NUMBER (0)")
        print(f"{'='*80}")

        response = api_client.http_client.post(
            "/onboarding/admin/registration",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500 for pageNumber=0, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected pageNumber=0")

    def test_invalid_page_size_zero(self, api_client):
        """
        Negative: Request with pageSize = 0.
        Expected: 400 or validation error
        """
        payload = {"pageNumber": 1, "pageSize": 0}

        print(f"\n{'='*80}")
        print("INVALID PAGE SIZE (0)")
        print(f"{'='*80}")

        response = api_client.http_client.post(
            "/onboarding/admin/registration",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500 for pageSize=0, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected pageSize=0")

    def test_empty_payload(self, api_client):
        """
        Negative: Request with empty payload.
        Expected: 400 INPUT_FORMAT_ERROR
        """
        payload = {}

        print(f"\n{'='*80}")
        print("EMPTY PAYLOAD")
        print(f"{'='*80}")

        response = api_client.http_client.post(
            "/onboarding/admin/registration",
            json=payload
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500 for empty payload, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected empty payload")
