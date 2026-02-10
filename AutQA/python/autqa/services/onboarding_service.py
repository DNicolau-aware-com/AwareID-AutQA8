"""
Onboarding orchestration service.

Coordinates complete onboarding workflows combining enrollment
and authentication processes. Provides end-to-end user onboarding.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from autqa.services.authentication_service import AuthenticationService
from autqa.services.enrollment_service import EnrollmentService
from autqa.core.api_client import ApiClient, get_api_client

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Service for complete onboarding workflows.
    
    Orchestrates enrollment and authentication to provide
    end-to-end user onboarding experiences.
    
    Example:
        service = OnboardingService()
        result = service.onboard_user_with_face(
            username="john_doe",
            face_frames=[...],
            test_authentication=True
        )
    """
    
    def __init__(self, api_client: Optional[ApiClient] = None):
        """
        Initialize onboarding service.
        
        Args:
            api_client: Optional API client (uses default if None)
        """
        self.api = api_client or get_api_client()
        self.enrollment = EnrollmentService(api_client=self.api)
        self.authentication = AuthenticationService(api_client=self.api)
        logger.debug("Initialized OnboardingService")
    
    def onboard_user_with_face(
        self,
        username: str,
        face_frames: List[Dict[str, Any]],
        email: Optional[str] = None,
        workflow: str = "charlie4",
        test_authentication: bool = False,
    ) -> Dict[str, Any]:
        """
        Complete onboarding with face biometric.
        
        Enrolls user and optionally tests authentication.
        
        Args:
            username: Username for onboarding
            face_frames: List of face frame objects
            email: Optional email address
            workflow: Workflow identifier
            test_authentication: Whether to test authentication after enrollment
        
        Returns:
            Dict containing enrollment and optional authentication results
            
        Example:
            result = service.onboard_user_with_face(
                username="john_doe",
                face_frames=[frame1, frame2, frame3],
                email="john@example.com",
                test_authentication=True
            )
        """
        logger.info(f"Starting complete onboarding for {username}")
        
        # Step 1: Complete enrollment
        enrollment_result = self.enrollment.complete_enrollment_with_face(
            username=username,
            face_frames=face_frames,
            email=email,
            workflow=workflow,
        )
        
        results = {
            "enrollment": enrollment_result,
            "username": username,
        }
        
        # Step 2: Test authentication if requested
        if test_authentication:
            logger.info("Testing authentication after enrollment")
            
            # Use first face frame for authentication test
            test_face_data = {
                "faceLivenessData": {
                    "video": {
                        "workflow_data": {
                            "workflow": workflow,
                            "frames": face_frames[:1],  # Use first frame
                        }
                    }
                }
            }
            
            auth_result = self.authentication.authenticate_with_face(
                username=username,
                face_data=test_face_data,
            )
            
            results["authentication_test"] = auth_result
            
            if auth_result.get("verified"):
                logger.info("✓ Authentication test passed")
            else:
                logger.warning("✗ Authentication test failed")
        
        logger.info(f"✓ Complete onboarding finished for {username}")
        return results
    
    def onboard_user_multi_biometric(
        self,
        username: str,
        face_frames: Optional[List[Dict[str, Any]]] = None,
        voice_data: Optional[Dict[str, Any]] = None,
        device_fingerprint: Optional[Dict[str, Any]] = None,
        email: Optional[str] = None,
        test_authentication: bool = False,
    ) -> Dict[str, Any]:
        """
        Complete onboarding with multiple biometrics.
        
        Args:
            username: Username for onboarding
            face_frames: Optional face frame objects
            voice_data: Optional voice audio data
            device_fingerprint: Optional device fingerprint
            email: Optional email address
            test_authentication: Whether to test authentication after enrollment
        
        Returns:
            Dict containing all enrollment and optional authentication results
        """
        logger.info(f"Starting multi-biometric onboarding for {username}")
        
        # Step 1: Initiate enrollment
        initiate_result = self.enrollment.initiate_enrollment(
            username=username,
            email=email,
            save_token=True,
        )
        enrollment_token = initiate_result["enrollmentToken"]
        
        results = {
            "initiate": initiate_result,
            "username": username,
        }
        
        # Step 2: Add face if provided
        if face_frames:
            face_result = self.enrollment.add_face_data(
                enrollment_token=enrollment_token,
                face_frames=face_frames,
                username=username,
            )
            results["face_enrollment"] = face_result
        
        # Step 3: Add voice if provided
        if voice_data:
            voice_result = self.enrollment.add_voice_data(
                enrollment_token=enrollment_token,
                voice_data=voice_data,
            )
            results["voice_enrollment"] = voice_result
        
        # Step 4: Add device if provided
        if device_fingerprint:
            device_result = self.enrollment.add_device_data(
                enrollment_token=enrollment_token,
                device_fingerprint=device_fingerprint,
            )
            results["device_enrollment"] = device_result
        
        # Step 5: Test authentication if requested
        if test_authentication:
            logger.info("Testing multi-factor authentication after enrollment")
            
            auth_result = self.authentication.authenticate_multi_factor(
                username=username,
                face_data={"faceLivenessData": {"frames": face_frames[:1]}} if face_frames else None,
                voice_data=voice_data,
                device_fingerprint=device_fingerprint,
            )
            
            results["authentication_test"] = auth_result
        
        logger.info(f"✓ Multi-biometric onboarding finished for {username}")
        return results
    
    def verify_onboarding_complete(
        self,
        username: str,
        face_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Verify that onboarding was successful by testing authentication.
        
        Args:
            username: Username to verify
            face_data: Optional face data for verification
        
        Returns:
            True if authentication succeeds, False otherwise
        """
        logger.info(f"Verifying onboarding completion for {username}")
        
        try:
            result = self.authentication.authenticate_with_face(
                username=username,
                face_data=face_data or {},
            )
            
            verified = result.get("verified", False)
            
            if verified:
                logger.info(f"✓ Onboarding verified for {username}")
            else:
                logger.warning(f"✗ Onboarding verification failed for {username}")
            
            return verified
            
        except Exception as e:
            logger.error(f"Onboarding verification error: {e}")
            return False
    
    def cleanup_test_user(self, username: str) -> None:
        """
        Clean up test user data (tokens, etc.).
        
        Args:
            username: Username to clean up
        """
        logger.info(f"Cleaning up test user: {username}")
        self.enrollment.clear_enrollment_tokens()
        self.authentication.clear_auth_tokens()