"""
Authentication business logic service.

Handles authentication workflows including token management,
multi-factor verification, and session handling.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from autqa.core.api_client import ApiClient, get_api_client
from autqa.core.env_store import EnvStore
from autqa.core.config import default_env_path

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Service for authentication operations.
    
    Provides high-level authentication workflows that coordinate multiple
    verification steps and manage authentication tokens.
    
    Example:
        service = AuthenticationService()
        result = service.authenticate_with_face(
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
        Initialize authentication service.
        
        Args:
            api_client: Optional API client (uses default if None)
            env_store: Optional env store for token persistence (uses default if None)
        """
        self.api = api_client or get_api_client()
        self.env_store = env_store or EnvStore(default_env_path())
        logger.debug("Initialized AuthenticationService")
    
    def initiate_authentication(
        self,
        username: str,
        save_token: bool = True,
    ) -> Dict[str, Any]:
        """
        Initiate a new authentication session.
        
        Args:
            username: Username to authenticate
            save_token: Whether to save auth token to .env
        
        Returns:
            Dict containing authToken and other response data
            
        Raises:
            Exception: If authentication initiation fails
            
        Example:
            result = service.initiate_authentication("john_doe")
            auth_token = result["authToken"]
        """
        logger.info(f"Initiating authentication for user: {username}")
        
        response = self.api.authentication.initiate_authentication(username)
        
        if response.status_code != 200:
            error_msg = f"Authentication initiation failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        result = response.json()
        auth_token = result.get("authToken")
        
        if not auth_token:
            raise Exception("Response missing authToken")
        
        # Save token to .env if requested
        if save_token:
            self.env_store.set("AUTH_TOKEN", auth_token)
            logger.info("Saved AUTH_TOKEN to .env")
        
        logger.info(f"✓ Authentication initiated for {username}")
        return result
    
    def verify_face(
        self,
        auth_token: Optional[str] = None,
        face_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Verify face biometric.
        
        Args:
            auth_token: Auth token (loads from .env if None)
            face_data: Face liveness data
        
        Returns:
            Dict containing verification result
            
        Raises:
            Exception: If verification fails
            
        Example:
            result = service.verify_face(face_data={...})
            if result["verified"]:
                print("Face verified!")
        """
        if auth_token is None:
            auth_token = self.env_store.get("AUTH_TOKEN")
        
        if not auth_token:
            raise Exception("No auth token provided or found in .env")
        
        logger.info("Verifying face biometric")
        
        payload = face_data or {}
        response = self.api.authentication.verify_face(auth_token, payload)
        
        if response.status_code != 200:
            error_msg = f"Face verification failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        result = response.json()
        verified = result.get("verified", False)
        
        if verified:
            logger.info("✓ Face verified successfully")
        else:
            logger.warning("✗ Face verification failed")
        
        return result
    
    def verify_face_spoof(
        self,
        auth_token: Optional[str] = None,
        face_spoof_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Verify face with spoof detection.
        
        Args:
            auth_token: Auth token (loads from .env if None)
            face_spoof_data: Face spoof detection data
        
        Returns:
            Dict containing verification and spoof detection results
            
        Raises:
            Exception: If verification fails
        """
        if auth_token is None:
            auth_token = self.env_store.get("AUTH_TOKEN")
        
        if not auth_token:
            raise Exception("No auth token provided or found in .env")
        
        logger.info("Verifying face with spoof detection")
        
        payload = face_spoof_data or {}
        response = self.api.authentication.verify_face_spoof(auth_token, payload)
        
        if response.status_code != 200:
            error_msg = f"Face spoof verification failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        result = response.json()
        logger.info("✓ Face spoof verification completed")
        return result
    
    def verify_voice(
        self,
        auth_token: Optional[str] = None,
        voice_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Verify voice biometric.
        
        Args:
            auth_token: Auth token (loads from .env if None)
            voice_data: Voice audio data
        
        Returns:
            Dict containing verification result
            
        Raises:
            Exception: If verification fails
        """
        if auth_token is None:
            auth_token = self.env_store.get("AUTH_TOKEN")
        
        if not auth_token:
            raise Exception("No auth token provided or found in .env")
        
        logger.info("Verifying voice biometric")
        
        payload = voice_data or {}
        response = self.api.authentication.verify_voice(auth_token, payload)
        
        if response.status_code != 200:
            error_msg = f"Voice verification failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        result = response.json()
        verified = result.get("verified", False)
        
        if verified:
            logger.info("✓ Voice verified successfully")
        else:
            logger.warning("✗ Voice verification failed")
        
        return result
    
    def verify_device(
        self,
        auth_token: Optional[str] = None,
        device_fingerprint: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Verify device fingerprint.
        
        Args:
            auth_token: Auth token (loads from .env if None)
            device_fingerprint: Device fingerprint data
        
        Returns:
            Dict containing verification result
            
        Raises:
            Exception: If verification fails
        """
        if auth_token is None:
            auth_token = self.env_store.get("AUTH_TOKEN")
        
        if not auth_token:
            raise Exception("No auth token provided or found in .env")
        
        logger.info("Verifying device fingerprint")
        
        payload = device_fingerprint or {}
        response = self.api.authentication.verify_device(auth_token, payload)
        
        if response.status_code != 200:
            error_msg = f"Device verification failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        result = response.json()
        verified = result.get("verified", False)
        
        if verified:
            logger.info("✓ Device verified successfully")
        else:
            logger.warning("✗ Device verification failed")
        
        return result
    
    def cancel_authentication(
        self,
        auth_token: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel an authentication session.
        
        Args:
            auth_token: Auth token (loads from .env if None)
            reason: Optional cancellation reason
        
        Returns:
            Response data
            
        Raises:
            Exception: If operation fails
        """
        if auth_token is None:
            auth_token = self.env_store.get("AUTH_TOKEN")
        
        if not auth_token:
            raise Exception("No auth token provided or found in .env")
        
        logger.info(f"Cancelling authentication: {reason or 'No reason provided'}")
        
        response = self.api.authentication.cancel_authentication(auth_token, reason)
        
        if response.status_code != 200:
            error_msg = f"Cancel authentication failed: {response.status_code}"
            logger.error(error_msg)
            raise Exception(f"{error_msg} - {response.text}")
        
        logger.info("✓ Authentication cancelled successfully")
        return response.json()
    
    def authenticate_with_face(
        self,
        username: str,
        face_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Complete face authentication workflow: initiate + verify face.
        
        High-level method that handles the complete face authentication process.
        
        Args:
            username: Username to authenticate
            face_data: Face liveness data
        
        Returns:
            Dict containing verification result
            
        Raises:
            Exception: If any step fails
            
        Example:
            result = service.authenticate_with_face(
                username="john_doe",
                face_data={...}
            )
            if result["verified"]:
                print("Authenticated!")
        """
        logger.info(f"Starting complete face authentication for {username}")
        
        # Step 1: Initiate authentication
        initiate_result = self.initiate_authentication(username, save_token=True)
        auth_token = initiate_result["authToken"]
        
        # Step 2: Verify face
        verify_result = self.verify_face(auth_token=auth_token, face_data=face_data)
        
        logger.info(f"✓ Complete face authentication finished for {username}")
        
        # Combine results
        return {
            **initiate_result,
            **verify_result,
        }
    
    def authenticate_multi_factor(
        self,
        username: str,
        face_data: Optional[Dict[str, Any]] = None,
        voice_data: Optional[Dict[str, Any]] = None,
        device_fingerprint: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Multi-factor authentication with multiple biometrics.
        
        Args:
            username: Username to authenticate
            face_data: Optional face liveness data
            voice_data: Optional voice audio data
            device_fingerprint: Optional device fingerprint
        
        Returns:
            Dict containing all verification results
            
        Raises:
            Exception: If any step fails
            
        Example:
            result = service.authenticate_multi_factor(
                username="john_doe",
                face_data={...},
                voice_data={...}
            )
        """
        logger.info(f"Starting multi-factor authentication for {username}")
        
        # Step 1: Initiate
        initiate_result = self.initiate_authentication(username, save_token=True)
        auth_token = initiate_result["authToken"]
        
        results = {"authToken": auth_token}
        
        # Step 2: Verify face if provided
        if face_data:
            face_result = self.verify_face(auth_token=auth_token, face_data=face_data)
            results["face_verification"] = face_result
        
        # Step 3: Verify voice if provided
        if voice_data:
            voice_result = self.verify_voice(auth_token=auth_token, voice_data=voice_data)
            results["voice_verification"] = voice_result
        
        # Step 4: Verify device if provided
        if device_fingerprint:
            device_result = self.verify_device(auth_token=auth_token, device_fingerprint=device_fingerprint)
            results["device_verification"] = device_result
        
        logger.info(f"✓ Multi-factor authentication completed for {username}")
        return results
    
    def get_current_auth_token(self) -> Optional[str]:
        """
        Get current auth token from .env.
        
        Returns:
            Auth token or None if not found
        """
        return self.env_store.get("AUTH_TOKEN") or None
    
    def clear_auth_tokens(self) -> None:
        """
        Clear authentication-related tokens from .env.
        
        Removes AUTH_TOKEN.
        """
        logger.info("Clearing auth tokens from .env")
        self.env_store.delete("AUTH_TOKEN")