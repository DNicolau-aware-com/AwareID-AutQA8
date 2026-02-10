"""
Authentication API endpoints.

Thin wrapper around HTTP client for authentication-related API calls.
One method per endpoint. No environment reading/writing here.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class AuthenticationApi:
    """Handles all authentication-related API endpoints."""
    
    def __init__(self, client):
        """
        Initialize AuthenticationApi.
        
        Args:
            client: HTTP client instance (from autqa.core.http_client)
        """
        self.client = client
        self._base_path = "/onboarding/authentication"
    
    def initiate_authentication(self, username: str) -> requests.Response:
        """
        Initiate a new authentication session.
        
        Args:
            username: Username to authenticate
        
        Returns:
            Response containing authToken
        """
        return self.client.post(
            f"{self._base_path}/authenticate",
            json={"username": username}
        )
    
    def verify_face(
        self, 
        auth_token: str, 
        payload: Dict[str, Any]
    ) -> requests.Response:
        """
        Verify face biometric during authentication.
        
        Args:
            auth_token: Authentication session token
            payload: Face liveness data
        
        Returns:
            Response with verification result
        """
        headers = {"AUTHTOKEN": auth_token}
        return self.client.post(
            f"{self._base_path}/verifyFace",
            json=payload,
            extra_headers=headers
        )
    
    def verify_face_spoof(
        self,
        auth_token: str,
        payload: Dict[str, Any]
    ) -> requests.Response:
        """
        Verify face with spoof detection during authentication.
        
        Args:
            auth_token: Authentication session token
            payload: Face spoof detection data
        
        Returns:
            Response with spoof detection and verification result
        """
        headers = {"AUTHTOKEN": auth_token}
        return self.client.post(
            f"{self._base_path}/verifyFaceSpoof",
            json=payload,
            extra_headers=headers
        )
    
    def verify_voice(
        self, 
        auth_token: str, 
        payload: Dict[str, Any]
    ) -> requests.Response:
        """
        Verify voice biometric during authentication.
        
        Args:
            auth_token: Authentication session token
            payload: Voice audio data
        
        Returns:
            Response with voice verification result
        """
        headers = {"AUTHTOKEN": auth_token}
        return self.client.post(
            f"{self._base_path}/verifyVoice",
            json=payload,
            extra_headers=headers
        )
    
    def verify_device(
        self,
        auth_token: str,
        payload: Dict[str, Any]
    ) -> requests.Response:
        """
        Verify device fingerprint during authentication.
        
        Args:
            auth_token: Authentication session token
            payload: Device fingerprint data
        
        Returns:
            Response with device verification result
        """
        headers = {"AUTHTOKEN": auth_token}
        return self.client.post(
            f"{self._base_path}/verifyDevice",
            json=payload,
            extra_headers=headers
        )
    
    def cancel_authentication(
        self, 
        auth_token: str, 
        reason: Optional[str] = None
    ) -> requests.Response:
        """
        Cancel an ongoing authentication session.
        
        Args:
            auth_token: Authentication session token
            reason: Optional cancellation reason
        
        Returns:
            Response confirming cancellation
        """
        payload = {"reason": reason} if reason else {}
        headers = {"AUTHTOKEN": auth_token}
        return self.client.post(
            f"{self._base_path}/cancel",
            json=payload,
            extra_headers=headers
        )
    
    def retrieve_token(
        self,
        payload: Dict[str, Any]
    ) -> requests.Response:
        """
        Retrieve authentication token.
        
        Args:
            payload: Token retrieval request data
        
        Returns:
            Response containing authentication token
        """
        return self.client.post(
            f"{self._base_path}/retrieveToken",
            json=payload
        )