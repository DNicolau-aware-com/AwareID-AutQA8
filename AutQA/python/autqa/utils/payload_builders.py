"""
Payload building utilities.

Helper functions for constructing API request payloads.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


def build_face_frame_object(
    base64_data: str,
    timestamp: Optional[int] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a face frame object for liveness verification.
    
    Args:
        base64_data: Base64 encoded face image
        timestamp: Frame timestamp in milliseconds (uses current time if None)
        tags: Optional tags for the frame
    
    Returns:
        Face frame object
        
    Example:
        frame = build_face_frame_object("base64data...", timestamp=1234567890)
    """
    if timestamp is None:
        timestamp = int(time.time() * 1000)
    
    return {
        "data": base64_data,
        "timestamp": timestamp,
        "tags": tags or [],
    }


def build_face_liveness_payload(
    frames: List[Dict[str, Any]],
    workflow: str = "charlie4",
    username: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build face liveness data payload.
    
    Args:
        frames: List of face frame objects
        workflow: Workflow identifier
        username: Optional username for metadata
    
    Returns:
        Face liveness data structure
        
    Example:
        payload = build_face_liveness_payload(
            frames=[frame1, frame2],
            username="john_doe"
        )
    """
    return {
        "video": {
            "meta_data": {
                "username": username or "unknown_user",
            },
            "workflow_data": {
                "workflow": workflow,
                "frames": frames,
            },
        },
    }


def build_enrollment_payload(
    enrollment_token: str,
    face_liveness_data: Optional[Dict[str, Any]] = None,
    voice_data: Optional[Dict[str, Any]] = None,
    device_fingerprint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build enrollment payload with multiple biometric types.
    
    Args:
        enrollment_token: Enrollment token
        face_liveness_data: Optional face liveness data
        voice_data: Optional voice data
        device_fingerprint: Optional device fingerprint
    
    Returns:
        Enrollment payload
    """
    payload = {"enrollmentToken": enrollment_token}
    
    if face_liveness_data:
        payload["faceLivenessData"] = face_liveness_data
    
    if voice_data:
        payload["voiceData"] = voice_data
    
    if device_fingerprint:
        payload["deviceFingerprint"] = device_fingerprint
    
    return payload


def build_device_fingerprint(
    device_id: str,
    platform: str = "web",
    browser: Optional[str] = None,
    os: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build device fingerprint object.
    
    Args:
        device_id: Unique device identifier
        platform: Platform type (web, mobile, desktop)
        browser: Browser name and version
        os: Operating system
        additional_data: Additional device data
    
    Returns:
        Device fingerprint object
        
    Example:
        fingerprint = build_device_fingerprint(
            device_id="abc123",
            platform="web",
            browser="Chrome 120",
            os="Windows 11"
        )
    """
    fingerprint = {
        "deviceId": device_id,
        "platform": platform,
    }
    
    if browser:
        fingerprint["browser"] = browser
    
    if os:
        fingerprint["os"] = os
    
    if additional_data:
        fingerprint.update(additional_data)
    
    return fingerprint


def build_document_payload(
    document_images: List[str],
    document_type: str = "passport",
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build document verification payload.
    
    Args:
        document_images: List of base64 encoded document images
        document_type: Type of document (passport, driver_license, etc.)
        country: Optional country code
    
    Returns:
        Document payload
        
    Example:
        payload = build_document_payload(
            document_images=["base64data1", "base64data2"],
            document_type="passport",
            country="US"
        )
    """
    payload = {
        "documentImages": document_images,
        "documentType": document_type,
    }
    
    if country:
        payload["country"] = country
    
    return payload


def build_voice_payload(
    audio_data: str,
    format: str = "wav",
    sample_rate: Optional[int] = None,
    duration_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build voice verification payload.
    
    Args:
        audio_data: Base64 encoded audio data
        format: Audio format (wav, mp3, etc.)
        sample_rate: Audio sample rate in Hz
        duration_ms: Audio duration in milliseconds
    
    Returns:
        Voice payload
        
    Example:
        payload = build_voice_payload(
            audio_data="base64audio...",
            format="wav",
            sample_rate=16000
        )
    """
    payload = {
        "audioData": audio_data,
        "format": format,
    }
    
    if sample_rate:
        payload["sampleRate"] = sample_rate
    
    if duration_ms:
        payload["durationMs"] = duration_ms
    
    return payload


def merge_payloads(*payloads: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple payload dictionaries.
    
    Args:
        *payloads: Payload dictionaries to merge
    
    Returns:
        Merged payload
        
    Example:
        combined = merge_payloads(base_payload, metadata, extra_fields)
    """
    result = {}
    for payload in payloads:
        result.update(payload)
    return result