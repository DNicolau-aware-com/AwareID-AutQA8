"""
Portal settings validator for enrollment and authentication tests.

Automatically validates that test implementation matches portal settings.
Fails tests early with clear error messages if settings don't align.
"""

import pytest


def validate_enrollment_flow(required_checks, test_implements):
    """
    Validate enrollment test matches portal settings.
    
    Args:
        required_checks: List from /enroll response requiredChecks field
        test_implements: List of steps the test actually calls
    """
    print(f"\n{'='*80}")
    print("🔍 ENROLLMENT SETTINGS VALIDATION")
    print(f"{'='*80}")
    print(f"Portal requires:     {sorted(required_checks)}")
    print(f"Test implements:     {sorted(test_implements)}")

    portal_set = set(required_checks)
    test_set = set(test_implements)

    missing = portal_set - test_set
    if missing:
        error_msg = (
            f"\n❌ PORTAL SETTINGS MISMATCH - MISSING STEPS\n"
            f"{'='*80}\n"
            f"Portal requires but test doesn't implement: {sorted(list(missing))}\n\n"
            f"Portal requires:     {sorted(required_checks)}\n"
            f"Test implements:     {sorted(test_implements)}\n"
            f"{'='*80}\n"
            f"FIX: Add missing steps to test OR disable in admin portal\n"
            f"{'='*80}\n"
        )
        print(error_msg)
        pytest.fail(error_msg, pytrace=False)

    extra = test_set - portal_set
    if extra:
        error_msg = (
            f"\n❌ PORTAL SETTINGS MISMATCH - EXTRA STEPS\n"
            f"{'='*80}\n"
            f"Test implements but portal doesn't require: {sorted(list(extra))}\n\n"
            f"Portal requires:     {sorted(required_checks)}\n"
            f"Test implements:     {sorted(test_implements)}\n"
            f"{'='*80}\n"
            f"FIX: Remove extra steps from test OR enable in admin portal\n"
            f"{'='*80}\n"
        )
        print(error_msg)
        pytest.fail(error_msg, pytrace=False)

    print(f"\n✅ SETTINGS MATCH")
    print(f"   Both require: {sorted(required_checks)}")
    print(f"   Total steps: {len(portal_set)}")
    print(f"{'='*80}\n")
    return True


def validate_authentication_flow(required_checks, test_implements):
    """
    Validate authentication test matches portal settings.
    
    Args:
        required_checks: List from /authenticate response requiredChecks field
        test_implements: List of verification steps the test actually calls
    """
    print(f"\n{'='*80}")
    print("🔍 AUTHENTICATION SETTINGS VALIDATION")
    print(f"{'='*80}")
    print(f"Portal requires:     {sorted(required_checks)}")
    print(f"Test implements:     {sorted(test_implements)}")

    portal_set = set(required_checks)
    test_set = set(test_implements)

    missing = portal_set - test_set
    if missing:
        error_msg = (
            f"\n❌ PORTAL SETTINGS MISMATCH - MISSING STEPS\n"
            f"{'='*80}\n"
            f"Portal requires but test doesn't implement: {sorted(list(missing))}\n\n"
            f"Portal requires:     {sorted(required_checks)}\n"
            f"Test implements:     {sorted(test_implements)}\n"
            f"{'='*80}\n"
            f"FIX: Add missing steps to test OR disable in admin portal\n"
            f"{'='*80}\n"
        )
        print(error_msg)
        pytest.fail(error_msg, pytrace=False)

    extra = test_set - portal_set
    if extra:
        error_msg = (
            f"\n❌ PORTAL SETTINGS MISMATCH - EXTRA STEPS\n"
            f"{'='*80}\n"
            f"Test implements but portal doesn't require: {sorted(list(extra))}\n\n"
            f"Portal requires:     {sorted(required_checks)}\n"
            f"Test implements:     {sorted(test_implements)}\n"
            f"{'='*80}\n"
            f"FIX: Remove extra steps from test OR enable in admin portal\n"
            f"{'='*80}\n"
        )
        print(error_msg)
        pytest.fail(error_msg, pytrace=False)

    print(f"\n✅ SETTINGS MATCH")
    print(f"   Both require: {sorted(required_checks)}")
    print(f"   Total steps: {len(portal_set)}")
    print(f"{'='*80}\n")
    return True


def get_enrollment_required_checks(enroll_response):
    """Extract requiredChecks from enrollment response."""
    if hasattr(enroll_response, 'json'):
        data = enroll_response.json()
    else:
        data = enroll_response
    return data.get('requiredChecks', [])


def get_authentication_required_checks(auth_response):
    """Extract requiredChecks from authentication response."""
    if hasattr(auth_response, 'json'):
        data = auth_response.json()
    else:
        data = auth_response
    return data.get('requiredChecks', [])
