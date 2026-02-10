"""
Enrollment API endpoints.

Thin wrapper around HTTP client for enrollment-related API calls.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class EnrollmentApi:
    """Handles all enrollment-related API endpoints."""
    
    def __init__(self, client):
        """
        Initialize EnrollmentApi.
        
        Args:
            client: HTTP client instance (from autqa.core.http_client)
        """
        self.client = client
        self._base_path = "/onboarding/enrollment"
    
    def initiate_enrollment(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Initiate a new enrollment session.
        
        Args:
            payload: Request payload containing user info
        
        Returns:
            Response containing enrollmentToken
        """
        return self.client.post(f"{self._base_path}/enroll", json=payload)
    
    def add_device(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Add device information to enrollment.
        
        Args:
            payload: Device data including enrollmentToken
        
        Returns:
            Response with updated enrollment status
        """
        return self.client.post(f"{self._base_path}/addDevice", json=payload)
    
    def add_face(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Add face liveness data to enrollment.
        
        Args:
            payload: Face frames with enrollmentToken and liveness data
        
        Returns:
            Response containing registrationCode
        """
        return self.client.post(f"{self._base_path}/addFace", json=payload)
    
    def add_face_spoof(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Add face spoof detection data to enrollment.
        
        Args:
            payload: Face spoof data with enrollmentToken
        
        Returns:
            Response with spoof detection results
        """
        return self.client.post(f"{self._base_path}/addFaceSpoof", json=payload)
    
    def add_voice(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Add voice biometric data to enrollment.
        
        Args:
            payload: Voice audio data with enrollmentToken
        
        Returns:
            Response with voice enrollment status
        """
        return self.client.post(f"{self._base_path}/addVoice", json=payload)
    
    def add_document(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Add document images to enrollment.
        
        Args:
            payload: Document image data with enrollmentToken
        
        Returns:
            Response with document processing status
        """
        return self.client.post(f"{self._base_path}/addDocument", json=payload)
    
    def validate_document_type(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Validate document type before processing.
        
        Args:
            payload: Document metadata for validation
        
        Returns:
            Response indicating if document type is valid
        """
        return self.client.post(f"{self._base_path}/validateDocumentType", json=payload)
    
    def add_document_ocr(
        self, 
        payload: Dict[str, Any], 
        with_apikey: bool = True
    ) -> requests.Response:
        """
        Add document with OCR processing.
        
        Args:
            payload: Document data for OCR extraction
            with_apikey: Whether to include API key in request (default: True)
        
        Returns:
            Response with OCR extracted data
        """
        return self.client.post(
            f"{self._base_path}/addDocumentOCR", 
            json=payload, 
            with_apikey=with_apikey
        )
    
    def cancel_enrollment(
        self, 
        enrollment_token: str,
        reason: Optional[str] = None
    ) -> requests.Response:
        """
        Cancel an ongoing enrollment session.
        
        Args:
            enrollment_token: Token of enrollment to cancel
            reason: Optional cancellation reason
        
        Returns:
            Response confirming cancellation
        """
        payload = {"enrollmentToken": enrollment_token}
        if reason:
            payload["reason"] = reason
        
        return self.client.post(f"{self._base_path}/cancel", json=payload)