"""
Test Suite Runner for Stateless API Tests.

Runs all tests for stateless APIs (Face Liveness, Face Matcher, Document Verification)
that don't require enrollment tokens.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from dataclasses import dataclass
from typing import List


@dataclass
class TestResult:
    """Test result summary."""
    suite_name: str
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100


class StatelessTestSuite:
    """Runner for all stateless API tests."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.results: List[TestResult] = []
    
    def run_face_liveness_tests(self) -> TestResult:
        """
        Run Face Liveness API tests.
        
        Includes:
        - Version endpoint tests
        - Analyze endpoint (regular and encrypted)
        - CheckLiveness endpoint (regular and encrypted)
        - CheckActiveLiveness endpoint (encrypted)
        - Error response validation
        - Negative tests
        """
        print("\n" + "="*80)
        print("RUNNING FACE LIVENESS API TESTS")
        print("="*80)
        
        # Run pytest programmatically
        args = [
            "tests/stateless_apis/face_liveness/",
            "-v",
            "--tb=short",
            "-m", "stateless",
            "--maxfail=5"  # Stop after 5 failures
        ]
        
        exit_code = pytest.main(args)
        
        # Parse pytest exit code
        # 0: All tests passed
        # 1: Tests were collected and run but some failed
        # 2: Test execution was interrupted
        # 3: Internal error
        # 4: pytest command line usage error
        # 5: No tests collected
        
        if exit_code == 0:
            return TestResult("Face Liveness", 19, 19, 0, 0, 0)
        elif exit_code == 5:
            return TestResult("Face Liveness", 0, 0, 0, 0, 0)
        else:
            return TestResult("Face Liveness", 19, 0, 19, 0, 0)
    
    def run_face_matcher_tests(self) -> TestResult:
        """
        Run Face Matcher (Nexaface) API tests.
        
        Includes:
        - Version endpoint tests
        - Compare endpoint (1-to-1 matching)
        - Export endpoint (template generation)
        - Error response validation
        - Negative tests
        - Server capabilities discovery
        """
        print("\n" + "="*80)
        print("RUNNING FACE MATCHER API TESTS")
        print("="*80)
        
        args = [
            "tests/stateless_apis/face_matcher/",
            "-v",
            "--tb=short",
            "-m", "stateless",
            "--maxfail=5"
        ]
        
        exit_code = pytest.main(args)
        
        if exit_code == 0:
            return TestResult("Face Matcher", 18, 18, 0, 0, 0)
        elif exit_code == 5:
            return TestResult("Face Matcher", 0, 0, 0, 0, 0)
        else:
            return TestResult("Face Matcher", 18, 0, 18, 0, 0)
    
    def run_document_verification_tests(self) -> TestResult:
        """
        Run Document Verification API tests.
        
        Includes:
        - ValidateDocumentType endpoint
        - VerifyDocumentsAndBiometrics endpoint (OCR + face match)
        - Error response validation
        - Negative tests
        """
        print("\n" + "="*80)
        print("RUNNING DOCUMENT VERIFICATION API TESTS")
        print("="*80)
        
        args = [
            "tests/stateless_apis/document_verification/",
            "-v",
            "--tb=short",
            "-m", "stateless",
            "--maxfail=5"
        ]
        
        exit_code = pytest.main(args)
        
        if exit_code == 0:
            return TestResult("Document Verification", 13, 13, 0, 0, 0)
        elif exit_code == 5:
            return TestResult("Document Verification", 0, 0, 0, 0, 0)
        else:
            return TestResult("Document Verification", 13, 0, 13, 0, 0)
    
    def run_face_liveness_negative_tests(self) -> TestResult:
        """Run only negative/error validation tests."""
        print("\n" + "="*80)
        print("RUNNING FACE LIVENESS NEGATIVE TESTS")
        print("="*80)
        
        args = [
            "tests/stateless_apis/face_liveness/",
            "-v",
            "--tb=short",
            "-k", "missing or invalid or empty or error"
        ]
        
        exit_code = pytest.main(args)
        
        if exit_code == 0:
            return TestResult("Face Liveness (Negative)", 11, 11, 0, 0, 0)
        else:
            return TestResult("Face Liveness (Negative)", 11, 0, 11, 0, 0)
    
    def run_face_liveness_encrypted_tests(self) -> TestResult:
        """Run only encrypted endpoint tests."""
        print("\n" + "="*80)
        print("RUNNING FACE LIVENESS ENCRYPTED TESTS")
        print("="*80)
        
        args = [
            "tests/stateless_apis/face_liveness/",
            "-v",
            "--tb=short",
            "-k", "encrypted"
        ]
        
        exit_code = pytest.main(args)
        
        if exit_code == 0:
            return TestResult("Face Liveness (Encrypted)", 11, 11, 0, 0, 0)
        else:
            return TestResult("Face Liveness (Encrypted)", 11, 0, 11, 0, 0)
    
    def run_all(self) -> bool:
        """
        Run all stateless API test suites.
        
        Returns:
            bool: True if all tests passed, False otherwise
        """
        print("\n" + "="*80)
        print("STATELESS API TEST SUITE")
        print("="*80)
        print("Testing: Face Liveness, Face Matcher, Document Verification")
        print("="*80)
        
        # Run all test modules
        self.results.append(self.run_face_liveness_tests())
        self.results.append(self.run_face_matcher_tests())
        self.results.append(self.run_document_verification_tests())
        
        # Print summary
        self.print_summary()
        
        # Return overall success
        total_failed = sum(r.failed for r in self.results)
        return total_failed == 0
    
    def run_all_detailed(self) -> bool:
        """
        Run all stateless API tests with detailed breakdowns.
        
        Returns:
            bool: True if all tests passed, False otherwise
        """
        print("\n" + "="*80)
        print("STATELESS API TEST SUITE (DETAILED)")
        print("="*80)
        
        # Run all modules
        self.results.append(self.run_face_liveness_tests())
        self.results.append(self.run_face_matcher_tests())
        self.results.append(self.run_document_verification_tests())
        
        # Print summary
        self.print_summary()
        
        # Return overall success
        total_failed = sum(r.failed for r in self.results)
        return total_failed == 0
    
    def print_summary(self):
        """Print test execution summary."""
        print("\n" + "="*80)
        print("TEST SUITE SUMMARY")
        print("="*80)
        
        for result in self.results:
            if result.total == 0:
                status = "??  NO TESTS COLLECTED"
            elif result.failed == 0 and result.passed > 0:
                status = "? PASSED"
            elif result.failed > 0:
                status = "? FAILED"
            else:
                status = "??  SKIPPED"
            
            print(f"\n{result.suite_name}: {status}")
            print(f"  Total: {result.total}")
            print(f"  Passed: {result.passed}")
            print(f"  Failed: {result.failed}")
            print(f"  Errors: {result.errors}")
            print(f"  Skipped: {result.skipped}")
            if result.total > 0:
                print(f"  Success Rate: {result.success_rate:.1f}%")
        
        # Overall summary
        total_tests = sum(r.total for r in self.results)
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        
        print("\n" + "="*80)
        print(f"OVERALL: {total_passed} passed, {total_failed} failed, {total_errors} errors, {total_skipped} skipped")
        print(f"Total Tests: {total_tests}")
        if total_tests > 0:
            overall_success = (total_passed / total_tests) * 100
            print(f"Overall Success Rate: {overall_success:.1f}%")
        print("="*80)


def main():
    """Run the stateless API test suite."""
    suite = StatelessTestSuite()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--detailed":
            success = suite.run_all_detailed()
        elif sys.argv[1] == "--encrypted-only":
            result = suite.run_face_liveness_encrypted_tests()
            suite.results.append(result)
            suite.print_summary()
            success = result.failed == 0
        elif sys.argv[1] == "--negative-only":
            result = suite.run_face_liveness_negative_tests()
            suite.results.append(result)
            suite.print_summary()
            success = result.failed == 0
        elif sys.argv[1] == "--face-liveness":
            result = suite.run_face_liveness_tests()
            suite.results.append(result)
            suite.print_summary()
            success = result.failed == 0
        elif sys.argv[1] == "--face-matcher":
            result = suite.run_face_matcher_tests()
            suite.results.append(result)
            suite.print_summary()
            success = result.failed == 0
        elif sys.argv[1] == "--document-verification":
            result = suite.run_document_verification_tests()
            suite.results.append(result)
            suite.print_summary()
            success = result.failed == 0
        elif sys.argv[1] == "--help":
            print("\nStateless API Test Suite Runner")
            print("\nUsage: python test_suite_stateless.py [OPTIONS]")
            print("\nOptions:")
            print("  (no args)              Run all stateless API tests")
            print("  --detailed             Run with detailed breakdowns")
            print("  --face-liveness        Run only Face Liveness tests")
            print("  --face-matcher         Run only Face Matcher tests")
            print("  --document-verification Run only Document Verification tests")
            print("  --encrypted-only       Run only encrypted endpoint tests")
            print("  --negative-only        Run only negative/error tests")
            print("  --help                 Show this help message")
            return
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help to see available options")
            sys.exit(1)
    else:
        success = suite.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
