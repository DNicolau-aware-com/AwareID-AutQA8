"""
Enrollment business logic service.

Handles complete enrollment workflows including token management,
data validation, and multi-step enrollment processes. Provides high-level
methods that orchestrate multiple API calls.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from autqa.core.api_client import ApiClient, get_api_client
from autqa.core.env_store import EnvStore
from autqa.core.config import default_env_path

logger = logging.getLogger(__name__)


class EnrollmentService:
    """
    Service for enrollment operations.
    
    Provides high-level enrollment workflows that combine multiple API calls,
    handle token management, and coordinate the enrollment process.
    
    Example:
        service = EnrollmentService()
        result = service.enroll_user_with_face(
            username="john_doe",
            face_data={...}
        )
    """
    
    def __init__(
        self,
        api_client: Optional[ApiClient] = None,
        env_store: Optional[EnvStore] = None,
    ):
        """
        Initialize enrollment service.
        
        Args:
            api_client: Optional API client (uses default if None)
            env_store: Optional env store for token persistence (uses default if None)
        """
        self.api = api_client or get_api_client()
        self.env_store = env_store or EnvStore(default_env_path())
        logger.debug("Initialized EnrollmentService")
    
    def initiate_enrollment(
        self,
        username: str,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_token: bool = True,
    ) -> Dict[str, Any]:
        """
        Initiate a new enrollment session.
        
        Args:
            username: Username for enrollment
            email: Optional email address
            metadata: Optional additional metadata
            save_token: Whether to save enrollment token to .env
        
        Returns:
            Dict containing enrollmentToken and other response data
            
        Raises:
            Exception: If enrollment initiation fails
            
        Example:
            result = service.initiate_enrollment(
                username="john_doe",
                email="john@example.com"
            )
            token = result["enrollmentToken"]
        """
        logger.info(f"Initiating enrollment for user: {username}")
        
        # Build payload
        payload = {"username": username}
        if email:
            payload["email"] = email
        if metadata:
            payload["metadata"] = metadata
        
        # Call API
        response = self.api.enrollment.initiate_enrollment(payload)
        
        if response.status_code != 200:
            error_msg = f"Enrollment initiation failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        result = response.json()
        enrollment_token = result.get("enrollmentToken")
        
        if not enrollment_token:
            raise Exception("Response missing enrollmentToken")
        
        # Save token to .env if requested
        if save_token:
            self.env_store.set("ENROLLMENT_TOKEN", enrollment_token)
            logger.info("Saved ENROLLMENT_TOKEN to .env")
        
        logger.info(f"✓ Enrollment initiated for {username}")
        return result
    
    def add_face_data(
        self,
        enrollment_token: Optional[str] = None,
        face_frames: Optional[List[Dict[str, Any]]] = None,
        workflow: str = "charlie4",
        username: Optional[str] = None,
        save_registration_code: bool = True,
    ) -> Dict[str, Any]:
        """
        Add face liveness data to enrollment.
        
        Args:
            enrollment_token: Enrollment token (loads from .env if None)
            face_frames: List of face frame objects
            workflow: Workflow identifier
            username: Optional username for metadata
            save_registration_code: Whether to save registration code to .env
        
        Returns:
            Dict containing registrationCode and other response data
            
        Raises:
            Exception: If face data addition fails
            
        Example:
            result = service.add_face_data(
                face_frames=[...],
                username="john_doe"
            )
            reg_code = result["registrationCode"]
        """
        # Get enrollment token
        if enrollment_token is None:
            enrollment_token = self.env_store.get("ENROLLMENT_TOKEN")
        
        if not enrollment_token:
            raise Exception("No enrollment token provided or found in .env")
        
        logger.info("Adding face data to enrollment")
        
        # Build payload
        payload = {
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {
                        "username": username or "unknown_user",
                    },
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames or [],
                    },
                },
            },
        }
        
        # Call API
        response = self.api.enrollment.add_face(payload)
        
        if response.status_code != 200:
            error_msg = f"Add face failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        result = response.json()
        registration_code = result.get("registrationCode")
        
        # Save registration code if requested
        if save_registration_code and registration_code:
            self.env_store.set("REGISTRATION_CODE", registration_code)
            logger.info("Saved REGISTRATION_CODE to .env")
        
        logger.info("✓ Face data added successfully")
        return result
    
    def add_face_spoof_data(
        self,
        enrollment_token: Optional[str] = None,
        face_spoof_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add face spoof detection data to enrollment.
        
        Args:
            enrollment_token: Enrollment token (loads from .env if None)
            face_spoof_data: Face spoof detection data
        
        Returns:
            Response data
            
        Raises:
            Exception: If operation fails
        """
        if enrollment_token is None:
            enrollment_token = self.env_store.get("ENROLLMENT_TOKEN")
        
        if not enrollment_token:
            raise Exception("No enrollment token provided or found in .env")
        
        logger.info("Adding face spoof data to enrollment")
        
        payload = {
            "enrollmentToken": enrollment_token,
            "faceSpoofData": face_spoof_data or {},
        }
        
        response = self.api.enrollment.add_face_spoof(payload)
        
        if response.status_code != 200:
            error_msg = f"Add face spoof failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        logger.info("✓ Face spoof data added successfully")
        return response.json()
    
    def add_voice_data(
        self,
        enrollment_token: Optional[str] = None,
        voice_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add voice biometric data to enrollment.
        
        Args:
            enrollment_token: Enrollment token (loads from .env if None)
            voice_data: Voice audio data
        
        Returns:
            Response data
            
        Raises:
            Exception: If operation fails
        """
        if enrollment_token is None:
            enrollment_token = self.env_store.get("ENROLLMENT_TOKEN")
        
        if not enrollment_token:
            raise Exception("No enrollment token provided or found in .env")
        
        logger.info("Adding voice data to enrollment")
        
        payload = {
            "enrollmentToken": enrollment_token,
            "voiceData": voice_data or {},
        }
        
        response = self.api.enrollment.add_voice(payload)
        
        if response.status_code != 200:
            error_msg = f"Add voice failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        logger.info("✓ Voice data added successfully")
        return response.json()
    
    def add_device_data(
        self,
        enrollment_token: Optional[str] = None,
        device_fingerprint: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add device fingerprint to enrollment.
        
        Args:
            enrollment_token: Enrollment token (loads from .env if None)
            device_fingerprint: Device fingerprint data
        
        Returns:
            Response data
            
        Raises:
            Exception: If operation fails
        """
        if enrollment_token is None:
            enrollment_token = self.env_store.get("ENROLLMENT_TOKEN")
        
        if not enrollment_token:
            raise Exception("No enrollment token provided or found in .env")
        
        logger.info("Adding device data to enrollment")
        
        payload = {
            "enrollmentToken": enrollment_token,
            "deviceFingerprint": device_fingerprint or {},
        }
        
        response = self.api.enrollment.add_device(payload)
        
        if response.status_code != 200:
            error_msg = f"Add device failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        logger.info("✓ Device data added successfully")
        return response.json()
    
    def add_document_data(
        self,
        enrollment_token: Optional[str] = None,
        document_images: Optional[List[str]] = None,
        document_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add document images to enrollment.
        
        Args:
            enrollment_token: Enrollment token (loads from .env if None)
            document_images: List of base64 document images
            document_type: Type of document (passport, driver_license, etc.)
        
        Returns:
            Response data
            
        Raises:
            Exception: If operation fails
        """
        if enrollment_token is None:
            enrollment_token = self.env_store.get("ENROLLMENT_TOKEN")
        
        if not enrollment_token:
            raise Exception("No enrollment token provided or found in .env")
        
        logger.info("Adding document data to enrollment")
        
        payload = {
            "enrollmentToken": enrollment_token,
            "documentImages": document_images or [],
            "documentType": document_type,
        }
        
        response = self.api.enrollment.add_document(payload)
        
        if response.status_code != 200:
            error_msg = f"Add document failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        logger.info("✓ Document data added successfully")
        return response.json()
    
    def cancel_enrollment(
        self,
        enrollment_token: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel an enrollment session.
        
        Args:
            enrollment_token: Enrollment token (loads from .env if None)
            reason: Optional cancellation reason
        
        Returns:
            Response data
            
        Raises:
            Exception: If operation fails
        """
        if enrollment_token is None:
            enrollment_token = self.env_store.get("ENROLLMENT_TOKEN")
        
        if not enrollment_token:
            raise Exception("No enrollment token provided or found in .env")
        
        logger.info(f"Cancelling enrollment: {reason or 'No reason provided'}")
        
        response = self.api.enrollment.cancel_enrollment(
            enrollment_token=enrollment_token,
            reason=reason,
        )
        
        if response.status_code != 200:
            error_msg = f"Cancel enrollment failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        logger.info("✓ Enrollment cancelled successfully")
        return response.json()
    
    def complete_enrollment_with_face(
        self,
        username: str,
        face_frames: List[Dict[str, Any]],
        email: Optional[str] = None,
        workflow: str = "charlie4",
    ) -> Dict[str, Any]:
        """
        Complete enrollment workflow: initiate + add face.
        
        High-level method that handles the complete face enrollment process.
        
        Args:
            username: Username for enrollment
            face_frames: List of face frame objects
            email: Optional email address
            workflow: Workflow identifier
        
        Returns:
            Dict containing both enrollmentToken and registrationCode
            
        Raises:
            Exception: If any step fails
            
        Example:
            result = service.complete_enrollment_with_face(
                username="john_doe",
                face_frames=[frame1, frame2, frame3],
                email="john@example.com"
            )
            print(f"Registration code: {result['registrationCode']}")
        """
        logger.info(f"Starting complete enrollment for {username}")
        
        # Step 1: Initiate enrollment
        initiate_result = self.initiate_enrollment(
            username=username,
            email=email,
            save_token=True,
        )
        enrollment_token = initiate_result["enrollmentToken"]
        
        # Step 2: Add face data
        face_result = self.add_face_data(
            enrollment_token=enrollment_token,
            face_frames=face_frames,
            workflow=workflow,
            username=username,
            save_registration_code=True,
        )
        
        logger.info(f"✓ Complete enrollment finished for {username}")
        
        # Combine results
        return {
            **initiate_result,
            **face_result,
        }
    
    def get_current_enrollment_token(self) -> Optional[str]:
        """
        Get current enrollment token from .env.
        
        Returns:
            Enrollment token or None if not found
        """
        return self.env_store.get("ENROLLMENT_TOKEN") or None
    
    def get_current_registration_code(self) -> Optional[str]:
        """
        Get current registration code from .env.
        
        Returns:
            Registration code or None if not found
        """
        return self.env_store.get("REGISTRATION_CODE") or None
    
    def clear_enrollment_tokens(self) -> None:
        """
        Clear enrollment-related tokens from .env.
        
        Removes ENROLLMENT_TOKEN and REGISTRATION_CODE.
        """
        logger.info("Clearing enrollment tokens from .env")
        self.env_store.delete("ENROLLMENT_TOKEN")
        self.env_store.delete("REGISTRATION_CODE")